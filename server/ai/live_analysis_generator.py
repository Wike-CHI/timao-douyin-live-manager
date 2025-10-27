"""
Live analysis card generator for the TiMao Douyin Live Manager.

This module produces analysis-only cards (no scripts) by sending the latest
transcript snippets and chat signals to a Qwen3-Max compatible endpoint.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

# 使用统一网关
from .ai_gateway import get_gateway

try:
    from ..utils.ai_tracking_decorator import track_ai_usage
    _TRACKING_AVAILABLE = True
except Exception:
    _TRACKING_AVAILABLE = False
    def track_ai_usage(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger(__name__)


class LiveAnalysisGenerator:
    """Generate live analysis cards via AI Gateway."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.gateway = get_gateway()
        self.model: str = config.get("ai_model", "qwen-plus")
        logger.info("LiveAnalysisGenerator initialized with AI Gateway.")

    def _format_chat_samples(self, chat_signals: List[Dict[str, Any]]) -> str:
        lines: List[str] = []
        for idx, signal in enumerate(chat_signals[:12], start=1):
            category = signal.get("category") or "other"
            weight = signal.get("weight")
            text = signal.get("text") or ""
            prefix = f"{idx}. [{category}]"
            if weight is not None:
                prefix += f"(w={weight})"
            lines.append(f"{prefix} {text}")
        return "\n".join(lines) or "（本窗口暂无有效弹幕）"

    def _format_topic_candidates(self, topics: List[Dict[str, Any]]) -> str:
        if not topics:
            return "（未检测到稳定话题）"
        parts: List[str] = []
        for rank, topic in enumerate(topics[:5], start=1):
            name = topic.get("topic") or ""
            conf = topic.get("confidence")
            if conf is not None:
                parts.append(f"{rank}. {name} (置信 {conf})")
            else:
                parts.append(f"{rank}. {name}")
        return "\n".join(parts)

    def _format_lead_candidates(self, leads: List[Dict[str, Any]]) -> str:
        if not leads:
            return "（尚未捕捉到优质弹幕或高价值信号）"
        lines: List[str] = []
        for idx, lead in enumerate(leads[:4], start=1):
            user = lead.get("user") or "观众"
            text = lead.get("text") or ""
            reason = lead.get("reason") or ""
            score = lead.get("score")
            label = f"{idx}. {user}：{text}"
            if reason:
                label += f" —— {reason}"
            if score is not None:
                label += f"（参考分 {score}）"
            lines.append(label)
        return "\n".join(lines)

    def _format_category_stats(self, stats: Dict[str, Any]) -> str:
        total = stats.get("total_messages", 0)
        window_seconds = stats.get("window_seconds")
        by_cat = stats.get("category_counts") or {}
        readable_names = {
            "question": "提问类",
            "product": "产品/成交类",
            "support": "打气支持类",
            "emotion": "情绪反馈类",
            "other": "其他闲聊",
        }
        lines = [f"总量: {total}"]
        if window_seconds is not None:
            lines.append(f"窗口时长: {window_seconds}s")
        subtotal = sum(by_cat.values()) or 1
        for key in ("question", "product", "support", "emotion", "other"):
            if key not in by_cat:
                continue
            label = readable_names.get(key, key)
            count = by_cat[key]
            ratio = (count / subtotal) * 100
            lines.append(f"{label}: {count} 条（约 {ratio:.1f}%）")
        return "\n".join(lines)

    def _format_speech_stats(self, stats: Dict[str, Any]) -> str:
        sentences = int(stats.get("sentence_count") or 0)
        total_chars = int(stats.get("total_chars") or 0)
        last_sentence = str(stats.get("last_sentence") or "").strip()
        window_seconds = stats.get("window_seconds")
        speaking_ratio = stats.get("speaking_ratio")
        other_ratio = stats.get("other_like_ratio")
        host_ratio = stats.get("host_like_ratio")
        possible_other = stats.get("possible_other_speaker")
        host_examples = stats.get("host_examples") or []
        other_examples = stats.get("other_examples") or []
        speaker_counts = stats.get("speaker_counts") or {}
        speaker_examples = stats.get("speaker_examples") or {}
        if speaker_examples and not host_examples:
            host_examples = speaker_examples.get("host") or host_examples
        if speaker_examples and not other_examples:
            other_examples = speaker_examples.get("guest") or speaker_examples.get("other") or other_examples
        rows = [
            f"最终句数: {sentences}",
            f"总字数: {total_chars}",
        ]
        if window_seconds is not None:
            rows.append(f"窗口时长: {window_seconds}s")
        if speaking_ratio is not None:
            rows.append(f"说话占比: {round(float(speaking_ratio)*100, 1)}%")
        if speaker_counts:
            host_count = int(speaker_counts.get("host", 0))
            guest_count = int(sum(count for spk, count in speaker_counts.items() if spk not in {"host", "unknown", "", "neutral"}))
            unknown_count = int(
                speaker_counts.get("unknown", 0)
                + speaker_counts.get("", 0)
                + speaker_counts.get("neutral", 0)
            )
            rows.append(
                f"话者分布: 主播{host_count}句 / 嘉宾{guest_count}句 / 未识别{unknown_count}句"
            )
        else:
            if host_ratio is not None:
                rows.append(f"判定为主播的句占比: {round(float(host_ratio)*100, 1)}%")
            if other_ratio is not None:
                rows.append(f"疑似对手发言占比: {round(float(other_ratio)*100, 1)}%")
        if last_sentence:
            preview = last_sentence if len(last_sentence) <= 30 else last_sentence[:30] + "…"
            rows.append(f"最近一句: {preview}")
        else:
            rows.append("最近一句: （暂无）")
        last_speaker = stats.get("last_speaker")
        if last_speaker:
            label = "主播" if last_speaker == "host" else ("嘉宾" if last_speaker not in {None, "", "unknown", "neutral"} else "未识别")
            rows.append(f"最近发言者: {label}")
        if possible_other:
            rows.append("提示：对方主播发言较多")
        if host_examples:
            rows.append("主播示例：" + " | ".join(str(x)[:20] for x in host_examples))
        if other_examples:
            rows.append("嘉宾/其他示例：" + " | ".join(str(x)[:20] for x in other_examples))
        return "\n".join(rows)

    def _build_prompt(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        transcript = context.get("transcript") or ""
        chat_summary = self._format_chat_samples(context.get("chat_signals") or [])
        topics = self._format_topic_candidates(context.get("topics") or [])
        stats = self._format_category_stats(context.get("chat_stats") or {})
        raw_speech_stats = context.get("speech_stats") or {}
        speech_stats = self._format_speech_stats(raw_speech_stats)
        window_seconds = raw_speech_stats.get("window_seconds") or context.get("chat_stats", {}).get("window_seconds")
        window_label = f"最近 {int(window_seconds)} 秒" if window_seconds else "最近 1 分钟"
        vibe = context.get("vibe") or {}
        persona = context.get("persona") or {}
        planner_focus = context.get("planner_focus") or ""
        focus_notes = ""
        if planner_focus:
            focus_notes = f"【系统聚焦建议】{planner_focus}\n\n"

        lead_candidates_fmt = self._format_lead_candidates(context.get("lead_candidates") or [])

        knowledge_snippets = context.get("knowledge_snippets") or []
        knowledge_blocks: List[str] = []
        for snippet in knowledge_snippets:
            block = snippet.get("prompt_block") if isinstance(snippet, dict) else None
            if not block:
                title = snippet.get("title") if isinstance(snippet, dict) else None
                summary = snippet.get("summary") if isinstance(snippet, dict) else None
                highlights = snippet.get("highlights") if isinstance(snippet, dict) else []
                highlight_text = " | ".join(str(h) for h in highlights[:3]) if highlights else ""
                block = f"《{title or '知识片段'}》 {summary or highlight_text}"
            knowledge_blocks.append(block)
        knowledge_note = ""
        if knowledge_blocks:
            knowledge_note = "【知识库参考】\n" + "\n\n".join(knowledge_blocks[:3]) + "\n\n"

        vibe_line = (
            f"level={vibe.get('level', 'unknown')}, "
            f"score={vibe.get('score', 'N/A')}, "
            f"mood={context.get('mood', 'unknown')}"
        )

        system_prompt = (
            "你是一名资深直播运营教练。每 30-60 秒收到主播口播、弹幕与统计，需要写一份给主播看的《实时观察》。"
            "请专注分析与建议，不要输出固定口播模板或引导观众的脚本文字。"
            "回复必须是 JSON 对象，字段包括："
            '{"analysis_overview":"一句自然语言总结(≤35字)",'
            '"audience_sentiment":{"label":"热|平稳|冷","signals":["两条以内的证据"]},'
            '"engagement_highlights":["两条以内的真实观察"],'
            '"risks":["两条以内的潜在问题与原因"],'
            '"next_actions":["三条以内的行动指引"],'
            '"next_topic_direction":"一句话点出接下来要围绕的聊天方向",'
            '"confidence":0.0~1.0,'
            '"style_profile":{"persona":"","tone":"","tempo":"","register":"","catchphrases":[],"slang":[]},'
            '"vibe":{"level":"cold|neutral|hot","score":0,"trends":["两条趋势"]}}'
            "。若信息不足，也要保留字段并说明“暂无数据”。"
            "写作要求："
            "1) 用主播能听懂的口语表达，语气自然、有温度，避免“当前”“本轮”“请注意”等官腔；"
            "2) 每条 highlights/risks/next_actions 最多 16 个字，聚焦现象或原因；"
            "3) next_actions 写可执行方向（如“围绕宿舍话题提问”“点名欢迎新观众”），不要给出口播样板；"
            "4) next_topic_direction 结合当前弹幕与口播，用 12 字以内的口语句式描述“接下来聊点什么”，不要写“围绕/建议”等字眼；"
            "5) 引用提供的弹幕、口播、统计线索，必要时说明数量或关键词；"
            "6) style_profile 结合近期语气和历史画像总结语气、节奏、常用表达；"
            "7) 提醒互动时可参考关键词，但不要让主播照念任何模板；"
            "8) 全文保持像熟悉运营同事的口吻，避免过度书面或命令式表达；"
            "9) 优先点名“优质弹幕/高价值信号”中的观众，并结合其关键词顺势延展话题。"
            "10) audience_sentiment中的signals字段必须包含具体的证据，如'新观众连续入场带节奏'、'点赞数增加'等。"
        )

        persona_notes = ""
        if persona:
            persona_notes = (
                "【主播画像】\n"
                + json.dumps(persona, ensure_ascii=False)
                + "\n\n"
            )

        user_prompt = (
            f"{focus_notes}"
            f"{persona_notes}"
            f"{knowledge_note}"
            f"【时间窗口】{window_label}\n"
            "【口播节选】\n"
            f"{transcript or '（暂无口播文本）'}\n\n"
            "【观众互动摘录】\n"
            f"{chat_summary}\n\n"
            "【优质弹幕/高价值信号】\n"
            f"{lead_candidates_fmt}\n\n"
            "【互动分类统计】\n"
            f"{stats}\n\n"
            "【主播口播情况】\n"
            f"{speech_stats}\n\n"
            "【讨论焦点候选】\n"
            f"{topics}\n\n"
            "【系统氛围评估】\n"
            f"{vibe_line}"
        )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def generate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # 调用带追踪的内部方法
        return self._generate_with_tracking(context)
    
    @track_ai_usage("实时分析")
    def _generate_with_tracking(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """带使用追踪的生成方法"""
        messages = self._build_prompt(context)
        
        # 使用网关调用
        response = self.gateway.chat_completion(
            messages=messages,
            model=self.model,
            temperature=0.3,
            response_format={"type": "json_object"},
            max_tokens=800,
        )
        
        if not response.success:
            logger.error(f"AI调用失败: {response.error}")
            return {"analysis_overview": "生成失败，请稍后重试"}
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            logger.warning("无法解析 AI 返回的 JSON：%s", response.content)
            return {"analysis_overview": response.content}
