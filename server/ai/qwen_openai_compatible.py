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
from typing import Any, Dict, List

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


def build_messages(transcript: str, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    transcript_clip, comments_digest, top_users_text = _digest(transcript, comments)

    system = (
        "你是通用直播复盘教练，适用于聊天、游戏、音乐、知识、户外等各类直播场景。"
        "请基于‘主播口播转写’与‘弹幕概览’，输出结构化 JSON："
        "{highlight_points:[], risks:[], suggestions:[], top_questions:[], scripts:[{text,type,tags}]}。"
        "要求：语言中立、可执行；建议围绕内容节奏、互动质量、信息清晰度、情绪与氛围等；"
        "脚本 3-5 条，每条 1-2 句，可用于引导互动（如关注、点赞、弹幕提问、点歌/点梗、参与活动等）。"
    )
    user_text = (
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


def analyze_live_session(transcript: str, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    client = _get_client()
    model = DEFAULT_OPENAI_MODEL
    messages = build_messages(transcript, comments)
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
        return json.loads(txt)
    except Exception:
        return {"raw": txt}


def analyze_window(transcript: str, comments: List[Dict[str, Any]], prev_summary: str | None = None) -> Dict[str, Any]:
    """Analyze a 5-min window with optional previous summary to maintain continuity.

    Returns a dict JSON with fields similar to analyze_live_session, and a short
    'carry' string for feeding the next window.
    """
    client = _get_client()
    model = DEFAULT_OPENAI_MODEL
    t_clip, comments_digest, top_users_text = _digest(transcript, comments)

    system = (
        "你是通用直播的运营复盘教练，帮助主播针对最近窗口做节奏复盘与下一步建议（适用于聊天、游戏、音乐、知识、户外等）。"
        "输出 JSON：{summary, highlight_points:[], risks:[], suggestions:[], top_questions:[], scripts:[{text,type,tags}], carry}。"
        "carry 为 1-3 句、<=160 字的可传递摘要，用于下一窗口延续与优化。"
    )
    user_blocks = [
        f"【上一窗口摘要】\n{(prev_summary or '（无）')}",
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
        temperature=0.2,
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
    return out
