# -*- coding: utf-8 -*-
"""Live AI Analyzer Service

Collects final sentences from live_audio and chat events from Douyin web relay,
batches them into short windows, calls AI analysis (Qwen OpenAI-compatible), and
streams results to frontend via SSE.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

try:
    from ...ai.qwen_openai_compatible import analyze_window  # type: ignore
except Exception:  # pragma: no cover
    analyze_window = None  # type: ignore

from .live_audio_stream_service import get_live_audio_service
from .douyin_web_relay import get_douyin_web_relay


def _now_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class AIState:
    active: bool = False
    window_sec: int = 60
    last_window_ts: int = field(default_factory=_now_ms)
    carry: str = ""
    last_result: Dict[str, Any] = field(default_factory=dict)
    sentences: List[str] = field(default_factory=list)
    comments: List[Dict[str, Any]] = field(default_factory=list)
    # Persisted context for other modules to reuse/style-mimic
    style_profile: Dict[str, Any] = field(default_factory=dict)
    vibe: Dict[str, Any] = field(default_factory=dict)


class AILiveAnalyzer:
    def __init__(self) -> None:
        self._state = AIState()
        self._lock = asyncio.Lock()
        self._task: Optional[asyncio.Task] = None
        self._clients: Set[asyncio.Queue] = set()

        # hook ids for live_audio callbacks
        self._cb_name: Optional[str] = None
        self._relay_queue: Optional[asyncio.Queue] = None

    # -------------- Public API --------------
    async def start(self, window_sec: int = 90) -> Dict[str, Any]:
        async with self._lock:
            if self._state.active:
                return {"success": True, "message": "already running"}
            self._state = AIState(active=True, window_sec=max(30, int(window_sec)))
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
                # normalize minimal fields
                payload = ev.get("payload") or {}
                msg = {
                    "type": ev.get("type"),
                    "user": payload.get("nickname") or payload.get("user_id") or "",
                    "content": payload.get("content") or payload.get("gift_name") or "",
                    "ts": int(time.time() * 1000),
                }
                self._state.comments.append(msg)

    async def _maybe_analyze(self) -> None:
        s = self._state
        if _now_ms() - s.last_window_ts < s.window_sec * 1000:
            return
        # prepare window
        transcript = "\n".join(s.sentences[-100:])  # last 100 sentences
        comments = list(s.comments[-200:])  # last 200 events
        s.last_window_ts = _now_ms()
        s.sentences.clear()
        s.comments.clear()

        if not transcript and not comments:
            return

        # call AI
        try:
            if analyze_window is None:
                raise RuntimeError("AI analyzer not available")
            ai = analyze_window(transcript, comments, s.carry)  # type: ignore
            # persist carry for continuity if present
            if isinstance(ai, dict):
                s.carry = str(ai.get("carry") or "")[:200]
                s.last_result = ai
                # update style & vibe snapshots if provided
                if isinstance(ai.get("style_profile"), dict):
                    s.style_profile = ai.get("style_profile") or {}
                if isinstance(ai.get("vibe"), dict):
                    s.vibe = ai.get("vibe") or {}
            else:
                s.last_result = {"summary": str(ai)}
        except Exception as e:
            s.last_result = {"error": str(e)}
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
