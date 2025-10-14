"""LangGraph workflow for live analysis card orchestration.

This module powers the live analysis card described in
``docs/AI处理工作流/直播AI话术LangGraph规划.md``. It ingests rolling transcript
snippets and chat events, performs lightweight categorisation, and invokes a
Qwen3-Max based assistant to produce an analysis-only report (no scripts).
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple, TypedDict

try:  # pragma: no cover - optional dependency
    from langgraph.graph import END, StateGraph
    from langgraph.checkpoint.memory import MemorySaver

    _LANGGRAPH_AVAILABLE = True
except Exception:  # pragma: no cover
    StateGraph = None  # type: ignore[assignment]
    MemorySaver = None  # type: ignore[assignment]
    END = "__end__"  # type: ignore[misc]
    _LANGGRAPH_AVAILABLE = False

from .live_analysis_generator import LiveAnalysisGenerator
from .live_question_responder import LiveQuestionResponder

try:  # pragma: no cover - optional reuse of helpers
    from .style_memory import _sanitize_anchor_id  # type: ignore
except Exception:  # pragma: no cover
    def _sanitize_anchor_id(anchor_id: Optional[str]) -> Optional[str]:
        if anchor_id is None:
            return None
        text = str(anchor_id).strip()
        if not text:
            return None
        cleaned = re.sub(r"[\\s/]+", "_", text)
        cleaned = re.sub(r"[^0-9A-Za-z_\\-]+", "_", cleaned)
        cleaned = cleaned.strip("_")
        return cleaned[:120] or None


logger = logging.getLogger(__name__)


class ChatSignal(TypedDict, total=False):
    text: str
    weight: float
    source: str
    category: Literal["question", "product", "support", "emotion", "other"]


class GraphState(TypedDict, total=False):
    broadcaster_id: Optional[str]
    anchor_id: Optional[str]
    window_start: float
    sentences: List[str]
    comments: List[Dict[str, Any]]
    transcript_snippet: str
    chat_signals: List[ChatSignal]
    chat_stats: Dict[str, Any]
    speech_stats: Dict[str, Any]
    topic_candidates: List[Dict[str, Any]]
    mood: str
    vibe: Dict[str, Any]
    persona: Dict[str, Any]
    planner_notes: Dict[str, Any]
    analysis_focus: str
    analysis_card: Dict[str, Any]
    summary: str
    highlight_points: List[str]
    risks: List[str]
    suggestions: List[str]
    top_questions: List[str]


@dataclass
class LiveWorkflowConfig:
    """Runtime configuration for the LangGraph workflow."""

    anchor_id: Optional[str] = None
    memory_root: Path = Path("records") / "memory"


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to read json %s: %s", path, exc)
        return {}


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[\\w\\u4e00-\\u9fff]{2,}", text.lower())


def _top_n_words(items: Iterable[str], n: int = 5) -> List[Tuple[str, int]]:
    counter: Counter[str] = Counter()
    for item in items:
        for token in _tokenize(item):
            counter[token] += 1
    return counter.most_common(n)


class LangGraphLiveWorkflow:
    """Top-level orchestrator exposing a `.invoke()` helper."""

    def __init__(
        self,
        analysis_generator: LiveAnalysisGenerator,
        question_responder: Optional[LiveQuestionResponder] = None,
        config: Optional[LiveWorkflowConfig] = None,
    ) -> None:
        self.analysis_generator = analysis_generator
        self.question_responder = question_responder
        self.config = config or LiveWorkflowConfig()
        self._graph = None
        self._workflow = None
        if _LANGGRAPH_AVAILABLE:
            self._graph = self._build_graph()
            checkpointer = MemorySaver() if MemorySaver else None
            self._workflow = (
                self._graph.compile(checkpointer=checkpointer) if checkpointer else self._graph.compile()
            )
        else:
            logger.warning("LangGraph unavailable; workflow will run in sequential fallback mode.")

    def invoke(self, state: GraphState) -> GraphState:
        anchor_input = state.get("anchor_id") or self.config.anchor_id
        anchor_key = _sanitize_anchor_id(anchor_input)
        state["anchor_id"] = anchor_key
        state["broadcaster_id"] = anchor_key
        thread_id = anchor_key or f"session_{uuid.uuid4().hex}"
        if self._workflow is None:
            return self._fallback_run(dict(state))
        cfg = {"configurable": {"thread_id": thread_id}}
        result: GraphState = self._workflow.invoke(state, config=cfg)  # type: ignore[arg-type]
        return result

    # ------------------------------------------------------------------ graph
    def _build_graph(self) -> Any:
        assert StateGraph is not None  # type hint
        graph = StateGraph(GraphState)
        graph.add_node("memory_loader", self._memory_loader)
        graph.add_node("signal_collector", self._signal_collector)
        graph.add_node("topic_detector", self._topic_detector)
        graph.add_node("mood_estimator", self._mood_estimator)
        graph.add_node("planner", self._planner)
        graph.add_node("analysis_generator", self._analysis_generator)
        if self.question_responder:
            graph.add_node("question_responder", self._question_responder)
        graph.add_node("summary", self._summary_node)

        graph.set_entry_point("memory_loader")
        graph.add_edge("memory_loader", "signal_collector")
        graph.add_edge("signal_collector", "topic_detector")
        graph.add_edge("topic_detector", "mood_estimator")
        graph.add_edge("mood_estimator", "planner")
        graph.add_edge("planner", "analysis_generator")
        if self.question_responder:
            graph.add_edge("analysis_generator", "question_responder")
            graph.add_edge("question_responder", "summary")
        else:
            graph.add_edge("analysis_generator", "summary")
        graph.add_edge("summary", END)
        return graph

    # ------------------------------------------------------------------ nodes
    def _memory_loader(self, state: GraphState) -> Dict[str, Any]:
        anchor_key = _sanitize_anchor_id(state.get("anchor_id"))
        persona: Dict[str, Any] = {}
        if anchor_key:
            base = (self.config.memory_root / anchor_key).resolve()
            persona = _read_json(base / "profile.json")
        if not persona:
            persona = {"tone": "专业陪伴", "taboo": []}
        return {"persona": persona}

    def _signal_collector(self, state: GraphState) -> Dict[str, Any]:
        sentences = state.get("sentences") or []
        comments = state.get("comments") or []
        transcript_snippet = "\n".join(sentences[-6:])
        chat_signals: List[ChatSignal] = []
        top_questions: List[str] = []
        category_counts: Dict[str, int] = {"question": 0, "product": 0, "support": 0, "emotion": 0, "other": 0}
        total_chars = sum(len(s) for s in sentences)
        window_start = float(state.get("window_start") or time.time())
        elapsed = max(1.0, time.time() - window_start)
        speaking_estimate = max(0.0, len(sentences) * 2.0)
        speaking_ratio = min(1.0, speaking_estimate / elapsed)
        last_sentence = sentences[-1] if sentences else ""
        first_pronouns = (
            "我", "咱", "咱们", "本主播", "主播我", "小妹", "小姐姐", "哥哥我", "姐姐我", "哥我"
        )
        audience_terms = (
            "大家", "家人", "家人们", "兄弟们", "姐妹们", "宝宝", "宝宝们", "朋友们", "伙伴们"
        )
        other_terms = (
            "她", "他", "她们", "他们", "对面", "对方", "对家", "对手", "敌方", "她那边", "他那边"
        )
        target_sentences = sentences[-10:] or []
        other_like = 0
        host_like = 0
        neutral_like = 0
        total_checked = 0
        host_examples: List[str] = []
        other_examples: List[str] = []
        neutral_examples: List[str] = []
        for raw in target_sentences:
            text = str(raw).strip()
            if not text:
                continue
            total_checked += 1
            has_first = any(token in text for token in first_pronouns)
            has_audience = any(token in text for token in audience_terms)
            has_other = any(token in text for token in other_terms)
            host_flag = has_first or has_audience
            other_flag = has_other and not has_first

            if host_flag and not other_flag:
                host_like += 1
                if len(host_examples) < 2:
                    host_examples.append(text[:30])
            elif other_flag:
                other_like += 1
                if len(other_examples) < 2:
                    other_examples.append(text[:30])
            else:
                neutral_like += 1
                if len(neutral_examples) < 2:
                    neutral_examples.append(text[:30])

        other_ratio = other_like / total_checked if total_checked else 0.0
        host_ratio = host_like / total_checked if total_checked else 0.0

        speech_stats = {
            "sentence_count": len(sentences),
            "total_chars": total_chars,
            "last_sentence": last_sentence,
            "window_seconds": round(elapsed, 1),
            "speaking_ratio": round(speaking_ratio, 3),
            "other_like_ratio": round(other_ratio, 3),
            "host_like_ratio": round(host_ratio, 3),
            "host_like_count": host_like,
            "other_like_count": other_like,
            "neutral_like_count": neutral_like,
            "host_examples": host_examples,
            "other_examples": other_examples,
            "neutral_examples": neutral_examples,
            "possible_other_speaker": other_ratio >= 0.6 and sentence_count >= 2,
        }

        for comment in comments[-200:]:
            content = str(comment.get("content") or "").strip()
            if not content:
                continue
            lowered = content.lower()
            weight = 0.4
            source = comment.get("type") or "chat"
            category: Literal["question", "product", "support", "emotion", "other"] = "other"
            if any(q in lowered for q in ["?", "？", "什么", "怎么", "why", "how", "price"]):
                weight = 0.85
                category = "question"
                top_questions.append(content)
            elif any(p in lowered for p in ["买", "价", "券", "折扣", "产品"]):
                weight = 0.7
                category = "product"
            elif any(s in lowered for s in ["加油", "支持", "棒", "666", "冲"]):
                weight = 0.6
                category = "support"
            elif any(e in lowered for e in ["喜欢", "开心", "激动", "气", "焦虑"]):
                weight = 0.55
                category = "emotion"
            category_counts[category] = category_counts.get(category, 0) + 1
            chat_signals.append(
                {
                    "text": content,
                    "weight": round(weight, 2),
                    "source": source,
                    "category": category,
                }
            )

        chat_stats = {
            "total_messages": len(chat_signals),
            "category_counts": category_counts,
            "window_seconds": round(elapsed, 1),
        }
        return {
            "transcript_snippet": transcript_snippet,
            "chat_signals": chat_signals,
            "chat_stats": chat_stats,
            "top_questions": list(dict.fromkeys(top_questions))[:6],
            "speech_stats": speech_stats,
        }

    def _topic_detector(self, state: GraphState) -> Dict[str, Any]:
        snippet = state.get("transcript_snippet") or ""
        comments = [sig["text"] for sig in state.get("chat_signals") or []]
        corpus = [snippet] + comments
        keywords = _top_n_words(corpus, n=5)
        topics: List[Dict[str, Any]] = []
        for rank, (word, count) in enumerate(keywords, start=1):
            confidence = min(0.95, 0.6 + 0.07 * count)
            topics.append(
                {
                    "topic": word,
                    "confidence": round(confidence, 2),
                    "rank": rank,
                }
            )
        if not topics:
            topics = [{"topic": "互动", "confidence": 0.55, "rank": 1}]
        return {"topic_candidates": topics}

    def _mood_estimator(self, state: GraphState) -> Dict[str, Any]:
        chat_signals = state.get("chat_signals") or []
        excitement = sum(sig["weight"] for sig in chat_signals if sig.get("category") in {"support", "emotion"})
        questions = sum(sig["weight"] for sig in chat_signals if sig.get("category") == "question")
        base_score = 45.0 + excitement * 8.0 - questions * 2.0
        base_score = max(10.0, min(95.0, base_score))

        if base_score >= 70:
            level = "hot"
            mood = "hype"
        elif base_score >= 50:
            level = "neutral"
            mood = "calm"
        else:
            level = "cold"
            mood = "stressed" if questions > excitement else "calm"

        vibe = {
            "level": level,
            "score": round(base_score, 1),
            "trends": [
                "questions_high" if questions > excitement else "supporting",
                "interaction_dense" if len(chat_signals) > 40 else "interaction_light",
            ],
        }
        return {"mood": mood, "vibe": vibe}

    def _planner(self, state: GraphState) -> Dict[str, Any]:
        topics = state.get("topic_candidates") or []
        top_topic = topics[0] if topics else {"topic": "互动", "confidence": 0.55}
        vibe = state.get("vibe") or {}
        top_questions = state.get("top_questions") or []
        speech_stats = state.get("speech_stats") or {}
        sentence_count = int(speech_stats.get("sentence_count") or 0)
        speaking_ratio = float(speech_stats.get("speaking_ratio") or 0.0)
        other_like_ratio = float(speech_stats.get("other_like_ratio") or 0.0)
        host_like_ratio = float(speech_stats.get("host_like_ratio") or 0.0)
        possible_other_speaker = bool(speech_stats.get("possible_other_speaker"))

        focus: str
        if sentence_count == 0 and (state.get("chat_stats", {}).get("total_messages") or 0) <= 2:
            focus = "主播基本未开口，先主动打招呼或抛话题，唤醒直播间。"
        elif possible_other_speaker or other_like_ratio >= max(0.55, host_like_ratio + 0.15):
            focus = "对手说得更多，提醒主播抓住时机回应或反问，争取把节奏拉回来。"
        elif speaking_ratio < 0.2 and (state.get("chat_stats", {}).get("total_messages") or 0) <= 5:
            focus = "主播这一轮说话较少，可补充互动或分享话题，拉高存在感。"
        elif top_questions:
            focus = "重点观察观众提问，尽快帮助主播澄清或回应。"
        elif vibe.get("level") == "hot":
            focus = "当前热度较高，提醒主播稳住节奏并引导互动转化。"
        elif vibe.get("level") == "cold":
            focus = "互动偏冷，需要提示主播主动抛话题或互动任务。"
        else:
            focus = "整体平稳，可结合主要讨论话题加深内容。"

        planner_notes = {
            "selected_topic": top_topic,
            "top_questions": top_questions,
            "vibe": vibe,
            "speech_stats": speech_stats,
        }
        return {"analysis_focus": focus, "planner_notes": planner_notes}

    def _analysis_generator(self, state: GraphState) -> Dict[str, Any]:
        transcript = state.get("transcript_snippet") or "\n".join(state.get("sentences") or [])
        context = {
            "transcript": transcript,
            "chat_signals": state.get("chat_signals") or [],
            "chat_stats": state.get("chat_stats") or {},
            "speech_stats": state.get("speech_stats") or {},
            "topics": state.get("topic_candidates") or [],
            "vibe": state.get("vibe") or {},
            "mood": state.get("mood"),
            "persona": state.get("persona") or {},
            "planner_focus": state.get("analysis_focus"),
        }
        try:
            card = self.analysis_generator.generate(context)
        except Exception as exc:  # pragma: no cover
            logger.exception("Analysis generation failed: %s", exc)
            card = {"analysis_overview": f"生成失败：{exc}"}
        return {"analysis_card": card}

    def _question_responder(self, state: GraphState) -> Dict[str, Any]:
        if not self.question_responder:
            return {"answer_scripts": []}
        questions = state.get("planner_notes", {}).get("top_questions") or state.get("top_questions") or []
        if not questions:
            return {"answer_scripts": []}
        transcript = state.get("transcript_snippet") or "\n".join(state.get("sentences") or [])
        context = {
            "questions": questions,
            "persona": state.get("persona") or {},
            "vibe": state.get("vibe") or {},
            "mood": state.get("mood"),
            "transcript": transcript,
        }
        try:
            scripts = self.question_responder.generate(context)
        except Exception as exc:  # pragma: no cover
            logger.exception("Question responder failed: %s", exc)
            scripts = []
        return {"answer_scripts": scripts}

    def _summary_node(self, state: GraphState) -> Dict[str, Any]:
        card = state.get("analysis_card") or {}
        overview = str(card.get("analysis_overview") or "").strip()
        if not overview:
            overview = "当前窗口缺乏足够信息，无法生成详细分析。"
        highlights = card.get("engagement_highlights") or []
        risks = card.get("risks") or []
        suggestions = card.get("next_actions") or []
        planner_notes = state.get("planner_notes") or {}
        topic = planner_notes.get("selected_topic") or {}
        vibe = state.get("vibe") or {}
        speech_stats = planner_notes.get("speech_stats") or state.get("speech_stats") or {}
        sentence_count = int(speech_stats.get("sentence_count") or 0)
        speaking_ratio = float(speech_stats.get("speaking_ratio") or 0.0)
        other_like_ratio = float(speech_stats.get("other_like_ratio") or 0.0)
        possible_other_speaker = bool(speech_stats.get("possible_other_speaker"))
        host_like_ratio = float(speech_stats.get("host_like_ratio") or 0.0)
        host_examples = speech_stats.get("host_examples") or []
        other_examples = speech_stats.get("other_examples") or []
        if sentence_count == 0:
            speech_hint = "主播本轮几乎未发言"
        elif possible_other_speaker or other_like_ratio >= max(0.55, host_like_ratio + 0.15):
            speech_hint = f"主播这段说了 {sentence_count} 句，对方掌握话题较多"
        elif speaking_ratio <= 0.2:
            speech_hint = f"主播这段说了 {sentence_count} 句，话语占比偏低"
        else:
            speech_hint = f"主播这段说了 {sentence_count} 句"

        topic_text = topic.get("topic") or "互动"
        level_raw = (vibe.get("level") or "").lower()
        level_map = {"cold": "偏冷", "neutral": "平稳", "hot": "火热"}
        vibe_level = level_map.get(level_raw, "偏冷" if "cold" in level_raw else (level_raw or "偏冷"))
        vibe_score = vibe.get("score")
        if isinstance(vibe_score, (int, float)):
            score_text = f"{int(round(vibe_score))}分"
        else:
            score_text = "—"
        summary = f"{overview} 当前氛围{vibe_level}（{score_text}），话题集中在{topic_text}，{speech_hint}。"

        def _dedupe(items: List[str], limit: int) -> List[str]:
            seen = set()
            ordered: List[str] = []
            for text in items:
                key = text.strip()
                if not key or key in seen:
                    continue
                ordered.append(key)
                seen.add(key)
                if len(ordered) >= limit:
                    break
            return ordered

        if host_like_ratio >= 0.7 and sentence_count >= 3:
            highlights = list(highlights) if isinstance(highlights, list) else [highlights]
            highlights.append("主播节奏稳定，持续带话题")
        if possible_other_speaker or other_like_ratio >= max(0.55, host_like_ratio + 0.15):
            risks = list(risks) if isinstance(risks, list) else [risks]
            risks.append("对手掌握话题较多，主播需抓住空隙回应")
            if other_examples:
                risks.append(f"疑似对手语句：{str(other_examples[0])[:18]}")
            suggestions = list(suggestions) if isinstance(suggestions, list) else [suggestions]
            suggestions.append("接对方句尾补充或反问，导回自家话题")

        clean_highlights = highlights if isinstance(highlights, list) else [highlights]
        clean_highlights = [str(item).strip() for item in clean_highlights if item]
        clean_highlights = _dedupe(clean_highlights, 2)

        clean_risks = risks if isinstance(risks, list) else [risks]
        clean_risks = [str(item).strip() for item in clean_risks if item]
        clean_risks = _dedupe(clean_risks, 2)

        clean_suggestions = suggestions if isinstance(suggestions, list) else [suggestions]
        clean_suggestions = [str(item).strip() for item in clean_suggestions if item]
        clean_suggestions = _dedupe(clean_suggestions, 3)

        return {
            "summary": summary,
            "highlight_points": clean_highlights,
            "risks": clean_risks,
            "suggestions": clean_suggestions,
        }

    # ------------------------------------------------------------------ fallback
    def _fallback_run(self, state: GraphState) -> GraphState:
        updates: Dict[str, Any] = {}
        sequence = [
            self._memory_loader,
            self._signal_collector,
            self._topic_detector,
            self._mood_estimator,
            self._planner,
            self._analysis_generator,
        ]
        if self.question_responder:
            sequence.append(self._question_responder)
        sequence.append(self._summary_node)
        for step in sequence:
            updates = step({**state, **updates})
            state.update(updates)
        return state


def ensure_workflow(
    analysis_generator: LiveAnalysisGenerator,
    question_responder: Optional[LiveQuestionResponder] = None,
    config: Optional[LiveWorkflowConfig] = None,
) -> LangGraphLiveWorkflow:
    """Factory helper to align with legacy imports."""
    return LangGraphLiveWorkflow(
        analysis_generator=analysis_generator,
        question_responder=question_responder,
        config=config,
    )
