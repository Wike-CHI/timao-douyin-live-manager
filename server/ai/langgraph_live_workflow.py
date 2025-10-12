"""LangGraph workflow for live AI script orchestration.

This module implements the workflow described in
``docs/AI处理工作流/直播AI话术LangGraph规划.md``. The workflow stitches together
memory loading, signal aggregation, lightweight analytics, script generation,
scoring, and persistence in a stateful LangGraph pipeline.
"""

from __future__ import annotations

import json
import logging
import random
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple, TypedDict

try:  # pragma: no cover - optional dependency
    from langgraph.graph import END, StateGraph
    from langgraph.checkpoint.memory import MemorySaver

    _LANGGRAPH_AVAILABLE = True
except Exception:  # pragma: no cover - graceful fallback
    StateGraph = None  # type: ignore[assignment]
    MemorySaver = None  # type: ignore[assignment]
    END = "__end__"  # type: ignore[misc]
    _LANGGRAPH_AVAILABLE = False

from .generator import AIScriptGenerator

try:  # pragma: no cover - optional reuse of helpers
    from .style_memory import _sanitize_anchor_id  # type: ignore
except Exception:  # pragma: no cover
    def _sanitize_anchor_id(anchor_id: Optional[str]) -> str:
        if not anchor_id:
            return "default"
        cleaned = re.sub(r"[\\s/]+", "_", anchor_id.strip())
        cleaned = re.sub(r"[^0-9A-Za-z_\\-]+", "_", cleaned)
        cleaned = cleaned.strip("_") or "default"
        return cleaned[:120]


logger = logging.getLogger(__name__)


class ChatSignal(TypedDict, total=False):
    text: str
    weight: float
    source: str
    category: Literal["question", "product", "support", "emotion", "other"]


class ScriptCandidate(TypedDict, total=False):
    text: str
    type: str
    route: str
    vibe: str
    keywords: List[str]
    score: float
    rationale: str
    script_id: str


class ScoreSummary(TypedDict, total=False):
    avg_score: float
    high_quality: List[ScriptCandidate]
    low_quality: List[ScriptCandidate]


class GraphState(TypedDict, total=False):
    broadcaster_id: str
    anchor_id: str
    window_start: float
    sentences: List[str]
    comments: List[Dict[str, Any]]
    transcript_snippet: str
    chat_signals: List[ChatSignal]
    topic_candidates: List[Dict[str, Any]]
    mood: str
    vibe: Dict[str, Any]
    persona: Dict[str, Any]
    memory_refs: Dict[str, Any]
    planner_route: str
    planner_notes: Dict[str, Any]
    scripts: List[ScriptCandidate]
    score_summary: ScoreSummary
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
    max_history: int = 120
    good_threshold: float = 7.0
    bad_threshold: float = 4.0


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to read json %s: %s", path, exc)
        return {}


def _read_jsonl(path: Path, limit: int = 80) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to read jsonl %s: %s", path, exc)
        return []
    return rows[-limit:]


def _trim_jsonl(path: Path, max_lines: int) -> None:
    if max_lines <= 0 or not path.exists():
        return
    try:
        with path.open("r", encoding="utf-8") as fh:
            lines = fh.readlines()
        if len(lines) <= max_lines:
            return
        with path.open("w", encoding="utf-8") as fh:
            fh.writelines(lines[-max_lines:])
    except Exception:  # pragma: no cover
        pass


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to append jsonl %s: %s", path, exc)


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[\\w\\u4e00-\\u9fff]{2,}", text.lower())


def _top_n_words(items: Iterable[str], n: int = 5) -> List[Tuple[str, int]]:
    counter: Counter[str] = Counter()
    for item in items:
        for token in _tokenize(item):
            counter[token] += 1
    return counter.most_common(n)


def _derive_keywords_from_scripts(scripts: List[ScriptCandidate]) -> List[str]:
    phrases: List[str] = []
    for sc in scripts:
        phrases.extend(sc.get("keywords") or [])
        text = sc.get("text") or ""
        phrases.extend([w for w, _ in _top_n_words([text], 3)])
    deduped: List[str] = []
    for phrase in phrases:
        if phrase and phrase not in deduped:
            deduped.append(phrase)
    return deduped[:8]


class LangGraphLiveWorkflow:
    """Top-level orchestrator exposing a `.invoke()` helper."""

    def __init__(
        self,
        generator: AIScriptGenerator,
        config: Optional[LiveWorkflowConfig] = None,
    ) -> None:
        self.generator = generator
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

    # ------------------------------------------------------------------ public
    def invoke(self, state: GraphState) -> GraphState:
        anchor_id = state.get("anchor_id") or self.config.anchor_id
        state["anchor_id"] = anchor_id or "default"
        state.setdefault("broadcaster_id", state.get("anchor_id") or "default")
        if self._workflow is None:
            return self._fallback_run(dict(state))
        cfg = {
            "configurable": {
                "thread_id": _sanitize_anchor_id(state["broadcaster_id"]),
            }
        }
        result: GraphState = self._workflow.invoke(state, config=cfg)  # type: ignore[arg-type]
        return result

    # ------------------------------------------------------------------ graph
    def _build_graph(self) -> Any:
        assert StateGraph is not None  # hint for type-checkers
        graph = StateGraph(GraphState)
        graph.add_node("memory_loader", self._memory_loader)
        graph.add_node("signal_collector", self._signal_collector)
        graph.add_node("topic_detector", self._topic_detector)
        graph.add_node("mood_estimator", self._mood_estimator)
        graph.add_node("planner", self._planner)
        graph.add_node(
            "script_gen_deep",
            lambda state: self._script_generator(state, route="deep_dive"),
        )
        graph.add_node(
            "script_gen_warm",
            lambda state: self._script_generator(state, route="warm_up"),
        )
        graph.add_node(
            "script_gen_promo",
            lambda state: self._script_generator(state, route="promo"),
        )
        graph.add_node("score_assessor", self._score_assessor)
        graph.add_node("summary", self._summary_node)
        graph.add_node("memory_updater", self._memory_updater)

        graph.set_entry_point("memory_loader")
        graph.add_edge("memory_loader", "signal_collector")
        graph.add_edge("signal_collector", "topic_detector")
        graph.add_edge("topic_detector", "mood_estimator")
        graph.add_edge("mood_estimator", "planner")
        graph.add_conditional_edges(
            "planner",
            self._route_selector,
            {
                "deep_dive": "script_gen_deep",
                "warm_up": "script_gen_warm",
                "promo": "script_gen_promo",
            },
        )
        graph.add_edge("script_gen_deep", "score_assessor")
        graph.add_edge("script_gen_warm", "score_assessor")
        graph.add_edge("script_gen_promo", "score_assessor")
        graph.add_edge("score_assessor", "summary")
        graph.add_edge("summary", "memory_updater")
        graph.add_edge("memory_updater", END)
        return graph

    # ------------------------------------------------------------------ nodes
    def _memory_loader(self, state: GraphState) -> Dict[str, Any]:
        anchor_id = _sanitize_anchor_id(state.get("anchor_id"))
        base = (self.config.memory_root / anchor_id).resolve()
        persona = _read_json(base / "profile.json")
        history = _read_jsonl(base / "history.jsonl", limit=40)
        good_fb = _read_jsonl(base / "feedback_good.jsonl", limit=40)
        bad_fb = _read_jsonl(base / "feedback_bad.jsonl", limit=40)

        persona.setdefault("tone", persona.get("tone") or "自然口语+陪伴")
        persona.setdefault("taboo", persona.get("taboo") or [])

        return {
            "persona": persona,
            "memory_refs": {
                "good_scripts": history,
                "feedback_good": good_fb,
                "feedback_bad": bad_fb,
            },
        }

    def _signal_collector(self, state: GraphState) -> Dict[str, Any]:
        sentences = state.get("sentences") or []
        comments = state.get("comments") or []
        last_sentences = sentences[-5:]
        transcript_snippet = "\n".join(last_sentences)
        chat_signals: List[ChatSignal] = []
        top_questions: List[str] = []

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
                weight = 0.75
                category = "product"
            elif any(s in lowered for s in ["加油", "支持", "棒", "666"]):
                weight = 0.6
                category = "support"
            elif any(e in lowered for e in ["喜欢", "好开心", "激动", "气"]):
                weight = 0.55
                category = "emotion"
            chat_signals.append(
                {
                    "text": content,
                    "weight": round(weight, 2),
                    "source": source,
                    "category": category,
                }
            )

        keywords = _top_n_words([sig["text"] for sig in chat_signals], n=6)
        signal_topics = [
            {"topic": word, "weight": count, "confidence": min(0.95, 0.55 + 0.05 * count)}
            for word, count in keywords
        ]
        return {
            "transcript_snippet": transcript_snippet,
            "chat_signals": chat_signals,
            "topic_candidates": signal_topics,
            "top_questions": list(dict.fromkeys(top_questions))[:6],
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
        merged = topics
        return {"topic_candidates": merged}

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
        top_topic = topics[0] if topics else {"topic": "互动", "confidence": 0.6}
        mood = state.get("mood") or "calm"
        chat_signals = state.get("chat_signals") or []

        has_product = any(sig.get("category") == "product" for sig in chat_signals)
        has_questions = any(sig.get("category") == "question" for sig in chat_signals)

        if has_product or (top_topic.get("topic") and re.search(r"(买|价|券|折|送)", top_topic["topic"])):
            route = "promo"
        elif has_questions or top_topic.get("confidence", 0) >= 0.75:
            route = "deep_dive"
        elif mood in {"stressed", "cold"}:
            route = "warm_up"
        else:
            route = "deep_dive"

        planner_notes = {
            "selected_topic": top_topic,
            "mood": mood,
            "heuristics": {
                "has_product_signal": has_product,
                "has_question_signal": has_questions,
            },
        }
        return {"planner_route": route, "planner_notes": planner_notes}

    def _route_selector(self, state: GraphState) -> str:
        return state.get("planner_route") or "deep_dive"

    def _script_generator(self, state: GraphState, route: str) -> Dict[str, Any]:
        context = {
            "hot_words": [
                {"word": t.get("topic"), "count": int(t.get("confidence", 0) * 100)}
                for t in state.get("topic_candidates") or []
            ],
            "top_questions": state.get("top_questions", []),
            "persona": state.get("persona") or {},
            "vibe": state.get("vibe") or {},
            "mood": state.get("mood"),
            "route": route,
        }
        try:
            bundle = self.generator.generate_bundle(
                route=route,
                hot_words=context.get("hot_words"),
                questions=context.get("top_questions"),
                persona=context.get("persona"),
                vibe=context.get("vibe"),
            )
        except Exception as exc:  # pragma: no cover
            logger.exception("Script generation failed: %s", exc)
            bundle = []

        scripts: List[ScriptCandidate] = []
        for item in bundle:
            scripts.append(
                {
                    "text": item.get("content") or item.get("text") or "",
                    "type": item.get("type") or "general",
                    "route": route,
                    "vibe": item.get("vibe") or context.get("vibe", {}).get("level") or "neutral",
                    "keywords": item.get("keywords") or _derive_keywords_from_scripts([item]),  # type: ignore[arg-type]
                    "score": float(item.get("score") or 0.0),
                    "rationale": item.get("rationale") or "",
                    "script_id": item.get("id") or "",
                }
            )
        return {"scripts": scripts}

    def _score_assessor(self, state: GraphState) -> Dict[str, Any]:
        scripts = state.get("scripts") or []
        if not scripts:
            return {"score_summary": {"avg_score": 0.0, "high_quality": [], "low_quality": []}}
        high: List[ScriptCandidate] = []
        low: List[ScriptCandidate] = []
        total = 0.0
        for script in scripts:
            score = float(script.get("score") or self.generator.score_text(script.get("text") or ""))
            script["score"] = round(score, 2)
            total += score
            if score >= self.config.good_threshold:
                high.append(script)
            elif score <= self.config.bad_threshold:
                low.append(script)
        avg_score = round(total / len(scripts), 2)
        return {
            "scripts": scripts,
            "score_summary": {
                "avg_score": avg_score,
                "high_quality": high,
                "low_quality": low,
            },
        }

    def _summary_node(self, state: GraphState) -> Dict[str, Any]:
        topic = state.get("planner_notes", {}).get("selected_topic") or {}
        vibe = state.get("vibe") or {}
        summary_parts = [
            f"当前主轴：{topic.get('topic', '互动话题')} (置信 {topic.get('confidence', 0)})",
            f"直播氛围：{vibe.get('level', 'neutral')}，热度分 {vibe.get('score', 0)}",
        ]
        scripts = state.get("scripts") or []
        if scripts:
            summary_parts.append(f"推荐话术 {len(scripts)} 条，可用于 {scripts[0].get('route', '')} 场景")
        summary = "；".join(summary_parts)

        highlight = [
            f"高频话题：{topic.get('topic')}",
            f"氛围评分 {vibe.get('score', 0)} ({vibe.get('level', 'neutral')})",
        ]
        questions = state.get("top_questions") or []
        if questions:
            highlight.append(f"实时问题关注：{questions[0]}")

        suggestions: List[str] = []
        if state.get("planner_route") == "promo":
            suggestions.append("适时发出行动号召，引导观众关注、留言或参与互动任务。")
        elif state.get("planner_route") == "warm_up":
            suggestions.append("适当抛出互动提问，调动积极回应。")
        else:
            suggestions.append("结合弹幕问题做更深入的场景剖析。")

        risks: List[str] = []
        if vibe.get("level") == "cold":
            risks.append("直播间互动偏冷，可能影响留存。")
        if state.get("score_summary", {}).get("low_quality"):
            risks.append("存在评分偏低的话术，建议谨慎使用。")

        top_questions = questions[:4]
        return {
            "summary": summary,
            "highlight_points": highlight,
            "suggestions": suggestions,
            "risks": risks,
            "top_questions": top_questions,
        }

    def _memory_updater(self, state: GraphState) -> Dict[str, Any]:
        anchor_id = _sanitize_anchor_id(state.get("anchor_id"))
        base = (self.config.memory_root / anchor_id).resolve()
        scripts = state.get("score_summary", {}).get("high_quality") or []
        bad_scripts = state.get("score_summary", {}).get("low_quality") or []
        if scripts:
            _write_jsonl(base / "history.jsonl", scripts)
            _trim_jsonl(base / "history.jsonl", self.config.max_history)
        if bad_scripts:
            payload = [{"text": sc.get("text"), "score": sc.get("score")} for sc in bad_scripts]
            _write_jsonl(base / "feedback_bad.jsonl", payload)
            _trim_jsonl(base / "feedback_bad.jsonl", self.config.max_history)
        if scripts:
            payload = [{"text": sc.get("text"), "score": sc.get("score")} for sc in scripts]
            _write_jsonl(base / "feedback_good.jsonl", payload)
            _trim_jsonl(base / "feedback_good.jsonl", self.config.max_history)
        return {}

    # ------------------------------------------------------------------ fallback
    def _fallback_run(self, state: GraphState) -> GraphState:
        updates: Dict[str, Any] = {}
        for step in (
            self._memory_loader,
            self._signal_collector,
            self._topic_detector,
            self._mood_estimator,
            self._planner,
        ):
            updates = step({**state, **updates})
            state.update(updates)

        route = self._route_selector(state)
        state.update(self._script_generator(state, route))
        state.update(self._score_assessor(state))
        state.update(self._summary_node(state))
        state.update(self._memory_updater(state))
        return state


def ensure_workflow(generator: AIScriptGenerator, config: Optional[LiveWorkflowConfig] = None) -> LangGraphLiveWorkflow:
    """Factory helper to align with legacy imports."""
    return LangGraphLiveWorkflow(generator=generator, config=config)
