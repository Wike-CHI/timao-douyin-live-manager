# -*- coding: utf-8 -*-
"""
抖音直播数据抓取服务
基于独立的抖音直播弹幕实时抓取模块
"""

import asyncio
import logging
import json
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime

# 导入适配器（避免在应用启动阶段加载抓取器实现）
from douyin_live_fecter_module.adapters import (
    CallbackAdapter,
    WebsocketBroadcasterAdapter,
    CompositeAdapter,
    LiveDataAdapter,
)

class DouyinLiveService:
    """抖音直播服务"""
    
    def __init__(self):
        """初始化抖音直播服务"""
        self.handler = None
        self.is_monitoring = False
        self.current_room_id = None
        self.current_live_id = None
        self.message_callbacks = {}
        self._fetcher = None
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        
        # 消息处理回调
        self.wss_callbacks = {
            "WebcastChatMessage": self._handle_chat_message,
            "WebcastGiftMessage": self._handle_gift_message,
            "WebcastLikeMessage": self._handle_like_message,
            "WebcastMemberMessage": self._handle_member_message,
            "WebcastSocialMessage": self._handle_social_message,
            "WebcastRoomUserSeqMessage": self._handle_room_user_seq_message,
            # 可以添加更多消息类型处理
        }
    
    async def start_monitoring(self, live_id: str, message_callback: Optional[Callable] = None, cookie: Optional[str] = None) -> Dict[str, Any]:
        """
        开始监控直播间（委派到 DouyinLiveFetcher）
        """
        try:
            if self.is_monitoring:
                return {"success": False, "error": "已在监控中"}

            # 延迟导入，避免在应用启动阶段触发依赖问题
            try:
                from douyin_live_fecter_module.service import DouyinLiveFetcher
            except Exception as ie:
                self.logger.error(f"导入 DouyinLiveFetcher 失败: {ie}")
                return {"success": False, "error": f"导入抓取器失败: {ie}"}

            # 清理旧回调
            self.message_callbacks.clear()
            if message_callback:
                self.message_callbacks["external"] = message_callback

            # 组装适配器：WebSocket 广播 + 回调转发
            adapters: List[LiveDataAdapter] = [WebsocketBroadcasterAdapter()]

            async def _forward(msg_type: str, data: Dict[str, Any]):
                # 通过现有回调机制转发，保持兼容
                await self._notify_callbacks(msg_type, data)

            adapters.append(CallbackAdapter(_forward))
            composite = CompositeAdapter(adapters)

            # 启动抓取器
            self._fetcher = DouyinLiveFetcher(adapter=composite)
            result = await self._fetcher.start(live_id, cookie=cookie)

            if not result.get("success"):
                # 启动失败，复位状态
                self._fetcher = None
                self.is_monitoring = False
                self.current_room_id = None
                self.current_live_id = None
                return {"success": False, "error": result.get("error", "未知错误")}

            # 启动成功，同步状态
            self.is_monitoring = True
            self.current_room_id = result.get("room_id")
            self.current_live_id = result.get("live_id")

            return {
                "success": True,
                "room_id": self.current_room_id,
                "live_id": self.current_live_id,
                "room_name": "",  # 保持旧接口字段，现阶段不可得
                "user_unique_id": result.get("user_unique_id", ""),
            }

        except Exception as e:
            self.logger.error(f"启动监控失败: {e}")
            self.is_monitoring = False
            return {"success": False, "error": str(e)}
    
    async def stop_monitoring(self) -> Dict[str, Any]:
        """
        停止监控直播间（委派到 DouyinLiveFetcher）
        """
        try:
            if not self.is_monitoring or not self._fetcher:
                return {"success": True, "message": "未在监控，已忽略"}

            result = await self._fetcher.stop()
            self.is_monitoring = False
            self.current_room_id = None
            self.current_live_id = None
            return {"success": True, **result}
        except Exception as e:
            self.logger.error(f"停止监控失败: {e}")
            return {"success": False, "error": str(e)}

    async def _start_websocket_monitoring(self, room_id: str, user_unique_id: str, 
                                        internal_ext: str, cursor: str):
        """（保留旧逻辑占位，不再直接使用）"""
        pass

    async def _handle_chat_message(self, message) -> None:
        """处理聊天消息（保留向后兼容的回调体系）"""
        try:
            data = {
                "type": "chat",
                "content": message.get("content"),
                "nickname": message.get("nickname"),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
            }
            await self._notify_callbacks("chat", data)
        except Exception as e:
            self.logger.error(f"处理聊天消息失败: {e}")

    async def _handle_gift_message(self, message) -> None:
        try:
            data = {
                "type": "gift",
                "gift_name": message.get("gift_name"),
                "count": message.get("count", 1),
                "nickname": message.get("nickname"),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
            }
            await self._notify_callbacks("gift", data)
        except Exception as e:
            self.logger.error(f"处理礼物消息失败: {e}")

    async def _handle_like_message(self, message) -> None:
        try:
            data = {
                "type": "like",
                "count": message.get("count", 1),
                "nickname": message.get("nickname"),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
            }
            await self._notify_callbacks("like", data)
        except Exception as e:
            self.logger.error(f"处理点赞消息失败: {e}")

    async def _handle_member_message(self, message) -> None:
        try:
            data = {
                "type": "member",
                "action": message.get("action", "enter"),
                "nickname": message.get("nickname"),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
            }
            await self._notify_callbacks("member", data)
        except Exception as e:
            self.logger.error(f"处理成员消息失败: {e}")

    async def _handle_social_message(self, message) -> None:
        try:
            data = {
                "type": "social",
                "action": message.get("action"),
                "nickname": message.get("nickname"),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
            }
            await self._notify_callbacks("social", data)
        except Exception as e:
            self.logger.error(f"处理社交消息失败: {e}")

    async def _handle_room_user_seq_message(self, message) -> None:
        try:
            data = {
                "type": "room_stats",
                "online": message.get("online", 0),
                "total": message.get("total", 0),
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
            }
            await self._notify_callbacks("room_stats", data)
        except Exception as e:
            self.logger.error(f"处理房间统计失败: {e}")

    async def _notify_callbacks(self, message_type: str, data: Dict[str, Any]):
        """统一的回调通知接口"""
        try:
            # 外部回调
            ext_cb = self.message_callbacks.get("external")
            if ext_cb:
                try:
                    await ext_cb(message_type, data)
                except Exception as e:
                    self.logger.error(f"外部回调处理失败: {e}")
        except Exception as e:
            self.logger.error(f"消息回调通知失败: {e}")

    def get_status(self) -> Dict[str, Any]:
        """获取服务监控状态（与 Fetcher 状态对齐）"""
        fetcher_status = None
        try:
            if self._fetcher:
                fs = self._fetcher.status()
                fetcher_status = {
                    "is_running": fs.is_running,
                    "room_id": fs.room_id,
                    "live_id": fs.live_id,
                    "callbacks_count": fs.callbacks_count,
                }
        except Exception as e:
            self.logger.error(f"获取抓取器状态失败: {e}")

        return {
            "is_monitoring": self.is_monitoring,
            "current_room_id": self.current_room_id,
            "current_live_id": self.current_live_id,
            "fetcher_status": fetcher_status or {
                "is_running": False,
                "room_id": None,
                "live_id": None,
                "callbacks_count": 0,
            },
        }

# 全局服务实例

douyin_service: Optional[DouyinLiveService] = None

def get_douyin_service() -> DouyinLiveService:
    global douyin_service
    if douyin_service is None:
        douyin_service = DouyinLiveService()
    return douyin_service

if __name__ == "__main__":
    async def test_douyin():
        svc = get_douyin_service()
        print("status:", svc.get_status())
        print("抖音直播服务已准备就绪")
    asyncio.run(test_douyin())
