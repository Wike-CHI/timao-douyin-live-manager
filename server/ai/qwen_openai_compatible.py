"""
OpenAI-compatible client for Aliyun DashScope (Qwen MAX / Qwen Omni families).

Reads standard envs:
- OPENAI_API_KEY
- OPENAI_BASE_URL (e.g. https://dashscope.aliyuncs.com/compatible-mode/v1)
- OPENAI_MODEL (examples: qwen-max, qwen-max-longcontext, qwen-omni-turbo; default: qwen-max)

We default to text-only fusion: transcript + aggregated comments.
If later we add image/audio packaging (base64 or upload), extend build_messages().
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore
try:
    import httpx  # type: ignore
except Exception:  # pragma: no cover
    httpx = None  # type: ignore

# Hardcoded DashScope OpenAI-compatible config (per user request)
DEFAULT_OPENAI_API_KEY = "sk-92045f0a33984350925ce3ccffb3489e"
DEFAULT_OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_OPENAI_MODEL = "qwen3-max"

try:  # pragma: no cover - optional style memory
    from .style_memory import StyleMemoryManager

    _STYLE_MANAGER = StyleMemoryManager()
except Exception:  # pragma: no cover
    _STYLE_MANAGER = None  # type: ignore
try:  # pragma: no cover - optional feedback memory
    from .feedback_memory import get_feedback_manager

    _FEEDBACK_MANAGER = get_feedback_manager()
except Exception:  # pragma: no cover
    _FEEDBACK_MANAGER = None  # type: ignore


def _get_client():
    if OpenAI is None:
        raise RuntimeError("openai package not installed")
    # Build a minimal httpx client explicitly to avoid version-mismatch issues
    # with deprecated 'proxies' kw in httpx.Client.
    kwargs = {}
    http_client = None
    if httpx is not None:
        try:
            http_client = httpx.Client(timeout=30.0, **kwargs)
        except TypeError:
            # Fallback: create client with no extra kwargs
            http_client = httpx.Client(timeout=30.0)
        except Exception:
            http_client = None

    return OpenAI(
        api_key=DEFAULT_OPENAI_API_KEY,
        base_url=DEFAULT_OPENAI_BASE_URL,
        http_client=http_client,
    )


def _digest(transcript: str, comments: List[Dict[str, Any]]):
    # Prepare a compact comments digest (avoid oversize payload)
    top = []
    cnt_by_user: Dict[str, int] = {}
    texts: List[str] = []
    for ev in comments[:2000]:  # cap
        user = (ev.get("user") or ev.get("payload", {}).get("user") or "?")
        content = ev.get("content") or ev.get("payload", {}).get("content") or ""
        if content:
            texts.append(f"{user}: {content}")
        cnt_by_user[user] = cnt_by_user.get(user, 0) + 1
    top = sorted(cnt_by_user.items(), key=lambda x: x[1], reverse=True)[:10]

    comments_digest = "\n".join(texts[:1000])  # textual sample
    top_users_text = ", ".join([f"{u}x{c}" for u, c in top])
    return transcript[:20000], comments_digest, top_users_text


def _style_context(anchor_id: Optional[str]) -> str:
    if _STYLE_MANAGER and _STYLE_MANAGER.available():
        try:
            return _STYLE_MANAGER.fetch_context(anchor_id, k=6)
        except Exception:
            return ""
    return ""


def _feedback_context(anchor_id: Optional[str]) -> str:
    if _FEEDBACK_MANAGER and _FEEDBACK_MANAGER.available():
        try:
            return _FEEDBACK_MANAGER.build_guidance(anchor_id, top_k=4)
        except Exception:
            return ""
    return ""


def build_messages(
    transcript: str,
    comments: List[Dict[str, Any]],
    style_notes: str = "",
    feedback_notes: str = "",
) -> List[Dict[str, Any]]:
    """Builds the prompt for a full-session review.

    Refined to: (1) learn the host's speaking style from transcript; (2) sense
    room vibe from comments; (3) output human-like, directly usable scripts that
    follow the host's style to warm up the room.
    """
    transcript_clip, comments_digest, top_users_text = _digest(transcript, comments)

    # System prompt focuses on style learning + vibe sensing while keeping
    # backward-compatible keys used by UI: highlight_points/risks/suggestions/
    # top_questions/scripts. Additional fields are additive.
    style_block = ""
    if style_notes:
        style_block = (
            "【历史画像与口头禅（来自累计记忆）】\n"
            f"{style_notes.strip()}\n\n"
        )

    guidance_block = ""
    if feedback_notes:
        guidance_block = (
            "\n【人工评分反馈】请保留以下优点并避免风险表达：\n"
            f"{feedback_notes}\n"
        )

    system = (
        "你是直播运营总监风格的AI教练，擅长从‘主播口播转写’和‘弹幕氛围’中学习语言风格，"
        "并给出可执行的复盘与可直接上嘴的话术。请输出严格JSON，包含但不限于以下字段："
        "{highlight_points:[], risks:[], suggestions:[], top_questions:[], scripts:[{text,type,tags}],"
        " style_profile:{persona,tone,tempo,register,slang:[],catchphrases:[],rhetoric:[]},"
        " vibe:{level: \"cold|neutral|hot\", score: 0-100, trends: []}}。"
        f"{guidance_block}"
        "要求："
        "1) 先从口播转写中总结‘语言风格画像（style_profile）’，含语气(俏皮/专业/热情等)、节奏(慢/中/快)、"
        "常用词与口头禅、句式与修辞；"
        "2) 结合弹幕密度/情绪与热点，判断当前氛围（vibe）与可带动点；"
        "3) highlight/risks/suggestions 要具体、可执行；"
        "4) scripts 生成 3-5 条，每条 1-2 句、20-50字，口语化，尽量贴近主播风格；"
        "   - 覆盖：互动引导/澄清回应/情绪带动/转场/关注点赞召唤；"
        "   - 文案避免生硬广告语和敏感词，合规友好；"
        "   - 每条给出 {text,type,tags}，type 可为 interaction|clarification|humor|engagement|call_to_action|transition；"
        "5) 只输出JSON，不要多余解释。"
    )
    user_text = (
        f"{style_block}"
        f"【口播转写（节选）】\n{transcript_clip}\n\n"
        f"【弹幕Top用户】{top_users_text}\n\n"
        f"【弹幕节选】\n{comments_digest}"
    )

    return [
        {
            "role": "system",
            "content": [{"type": "text", "text": system}],
        },
        {
            "role": "user",
            "content": [{"type": "text", "text": user_text}],
        },
    ]


def analyze_live_session(
    transcript: str,
    comments: List[Dict[str, Any]],
    anchor_id: Optional[str] = None,
) -> Dict[str, Any]:
    client = _get_client()
    model = DEFAULT_OPENAI_MODEL
    notes = _style_context(anchor_id)
    feedback_notes = _feedback_context(anchor_id)
    messages = build_messages(
        transcript,
        comments,
        style_notes=notes,
        feedback_notes=feedback_notes,
    )
    # Ask model to output JSON strictly
    messages.append({
        "role": "user",
        "content": [{"type": "text", "text": "只输出JSON，不要额外说明。"}],
    })

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        response_format={"type": "json_object"},  # OpenAI style
    )
    txt = resp.choices[0].message.content or "{}"
    try:
        result = json.loads(txt)
    except Exception:
        result = {"raw": txt}

    if anchor_id and _STYLE_MANAGER and _STYLE_MANAGER.available():
        try:
            _STYLE_MANAGER.ingest_summary(anchor_id, result)
        except Exception:
            pass
    return result


def analyze_window(
    transcript: str,
    comments: List[Dict[str, Any]],
    prev_summary: str | None = None,
    anchor_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Analyze a 5-min window with optional previous summary to maintain continuity.

    Returns a dict JSON with fields similar to analyze_live_session, and a short
    'carry' string for feeding the next window.
    """
    client = _get_client()
    model = DEFAULT_OPENAI_MODEL
    t_clip, comments_digest, top_users_text = _digest(transcript, comments)
    style_notes = _style_context(anchor_id)
    feedback_notes = _feedback_context(anchor_id)
    style_block = ""
    if style_notes:
        style_block = f"【历史画像与口头禅】\n{style_notes.strip()}\n\n"
    if feedback_notes:
        style_block += f"【人工评分反馈】\n{feedback_notes.strip()}\n\n"

    # Window-level prompt emphasizes continuity: carry over the style and
    # actionable next-step scripts to heat up the room.
    system = (
        "你是直播运营总监风格的AI教练，针对最近窗口做‘节奏复盘+下一步建议’，并延续上一窗口风格。"
        "输出严格JSON：{summary, highlight_points:[], risks:[], suggestions:[], top_questions:[],"
        " scripts:[{text,type,tags}], style_profile:{persona,tone,tempo,register,slang:[],catchphrases:[]},"
        " vibe:{level: \"cold|neutral|hot\", score: 0-100, trends: []}, carry}。"
        "要求："
        "1) 先快速归纳本窗的风格与氛围变化；"
        "2) scripts 贴合主播语言风格（如口头禅/语气/节奏），3-5 条，20-50字/条，口语自然；"
        "   - 覆盖互动引导/关注点赞/转场/澄清回应/情绪带动中的至少两类；"
        "3) carry 用 1-3 句、<=160 字总结‘延续点’，下个窗口可直接承接；"
        "4) 只输出JSON，不要多余解释。"
    )
    user_blocks = [
        style_block + f"【上一窗口摘要】\n{(prev_summary or '（无）')}",
        f"【本窗口口播（节选）】\n{t_clip}",
        f"【弹幕Top用户】{top_users_text}",
        f"【弹幕节选】\n{comments_digest}",
    ]
    messages = [
        {"role": "system", "content": [{"type": "text", "text": system}]},
        {"role": "user", "content": [{"type": "text", "text": "\n\n".join(user_blocks)}]},
        {"role": "user", "content": [{"type": "text", "text": "只输出JSON，不要额外说明。"}]},
    ]

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        # 略微提高创造性以使话术更有人味，但仍保持可控
        temperature=0.4,
        response_format={"type": "json_object"},
    )
    txt = resp.choices[0].message.content or "{}"
    try:
        out = json.loads(txt)
    except Exception:
        out = {"raw": txt}
    if "carry" not in out:
        # derive carry from summary if absent
        out["carry"] = (out.get("summary") or "")[:160]
    if anchor_id and _STYLE_MANAGER and _STYLE_MANAGER.available():
        try:
            _STYLE_MANAGER.ingest_summary(anchor_id, out)
        except Exception:
            pass
    return out
