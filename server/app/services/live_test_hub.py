# -*- coding: utf-8 -*-
"""Combined Douyin + AST live test hub."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from contextlib import suppress
from typing import Any, Dict, Optional, Set

from server.modules.ast.ast_service import TranscriptionResult, get_ast_service

from .douyin_web_relay import get_douyin_web_relay


@dataclass
class LiveTestStatus:
    is_running: bool = False
    live_id: Optional[str] = None
    ast_running: bool = False
    douyin_running: bool = False
    last_error: Optional[str] = None


class LiveTestHub:
    """Hub bridging SenseVoice transcription and Douyin live fetcher."""

    def __init__(self) -> None:
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._status = LiveTestStatus()
        self._lock = asyncio.Lock()

        # Douyin relay integration
        self._douyin_queue: Optional[asyncio.Queue] = None
        self._douyin_forward_task: Optional[asyncio.Task] = None

        # AST integration
        self._ast_callback_name: Optional[str] = None
        self._ast_service = None

        # SSE client queues
        self._clients: Set[asyncio.Queue] = set()
        self._last_status_event: Optional[Dict[str, Any]] = None

    async def start(self, live_id: str) -> Dict[str, Any]:
        async with self._lock:
            if self._status.is_running:
                if self._status.live_id == live_id:
                    return {"success": True, "message": "已在运行", "live_id": live_id}
                await self._stop_locked()

            self._loop = asyncio.get_running_loop()
            self._status = LiveTestStatus(is_running=True, live_id=live_id)
            self._emit_status("live_test_starting", {"live_id": live_id})

            try:
                await self._start_douyin(live_id)
                await self._start_ast(live_id)
                self._emit_status("live_test_started", {"live_id": live_id})
                return {"success": True, "live_id": live_id}
            except Exception as exc:  # pragma: no cover - runtime failures logged
                self._status.last_error = str(exc)
                self._emit_status(
                    "live_test_error",
                    {"message": str(exc)},
                )
                await self._stop_locked()
                return {"success": False, "error": str(exc)}

    async def stop(self) -> Dict[str, Any]:
        async with self._lock:
            if not self._status.is_running:
                return {"success": True, "message": "未在运行"}
            await self._stop_locked()
            return {"success": True}

    async def _start_douyin(self, live_id: str) -> None:
        relay = get_douyin_web_relay()
        result = await relay.start(live_id)
        if not result.get("success"):
            raise RuntimeError(result.get("error") or "启动 Douyin 抓取失败")

        self._douyin_queue = await relay.register_client()
        self._douyin_forward_task = asyncio.create_task(self._forward_douyin_events())
        self._status.douyin_running = True
        self._emit_status("douyin_started", {"live_id": live_id})

    async def _start_ast(self, live_id: str) -> None:
        ast_service = get_ast_service()

        init_ok = await ast_service.initialize()
        if not init_ok:
            raise RuntimeError("SenseVoice 服务初始化失败，请检查麦克风与依赖")

        if ast_service.is_running:
            await ast_service.stop_transcription()

        callback_name = f"live_test_transcription_{id(self)}"

        async def on_transcription(result: TranscriptionResult) -> None:
            payload = {
                "text": result.text,
                "confidence": result.confidence,
                "timestamp": result.timestamp,
                "is_final": result.is_final,
                "room_id": result.room_id,
                "source": "ast",
            }
            self._post_event({"type": "transcription", "payload": payload})

        ast_service.add_transcription_callback(callback_name, on_transcription)

        started = await ast_service.start_transcription(live_id, session_id=f"live_test:{live_id}")
        if not started:
            ast_service.remove_transcription_callback(callback_name)
            raise RuntimeError("语音转录启动失败，请检查麦克风权限")

        self._ast_callback_name = callback_name
        self._ast_service = ast_service
        self._status.ast_running = True
        self._emit_status("ast_started", {"live_id": live_id})

    async def _forward_douyin_events(self) -> None:
        queue = self._douyin_queue
        relay = get_douyin_web_relay()
        try:
            while queue is not None:
                event = await queue.get()
                if event is None:
                    continue
                payload = event.get("payload") or {}
                payload.setdefault("source", "douyin")
                event["payload"] = payload
                self._dispatch_event(event)
        except asyncio.CancelledError:  # pragma: no cover
            pass
        finally:
            if queue is not None:
                await relay.unregister_client(queue)

    def _post_event(self, event: Dict[str, Any]) -> None:
        if not self._loop:
            return
        self._loop.call_soon_threadsafe(self._dispatch_event, event)

    def _emit_status(self, stage: str, payload: Optional[Dict[str, Any]] = None) -> None:
        data = {
            "type": "status",
            "payload": {"stage": stage, "source": "live_test", **(payload or {})},
            "timestamp": time.time(),
        }
        self._dispatch_event(data)

    def _dispatch_event(self, event: Dict[str, Any]) -> None:
        event_type = event.get("type")
        if event_type == "status":
            payload = event.get("payload") or {}
            source = payload.get("source")
            stage = payload.get("stage")
            if source == "live_test":
                if stage == "live_test_started":
                    self._status.is_running = True
                elif stage == "live_test_stopped":
                    self._status.is_running = False
                elif stage == "live_test_error":
                    self._status.last_error = payload.get("message")
            elif source == "douyin":
                if stage in {"connected", "room_ready"}:
                    self._status.douyin_running = True
                elif stage in {"stopped", "closed"}:
                    self._status.douyin_running = False
            elif source == "ast":
                if stage == "ast_started":
                    self._status.ast_running = True
                elif stage == "ast_stopped":
                    self._status.ast_running = False
            self._last_status_event = event

        for queue in list(self._clients):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    async def _stop_locked(self) -> None:
        if self._douyin_forward_task:
            self._douyin_forward_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._douyin_forward_task
        self._douyin_forward_task = None

        relay = get_douyin_web_relay()
        if self._douyin_queue is not None:
            await relay.unregister_client(self._douyin_queue)
        self._douyin_queue = None
        await relay.stop()

        if self._ast_service and self._ast_callback_name:
            self._ast_service.remove_transcription_callback(self._ast_callback_name)
            with suppress(Exception):
                await self._ast_service.stop_transcription()
        self._ast_callback_name = None
        self._ast_service = None

        previous_live_id = self._status.live_id
        last_error = self._status.last_error
        ast_was_running = self._status.ast_running
        douyin_was_running = self._status.douyin_running

        self._status = LiveTestStatus(last_error=last_error)
        if douyin_was_running:
            self._emit_status("douyin_stopped", {"live_id": previous_live_id})
        if ast_was_running:
            self._emit_status("ast_stopped", {"live_id": previous_live_id})
        self._emit_status("live_test_stopped", {"live_id": previous_live_id})

    async def register_client(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._clients.add(queue)
        if self._last_status_event:
            queue.put_nowait(self._last_status_event)
        return queue

    async def unregister_client(self, queue: asyncio.Queue) -> None:
        self._clients.discard(queue)

    def get_status(self) -> LiveTestStatus:
        return self._status


_hub_instance: Optional[LiveTestHub] = None


def get_live_test_hub() -> LiveTestHub:
    global _hub_instance
    if _hub_instance is None:
        _hub_instance = LiveTestHub()
    return _hub_instance
