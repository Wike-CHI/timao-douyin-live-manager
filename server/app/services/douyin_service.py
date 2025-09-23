# -*- coding: utf-8 -*-
"""抖音直播数据抓取服务（统一基于 DouyinLiveWebFetcher 实现）。"""

import asyncio
import logging
from contextlib import suppress
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from .douyin_web_relay import get_douyin_web_relay


class DouyinLiveService:
    """抖音直播监控服务（兼容旧 API 接口）。"""

    def __init__(self):
        self.handler = None
        self.is_monitoring = False
        self.current_room_id: Optional[str] = None
        self.current_live_id: Optional[str] = None
        self.message_callbacks: Dict[str, Callable] = {}

        self._relay = get_douyin_web_relay()
        self._client_queue: Optional[asyncio.Queue] = None
        self._queue_consumer: Optional[asyncio.Task] = None

        self.logger = logging.getLogger(__name__)
        self.event_handlers = {
            "chat": self._handle_chat_message,
            "gift": self._handle_gift_message,
            "like": self._handle_like_message,
            "member": self._handle_member_message,
            "follow": self._handle_follow_message,
            "fansclub": self._handle_fansclub_message,
            "emoji_chat": self._handle_emoji_message,
            "room_info": self._handle_room_info_message,
            "room_stats": self._handle_room_stats_message,
            "room_user_stats": self._handle_room_user_stats_message,
            "room_rank": self._handle_room_rank_message,
            "room_control": self._handle_room_control_message,
            "stream_adaptation": self._handle_stream_adaptation_message,
        }

    async def start_monitoring(
        self,
        live_id: str,
        message_callback: Optional[Callable] = None,
        cookie: Optional[str] = None,
    ) -> Dict[str, Any]:  # noqa: ARG002
        """启动直播监控（与旧接口保持一致）。"""
        try:
            if self.is_monitoring:
                return {"success": False, "error": "已在监控中"}

            self.message_callbacks.clear()
            if message_callback:
                self.message_callbacks["external"] = message_callback

            relay_result = await self._relay.start(live_id)
            if not relay_result.get("success"):
                return relay_result

            self.is_monitoring = True
            self.current_live_id = live_id
            self.current_room_id = None

            self._client_queue = await self._relay.register_client()
            self._queue_consumer = asyncio.create_task(self._consume_events())

            for _ in range(20):
                status = self._relay.get_status()
                if status.room_id:
                    self.current_room_id = status.room_id
                    break
                await asyncio.sleep(0.25)

            return {
                "success": True,
                "room_id": self.current_room_id,
                "live_id": self.current_live_id,
                "room_name": "",
                "user_unique_id": None,
            }
        except Exception as exc:  # pragma: no cover - 运行时异常记录
            self.logger.error(f"启动监控失败: {exc}")
            self.is_monitoring = False
            return {"success": False, "error": str(exc)}

    async def stop_monitoring(self) -> Dict[str, Any]:
        """停止直播监控。"""
        try:
            if not self.is_monitoring:
                return {"success": True, "message": "未在监控，已忽略"}

            if self._queue_consumer:
                self._queue_consumer.cancel()
                with suppress(asyncio.CancelledError):
                    await self._queue_consumer
                self._queue_consumer = None

            if self._client_queue is not None:
                await self._relay.unregister_client(self._client_queue)
                self._client_queue = None

            await self._relay.stop()

            self.is_monitoring = False
            self.current_room_id = None
            self.current_live_id = None
            return {"success": True}
        except Exception as exc:  # pragma: no cover
            self.logger.error(f"停止监控失败: {exc}")
            return {"success": False, "error": str(exc)}

    async def _consume_events(self) -> None:
        queue = self._client_queue
        if queue is None:
            return
        try:
            while True:
                event = await queue.get()
                if event is None:
                    continue
                event_type = event.get("type")
                payload = event.get("payload", {})
                if event_type == "status":
                    stage = payload.get("stage")
                    if stage == "room_ready":
                        self.current_room_id = payload.get("room_id")
                    if stage == "stopped":
                        self.is_monitoring = False
                        break
                    continue
                handler = self.event_handlers.get(event_type)
                if handler:
                    await handler(payload)
                else:
                    await self._notify_callbacks(event_type, payload)
        except asyncio.CancelledError:
            pass
        finally:
            if self._client_queue is not None:
                await self._relay.unregister_client(self._client_queue)
                self._client_queue = None

    async def _handle_chat_message(self, message: Dict[str, Any]) -> None:
        try:
            data = {
                "type": "chat",
                "content": message.get("content"),
                "nickname": message.get("nickname"),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
            }
            await self._notify_callbacks("chat", data)
        except Exception as exc:
            self.logger.error(f"处理聊天消息失败: {exc}")

    async def _handle_gift_message(self, message: Dict[str, Any]) -> None:
        try:
            data = {
                "type": "gift",
                "gift_name": message.get("gift_name"),
                "count": message.get("count", 1),
                "nickname": message.get("nickname"),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
            }
            await self._notify_callbacks("gift", data)
        except Exception as exc:
            self.logger.error(f"处理礼物消息失败: {exc}")

    async def _handle_like_message(self, message: Dict[str, Any]) -> None:
        try:
            data = {
                "type": "like",
                "count": message.get("count", 1),
                "nickname": message.get("nickname"),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
            }
            await self._notify_callbacks("like", data)
        except Exception as exc:
            self.logger.error(f"处理点赞消息失败: {exc}")

    async def _handle_member_message(self, message: Dict[str, Any]) -> None:
        try:
            data = {
                "type": "member",
                "action": message.get("action", "enter"),
                "nickname": message.get("nickname"),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
            }
            await self._notify_callbacks("member", data)
        except Exception as exc:
            self.logger.error(f"处理成员消息失败: {exc}")

    async def _handle_room_rank_message(self, message: Dict[str, Any]) -> None:
        try:
            data = {
                "type": "room_rank",
                "ranks": message.get("ranks", []),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
            }
            await self._notify_callbacks("room_rank", data)
        except Exception as exc:
            self.logger.error(f"处理房间排行榜失败: {exc}")

    async def _handle_follow_message(self, message: Dict[str, Any]) -> None:
        try:
            data = {
                "type": "follow",
                "nickname": message.get("nickname"),
                "user_id": message.get("user_id"),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
                "action": message.get("action"),
            }
            await self._notify_callbacks("follow", data)
        except Exception as exc:
            self.logger.error(f"处理关注消息失败: {exc}")

    async def _handle_fansclub_message(self, message: Dict[str, Any]) -> None:
        try:
            data = {
                "type": "fansclub",
                "content": message.get("content"),
                "nickname": message.get("nickname"),
                "user_id": message.get("user_id"),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
            }
            await self._notify_callbacks("fansclub", data)
        except Exception as exc:
            self.logger.error(f"处理粉丝团消息失败: {exc}")

    async def _handle_emoji_message(self, message: Dict[str, Any]) -> None:
        try:
            data = {
                "type": "emoji_chat",
                "emoji_id": message.get("emoji_id"),
                "content": message.get("default_content"),
                "nickname": message.get("nickname"),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
            }
            await self._notify_callbacks("emoji_chat", data)
        except Exception as exc:
            self.logger.error(f"处理表情弹幕失败: {exc}")

    async def _handle_room_info_message(self, message: Dict[str, Any]) -> None:
        try:
            await self._notify_callbacks("room_info", message)
        except Exception as exc:
            self.logger.error(f"处理直播间信息失败: {exc}")

    async def _handle_room_stats_message(self, message: Dict[str, Any]) -> None:
        try:
            await self._notify_callbacks("room_stats", message)
        except Exception as exc:
            self.logger.error(f"处理直播间统计消息失败: {exc}")

    async def _handle_room_user_stats_message(self, message: Dict[str, Any]) -> None:
        try:
            await self._notify_callbacks("room_user_stats", message)
        except Exception as exc:
            self.logger.error(f"处理直播间用户统计失败: {exc}")

    async def _handle_room_control_message(self, message: Dict[str, Any]) -> None:
        try:
            status = message.get("status")
            if status == 3:
                self.is_monitoring = False
            await self._notify_callbacks("room_control", message)
        except Exception as exc:
            self.logger.error(f"处理直播间控制消息失败: {exc}")

    async def _handle_stream_adaptation_message(self, message: Dict[str, Any]) -> None:
        try:
            await self._notify_callbacks("stream_adaptation", message)
        except Exception as exc:
            self.logger.error(f"处理直播间流配置消息失败: {exc}")

    async def _notify_callbacks(self, message_type: str, data: Dict[str, Any]):
        try:
            callback = self.message_callbacks.get("external")
            if callback:
                result = callback(message_type, data)
                if asyncio.iscoroutine(result):
                    await result
        except Exception as exc:
            self.logger.error(f"消息回调通知失败: {exc}")

    def get_status(self) -> Dict[str, Any]:
        relay_status = self._relay.get_status()
        return {
            "is_monitoring": self.is_monitoring,
            "current_room_id": self.current_room_id or relay_status.room_id,
            "current_live_id": self.current_live_id or relay_status.live_id,
            "fetcher_status": {
                "is_running": relay_status.is_running,
                "room_id": relay_status.room_id,
                "live_id": relay_status.live_id,
                "callbacks_count": len(self.message_callbacks),
                "last_error": relay_status.last_error,
            },
        }


douyin_service: Optional[DouyinLiveService] = None


def get_douyin_service() -> DouyinLiveService:
    global douyin_service
    if douyin_service is None:
        douyin_service = DouyinLiveService()
    return douyin_service


if __name__ == "__main__":

    async def _test():
        svc = get_douyin_service()
        print("status:", svc.get_status())
        print("抖音直播服务已准备就绪")

    asyncio.run(_test())
