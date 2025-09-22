# -*- coding: utf-8 -*-
"""Douyin 弹幕到 Web 网页的实时转发服务."""

from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set

from DouyinLiveWebFetcher.liveMan import (ChatMessage, DouyinLiveWebFetcher,
                                          GiftMessage, LikeMessage,
                                          MemberMessage, RoomRankMessage)


@dataclass
class RelayStatus:
    is_running: bool = False
    live_id: Optional[str] = None
    room_id: Optional[str] = None
    last_error: Optional[str] = None


class _WebRelayFetcher(DouyinLiveWebFetcher):
    """DouyinLiveWebFetcher 的特化版本, 将消息透传给回调."""

    def __init__(self, live_id: str, emitter: Callable[[Dict[str, Any]], None]):
        super().__init__(live_id)
        self._emit = emitter

    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        try:
            self._emit(
                {
                    "type": event_type,
                    "payload": payload,
                    "timestamp": time.time(),
                }
            )
        except Exception:
            # 回调失败时忽略，以免影响主体流程
            pass

    def stop(self):  # type: ignore[override]
        try:
            if hasattr(self, "ws") and getattr(self, "ws", None):
                super().stop()
        except Exception:
            pass

    def _wsOnOpen(self, ws):  # noqa: N802
        self._emit_event("status", {"stage": "connected"})
        super()._wsOnOpen(ws)

    def _wsOnError(self, ws, error):  # noqa: N802
        self._emit_event("error", {"message": str(error)})
        super()._wsOnError(ws, error)

    def _wsOnClose(self, ws, *args):  # noqa: N802
        self._emit_event("status", {"stage": "closed"})
        super()._wsOnClose(ws, *args)

    def _parseChatMsg(self, payload):  # noqa: N802
        message = ChatMessage().parse(payload)
        self._emit_event(
            "chat",
            {
                "user_id": message.user.id,
                "user_id_str": message.user.id_str,
                "nickname": message.user.nick_name,
                "content": message.content,
            },
        )

    def _parseGiftMsg(self, payload):  # noqa: N802
        message = GiftMessage().parse(payload)
        self._emit_event(
            "gift",
            {
                "user_id": message.user.id,
                "user_id_str": message.user.id_str,
                "nickname": message.user.nick_name,
                "gift_name": message.gift.name,
                "count": message.combo_count,
            },
        )

    def _parseLikeMsg(self, payload):  # noqa: N802
        # 点赞信息在测试页面中忽略
        return

    def _parseMemberMsg(self, payload):  # noqa: N802
        # 进场信息在测试页面中忽略
        return

    def _parseRankMsg(self, payload):  # noqa: N802
        message = RoomRankMessage().parse(payload)
        ranks: List[Dict[str, Any]] = []
        for item in message.ranks_list:
            avatar = None
            if item.user.avatar_thumb and item.user.avatar_thumb.url_list_list:
                avatar = item.user.avatar_thumb.url_list_list[0]
            ranks.append(
                {
                    "rank": item.rank,
                    "score": item.score,
                    "score_str": item.score_str,
                    "user_id": item.user.id,
                    "user_id_str": item.user.id_str,
                    "nickname": item.user.nick_name,
                    "avatar": avatar,
                }
            )
        if ranks:
            self._emit_event("room_rank", {"ranks": ranks})


class DouyinWebRelay:
    """管理 Douyin 抓取线程 -> Async Web 客户端的桥接器."""

    def __init__(self):
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._fetcher: Optional[_WebRelayFetcher] = None
        self._thread: Optional[threading.Thread] = None
        self._status = RelayStatus()
        self._clients: Set[asyncio.Queue] = set()
        self._last_status_event: Optional[Dict[str, Any]] = None
        self._last_rank_event: Optional[Dict[str, Any]] = None
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # 客户端管理
    # ------------------------------------------------------------------
    async def register_client(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._clients.add(queue)
        if self._last_status_event:
            queue.put_nowait(self._last_status_event)
        if self._last_rank_event:
            queue.put_nowait(self._last_rank_event)
        return queue

    async def unregister_client(self, queue: asyncio.Queue) -> None:
        self._clients.discard(queue)

    # ------------------------------------------------------------------
    # 启动 / 停止
    # ------------------------------------------------------------------
    async def start(self, live_id: str) -> Dict[str, Any]:
        async with self._lock:
            if self._status.is_running:
                if self._status.live_id == live_id:
                    return {"success": True, "message": "已经在抓取该直播间"}
                await self.stop()

            self._event_loop = asyncio.get_running_loop()
            self._status = RelayStatus(is_running=True, live_id=live_id)
            self._status.last_error = None
            self._status.room_id = None
            self._emit_status("starting", {"live_id": live_id})

            def emitter(event: Dict[str, Any]) -> None:
                if not self._event_loop:
                    return
                self._event_loop.call_soon_threadsafe(self._dispatch_event, event)

            self._fetcher = _WebRelayFetcher(live_id, emitter)

            def runner():
                try:
                    emitter(
                        {
                            "type": "status",
                            "payload": {"stage": "resolving_room"},
                            "timestamp": time.time(),
                        }
                    )
                    try:
                        self._fetcher.get_room_status()
                        room_id = getattr(self._fetcher, "room_id", None)
                        if room_id:
                            emitter(
                                {
                                    "type": "status",
                                    "payload": {
                                        "stage": "room_ready",
                                        "room_id": room_id,
                                    },
                                    "timestamp": time.time(),
                                }
                            )
                    except Exception as exc:
                        emitter(
                            {
                                "type": "error",
                                "payload": {"message": str(exc)},
                                "timestamp": time.time(),
                            }
                        )
                        return

                    self._fetcher.start()
                except Exception as exc:
                    emitter(
                        {
                            "type": "error",
                            "payload": {"message": str(exc)},
                            "timestamp": time.time(),
                        }
                    )
                finally:
                    if self._event_loop:
                        self._event_loop.call_soon_threadsafe(self._thread_finished)

            self._thread = threading.Thread(
                target=runner, name="DouyinWebRelay", daemon=True
            )
            self._thread.start()
            return {"success": True, "live_id": live_id}

    async def stop(self) -> Dict[str, Any]:
        async with self._lock:
            if not self._status.is_running:
                return {"success": True, "message": "未在运行"}

            fetcher = self._fetcher
            thread = self._thread
            self._status.is_running = False
            self._status.live_id = None

            if fetcher:
                await asyncio.to_thread(fetcher.stop)
            if thread and thread.is_alive():
                await asyncio.to_thread(thread.join, 5)

            self._emit_status("stopped", {})
            self._fetcher = None
            self._thread = None
            self._status.room_id = None
            return {"success": True}

    def _thread_finished(self) -> None:
        self._emit_status("stopped", {})
        self._fetcher = None
        self._thread = None
        self._status.is_running = False
        self._status.live_id = None
        self._status.room_id = None

    # ------------------------------------------------------------------
    # 事件派发
    # ------------------------------------------------------------------
    def _dispatch_event(self, event: Dict[str, Any]) -> None:
        event_type = event.get("type")
        if event_type == "status":
            stage = (event.get("payload") or {}).get("stage")
            if stage == "room_ready":
                self._status.room_id = (event.get("payload") or {}).get("room_id")
            elif stage == "stopped":
                self._status.room_id = None
            self._last_status_event = event
        elif event_type == "room_rank":
            self._last_rank_event = event
        elif event_type == "error":
            self._status.last_error = (event.get("payload") or {}).get("message")
        for queue in list(self._clients):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def _emit_status(
        self, stage: str, payload: Optional[Dict[str, Any]] = None
    ) -> None:
        data = {
            "type": "status",
            "payload": {"stage": stage, **(payload or {})},
            "timestamp": time.time(),
        }
        if self._event_loop:
            self._event_loop.call_soon_threadsafe(self._dispatch_event, data)

    def get_status(self) -> RelayStatus:
        return self._status


_relay_instance: Optional[DouyinWebRelay] = None


def get_douyin_web_relay() -> DouyinWebRelay:
    global _relay_instance
    if _relay_instance is None:
        _relay_instance = DouyinWebRelay()
    return _relay_instance
