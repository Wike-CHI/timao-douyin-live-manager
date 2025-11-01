# -*- coding: utf-8 -*-
"""Live AI Analyzer Service

Collects final sentences from live_audio and chat events from Douyin web relay,
batches them into short windows, calls AI analysis (Qwen OpenAI-compatible), and
streams results to frontend via SSE.
"""

from __future__ import annotations

import asyncio
import time
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

try:
    from ...ai.qwen_openai_compatible import (  # type: ignore
        DEFAULT_OPENAI_API_KEY,
        DEFAULT_OPENAI_BASE_URL,
        DEFAULT_OPENAI_MODEL,
    )
except Exception:  # pragma: no cover
    DEFAULT_OPENAI_API_KEY = ""
    DEFAULT_OPENAI_BASE_URL = ""
    DEFAULT_OPENAI_MODEL = ""

from ...ai.live_analysis_generator import LiveAnalysisGenerator
from ...ai.langgraph_live_workflow import LiveWorkflowConfig, ensure_workflow
from ...ai.knowledge_service import get_knowledge_base

from .live_audio_stream_service import get_live_audio_service
from .douyin_web_relay import get_douyin_web_relay


def _now_ms() -> int:
    return int(time.time() * 1000)


logger = logging.getLogger(__name__)


@dataclass
class AIState:
    active: bool = False
    window_sec: int = 60
    last_window_ts: int = field(default_factory=_now_ms)
    carry: str = ""
    last_result: Dict[str, Any] = field(default_factory=dict)
    sentences: List[str] = field(default_factory=list)
    speaker_sentences: List[Dict[str, Any]] = field(default_factory=list)
    comments: List[Dict[str, Any]] = field(default_factory=list)
    # Persisted context for other modules to reuse/style-mimic
    style_profile: Dict[str, Any] = field(default_factory=dict)
    vibe: Dict[str, Any] = field(default_factory=dict)
    anchor_id: Optional[str] = None
    user_scores: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class AILiveAnalyzer:
    def __init__(self) -> None:
        self._state = AIState()
        self._lock = asyncio.Lock()
        self._task: Optional[asyncio.Task] = None
        self._clients: Set[asyncio.Queue] = set()

        # hook ids for live_audio callbacks
        self._cb_name: Optional[str] = None
        self._relay_queue: Optional[asyncio.Queue] = None
        self._anchor_id = self._resolve_anchor_id()
        self._generator: Optional[LiveAnalysisGenerator] = None
        self._script_responder = None
        self._workflow = None
        self._init_workflow()

    # -------------- Public API --------------
    async def start(self, window_sec: int = 90) -> Dict[str, Any]:
        async with self._lock:
            if self._state.active:
                return {"success": True, "message": "already running"}
            self._state = AIState(
                active=True,
                window_sec=max(30, int(window_sec)),
                anchor_id=self._anchor_id,
            )
            await self._attach_hooks()
            self._task = asyncio.create_task(self._run_loop())
            return {"success": True}

    async def stop(self) -> Dict[str, Any]:
        async with self._lock:
            self._state.active = False
            await self._detach_hooks()
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
                self._task = None
            return {"success": True}

    def status(self) -> Dict[str, Any]:
        s = self._state
        return {
            "active": s.active,
            "window_sec": s.window_sec,
            "last_result": s.last_result,
            "sentences_in_window": len(s.sentences),
            "comments_in_window": len(s.comments),
            # Expose learned style & vibe snapshot for consumers (frontend/other services)
            "style_profile": s.style_profile,
            "vibe": s.vibe,
        }

    async def register_client(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._clients.add(q)
        # push last result if any
        if self._state.last_result:
            try:
                q.put_nowait({
                    "type": "ai",
                    "payload": self._state.last_result,
                    "timestamp": time.time(),
                })
            except Exception:
                pass
        return q

    async def unregister_client(self, q: asyncio.Queue) -> None:
        self._clients.discard(q)

    # -------------- Internals --------------
    def _resolve_anchor_id(self) -> Optional[str]:
        return (
            os.getenv("ANCHOR_ID")
            or os.getenv("DOUYIN_ROOM_ID")
            or os.getenv("AI_ANCHOR_ID")
            or None
        )

    def _build_generator_config(self, anchor_id: Optional[str]) -> Dict[str, Any]:
        cfg = {
            "ai_service": os.getenv("AI_SERVICE", "qwen"),
            "ai_api_key": os.getenv("AI_API_KEY", DEFAULT_OPENAI_API_KEY),
            "ai_base_url": os.getenv("AI_BASE_URL", DEFAULT_OPENAI_BASE_URL),
            "ai_model": os.getenv("AI_MODEL", DEFAULT_OPENAI_MODEL),
        }
        if anchor_id:
            cfg["anchor_id"] = anchor_id
        return cfg

    def _init_workflow(self) -> None:
        try:
            cfg = self._build_generator_config(self._anchor_id)
            self._generator = LiveAnalysisGenerator(cfg)
            from ...ai.live_question_responder import LiveQuestionResponder  # local import to avoid cost when unused

            self._script_responder = LiveQuestionResponder(cfg)
            wf_config = LiveWorkflowConfig(anchor_id=self._anchor_id)
            self._workflow = ensure_workflow(
                analysis_generator=self._generator,
                config=wf_config,
            )
            self._state.anchor_id = self._anchor_id
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to initialize LangGraph workflow: %s", exc)
            self._generator = None
            self._script_responder = None
            self._workflow = None

    def _format_workflow_payload(self, result: Dict[str, Any]) -> Dict[str, Any]:
        card = result.get("analysis_card", {}) or {}
        persona_from_card = card.get("style_profile") if isinstance(card, dict) else None
        vibe_from_card = card.get("vibe") if isinstance(card, dict) else None

        payload = {
            "summary": result.get("summary"),
            "highlight_points": result.get("highlight_points", []),
            "risks": result.get("risks", []),
            "suggestions": result.get("suggestions", []),
            "top_questions": result.get("top_questions", []),
            "analysis_card": card,
            "topic_candidates": result.get("topic_candidates", []),
            "analysis_focus": result.get("analysis_focus"),
            "planner_notes": result.get("planner_notes", {}),
            "style_profile": persona_from_card if isinstance(persona_from_card, dict) else result.get("persona", {}),
            "vibe": vibe_from_card if isinstance(vibe_from_card, dict) else result.get("vibe", {}),
            "transcript_snippet": result.get("transcript_snippet", ""),
            "speech_stats": result.get("speech_stats", {}),
            "knowledge_snippets": result.get("knowledge_snippets", []),
            "knowledge_refs": result.get("knowledge_refs", []),
            "lead_candidates": result.get("lead_candidates", []),
            "error": result.get("analysis_error"),
        }
        if "speaker_timeline" in result:
            payload["speaker_timeline"] = result.get("speaker_timeline")
        playlist = result.get("topic_playlist") or []
        if not payload["error"]:
            if not playlist:
                try:
                    kb = get_knowledge_base()
                    queries: List[str] = []
                    planner = result.get("analysis_focus")
                    if isinstance(planner, str) and planner:
                        queries.append(planner)
                    for topic in result.get("topic_candidates") or []:
                        name = topic.get("topic") if isinstance(topic, dict) else None
                        if name:
                            queries.append(str(name))
                    
                    # 构建AI话题生成的上下文
                    context = {
                        'transcript': transcript or "",
                        'chat_messages': [],
                        'persona': result.get("persona", {}),
                        'vibe': result.get("vibe", {}),
                    }
                    
                    # 提取弹幕信息
                    chat_signals = result.get("chat_signals") or []
                    for signal in chat_signals[-10:]:  # 最近10条弹幕
                        if isinstance(signal, dict) and signal.get("text"):
                            context['chat_messages'].append({
                                'content': signal.get("text"),
                                'user': signal.get("user", "观众")
                            })
                    
                    playlist = kb.topic_suggestions(
                        limit=6, 
                        keywords=queries,
                        context=context,
                        use_ai=True
                    )
                except Exception:  # pragma: no cover - defensive
                    playlist = []
        else:
            playlist = []
        payload["topic_playlist"] = playlist
        return payload

    def generate_answer_scripts(
        self,
        questions: List[str],
        transcript: Optional[str] = None,
        style_profile: Optional[Dict[str, Any]] = None,
        vibe: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        clean_questions = [str(q).strip() for q in questions if str(q).strip()]
        if not clean_questions:
            raise ValueError("缺少有效的问题内容")
        if not self._script_responder:
            raise RuntimeError("话术生成器未初始化")

        persona = style_profile or self._state.style_profile or {}
        vibe_payload = vibe or self._state.vibe or {}
        mood = vibe_payload.get("level") or vibe_payload.get("mood") or (self._state.last_result.get("vibe", {}).get("level") if isinstance(self._state.last_result, dict) else None)

        last_transcript = None
        if isinstance(self._state.last_result, dict):
            last_transcript = self._state.last_result.get("transcript_snippet")
        sentence_clip = "\n".join(self._state.sentences[-6:]) if self._state.sentences else ""
        transcript_snippet = transcript or last_transcript or sentence_clip

        context = {
            "questions": clean_questions,
            "persona": persona,
            "vibe": vibe_payload,
            "mood": mood,
            "transcript": transcript_snippet,
        }
        scripts = self._script_responder.generate(context)
        return {"scripts": scripts}

    def _run_workflow(
        self,
        sentences: List[str],
        comments: List[Dict[str, Any]],
        window_start: float,
        user_scores: Optional[Dict[str, Dict[str, Any]]] = None,
        speaker_sentences: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        if self._workflow is None:
            raise RuntimeError("LangGraph workflow not available")
        state: Dict[str, Any] = {
            "anchor_id": self._anchor_id or "default",
            "broadcaster_id": self._anchor_id or "default",
            "window_start": window_start,
            "sentences": sentences,
            "comments": comments,
            "user_scores": user_scores or {},
        }
        if speaker_sentences:
            state["speaker_timeline"] = speaker_sentences
        # 使用 run_in_executor 将同步调用转为异步，避免阻塞事件循环
        result = self._workflow.invoke(state)  # type: ignore[arg-type]
        return self._format_workflow_payload(result)
    
    async def _run_workflow_async(
        self,
        sentences: List[str],
        comments: List[Dict[str, Any]],
        window_start: float,
        user_scores: Optional[Dict[str, Dict[str, Any]]] = None,
        speaker_sentences: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """异步运行 workflow，避免阻塞事件循环"""
        loop = asyncio.get_event_loop()
        # 在线程池中执行同步的 workflow 调用
        result = await loop.run_in_executor(
            None,
            self._run_workflow,
            sentences,
            comments,
            window_start,
            user_scores,
            speaker_sentences,
        )
        return result

    async def _attach_hooks(self) -> None:
        # Subscribe to live_audio final sentences
        svc = get_live_audio_service()
        name = f"ai_{int(time.time()*1000)}"
        self._cb_name = name

        async def on_tr(msg: Dict[str, Any]) -> None:
            try:
                if not isinstance(msg, dict):
                    return
                if msg.get("type") != "transcription":
                    return
                data = msg.get("data") or {}
                if not data.get("is_final"):
                    return
                text = (data.get("text") or "").strip()
                if text:
                    self._state.sentences.append(text)
                    entry: Dict[str, Any] = {
                        "text": text,
                        "speaker": str(data.get("speaker") or "unknown"),
                        "timestamp": float(data.get("timestamp") or time.time()),
                        "confidence": float(data.get("confidence") or 0.0),
                    }
                    debug = data.get("speaker_debug")
                    if isinstance(debug, dict):
                        try:
                            entry["debug"] = {k: float(v) for k, v in debug.items() if isinstance(v, (int, float))}
                        except Exception:
                            entry["debug"] = debug
                    self._state.speaker_sentences.append(entry)
                    if len(self._state.speaker_sentences) > 200:
                        del self._state.speaker_sentences[:-200]
                    if len(self._state.sentences) > 200:
                        del self._state.sentences[:-200]
            except Exception:
                pass

        svc.add_transcription_callback(name, on_tr)

        # Subscribe to Douyin relay events (chat-like)
        relay = get_douyin_web_relay()
        self._relay_queue = await relay.register_client()

    async def _detach_hooks(self) -> None:
        # Remove live_audio callback
        try:
            if self._cb_name:
                get_live_audio_service().remove_transcription_callback(self._cb_name)
        except Exception:
            pass
        self._cb_name = None
        # Unregister relay queue
        try:
            if self._relay_queue is not None:
                await get_douyin_web_relay().unregister_client(self._relay_queue)
        except Exception:
            pass
        self._relay_queue = None

    async def _run_loop(self) -> None:
        try:
            while self._state.active:
                await self._drain_relay_once()
                await self._maybe_analyze()
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            pass

    async def _drain_relay_once(self) -> None:
        q = self._relay_queue
        if q is None:
            return
        # drain a few items to keep up
        for _ in range(20):
            try:
                ev = q.get_nowait()
            except asyncio.QueueEmpty:
                break
            if isinstance(ev, dict) and ev.get("type") in {"chat", "gift", "like", "member", "emoji_chat"}:
                event_type = str(ev.get("type"))
                payload = ev.get("payload") or {}
                ts = int(time.time() * 1000)
                raw_user_id = payload.get("user_id_str") or payload.get("user_id")
                if isinstance(raw_user_id, bytes):
                    raw_user_id = raw_user_id.decode("utf-8", "ignore")
                user_id = str(raw_user_id) if raw_user_id not in (None, "", 0) else ""
                nickname = payload.get("nickname") or payload.get("user_name") or ""
                user_label = nickname or (user_id if user_id else "")
                user_key = user_id or user_label or "anonymous"
                msg: Dict[str, Any] = {
                    "type": event_type,
                    "user": user_label or "观众",
                    "user_id": user_id,
                    "user_key": user_key,
                    "content": str(payload.get("content") or ""),
                    "ts": ts,
                }

                if event_type == "gift":
                    gift_name = str(payload.get("gift_name") or "")
                    gift_count = int(payload.get("count") or 1)
                    diamond_count = int(payload.get("diamond_count") or 0)
                    if not diamond_count and payload.get("gift_value"):
                        try:
                            diamond_count = int(payload.get("gift_value"))
                        except Exception:
                            diamond_count = 0
                    fan_ticket = int(payload.get("fan_ticket_count") or 0)
                    gift_value = diamond_count * max(gift_count, 1)
                    msg.update(
                        {
                            "gift_name": gift_name,
                            "gift_count": gift_count,
                            "gift_value": gift_value,
                            "fan_ticket_count": fan_ticket,
                        }
                    )
                    msg["content"] = f"{msg['user']}送出{gift_name}x{gift_count}"
                elif event_type == "like":
                    like_count = int(payload.get("count") or 0)
                    msg.update({"like_count": like_count})
                    msg["content"] = f"{msg['user']}点赞+{like_count}" if like_count else f"{msg['user']}点了个赞"
                elif event_type == "member":
                    msg["content"] = f"{msg['user']}进入直播间"
                elif event_type == "emoji_chat":
                    emoji_text = payload.get("default_content") or payload.get("emoji_id") or ""
                    msg["content"] = f"{msg['user']}发送表情 {emoji_text}"

                metrics = self._state.user_scores.setdefault(
                    user_key,
                    {
                        "nickname": msg["user"],
                        "total_value": 0.0,
                        "gift_events": 0,
                        "chat_count": 0,
                        "last_ts": ts,
                    },
                )
                metrics["nickname"] = msg["user"] or metrics.get("nickname") or "观众"
                metrics["last_ts"] = ts
                if event_type == "gift":
                    gift_value = msg.get("gift_value") or 0
                    metrics["total_value"] = float(metrics.get("total_value", 0.0)) + float(gift_value or 0)
                    metrics["gift_events"] = metrics.get("gift_events", 0) + msg.get("gift_count", 1)
                elif event_type == "chat":
                    metrics["chat_count"] = metrics.get("chat_count", 0) + 1
                msg["user_total_value"] = metrics.get("total_value", 0.0)
                self._state.comments.append(msg)

    async def _maybe_analyze(self) -> None:
        s = self._state
        if _now_ms() - s.last_window_ts < s.window_sec * 1000:
            return
        # prepare window
        window_sentences = list(s.sentences[-100:])
        window_speaker_sentences = list(s.speaker_sentences[-100:])
        comments_window = list(s.comments[-200:])
        transcript = "\n".join(window_sentences)
        window_started_at = time.time()
        user_keys = {msg.get("user_key") for msg in comments_window if msg.get("user_key")}
        user_snapshot: Dict[str, Dict[str, Any]] = {}
        for key in user_keys:
            metrics = s.user_scores.get(key)
            if metrics:
                user_snapshot[key] = dict(metrics)
        s.last_window_ts = _now_ms()
        s.sentences.clear()
        s.comments.clear()
        s.speaker_sentences.clear()

        if not transcript and not comments_window:
            return

        # prune stale user scores (older than 10 minutes)
        cutoff_ms = _now_ms() - 600_000
        stale_keys = [
            key for key, metrics in list(s.user_scores.items())
            if int(metrics.get("last_ts") or 0) < cutoff_ms
        ]
        for key in stale_keys:
            s.user_scores.pop(key, None)

        # call AI (异步执行，避免阻塞事件循环)
        try:
            payload = await self._run_workflow_async(
                window_sentences,
                comments_window,
                window_started_at,
                user_snapshot,
                window_speaker_sentences,
            )
        except Exception as exc:
            logger.exception("LangGraph workflow failed, fallback to legacy analyzer: %s", exc)
            payload = {
                "summary": f"分析卡片生成失败：{exc}",
                "analysis_card": {"analysis_overview": f"分析卡片生成失败：{exc}"},
                "highlight_points": [],
                "risks": [f"workflow_error: {exc}"],
                "suggestions": ["请检查 Qwen3-Max 接口配置后重试。"],
                "topic_candidates": [],
            }

        # persist carry & context snapshots
        s.carry = str(payload.get("summary") or "")[:200]
        if isinstance(payload.get("style_profile"), dict):
            s.style_profile = payload.get("style_profile") or {}
        elif isinstance(payload.get("persona"), dict):
            # defensive fallback if legacy result used persona key
            s.style_profile = payload.get("persona") or {}
            payload.setdefault("style_profile", s.style_profile)
        else:
            payload.setdefault("style_profile", s.style_profile)

        if isinstance(payload.get("vibe"), dict):
            s.vibe = payload.get("vibe") or {}
        else:
            payload.setdefault("vibe", s.vibe)

        payload.setdefault("carry", s.carry)
        payload.setdefault("analysis_card", payload.get("analysis_card") or {})
        payload.setdefault("analysis_focus", payload.get("analysis_focus"))
        payload.setdefault("planner_notes", payload.get("planner_notes", {}))
        payload.setdefault("topic_candidates", [])

        s.last_result = payload
        await self._broadcast({"type": "ai", "payload": s.last_result, "timestamp": time.time()})

    async def _broadcast(self, event: Dict[str, Any]) -> None:
        for q in list(self._clients):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass


_ai_live_instance: Optional[AILiveAnalyzer] = None


def get_ai_live_analyzer() -> AILiveAnalyzer:
    global _ai_live_instance
    if _ai_live_instance is None:
        _ai_live_instance = AILiveAnalyzer()
    return _ai_live_instance
