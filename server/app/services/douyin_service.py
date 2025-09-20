# -*- coding: utf-8 -*-
"""
抖音直播数据抓取服务
基于F2项目的抖音直播弹幕实时抓取
"""

import asyncio
import logging
import sys
import json
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
from pathlib import Path

# 添加F2项目路径
F2_PATH = Path(__file__).parent.parent.parent.parent / "f2"
sys.path.insert(0, str(F2_PATH))

try:
    from f2.apps.douyin.handler import DouyinHandler
    from f2.apps.douyin.crawler import DouyinWebSocketCrawler
    from f2.apps.douyin.utils import TokenManager
    from f2.log.logger import logger as f2_logger
except ImportError as e:
    logging.error(f"F2项目导入失败: {e}")
    raise

from douyin_live_fecter_module import (
    DouyinLiveFetcher,
    CallbackAdapter,
    WebsocketBroadcasterAdapter,
    CompositeAdapter,
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
        
        # F2请求配置
        self.http_kwargs = {
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Referer": "https://www.douyin.com/",
                "Content-Type": "application/protobuffer;",
            },
            "proxies": {"http://": None, "https://": None},
            "timeout": 10,
            "cookie": f"ttwid={TokenManager.gen_ttwid()}; __live_version__=\"1.1.2.6631\"; live_use_vvc=\"false\";",
        }
        
        # WebSocket配置
        self.wss_kwargs = {
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Upgrade": "websocket",
                "Connection": "Upgrade",
            },
            "proxies": {"http://": None, "https://": None},
            "timeout": 10,
            "show_message": False,  # 不在终端显示弹幕
            "cookie": "",
        }
        
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
    
    async def start_monitoring(self, live_id: str, message_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        开始监控直播间（委派到 DouyinLiveFetcher）
        """
        try:
            if self.is_monitoring:
                return {"success": False, "error": "已在监控中"}

            # 清理旧回调
            self.message_callbacks.clear()
            if message_callback:
                self.message_callbacks["external"] = message_callback

            # 组装适配器：WebSocket 广播 + 回调转发
            adapters = [WebsocketBroadcasterAdapter()]

            async def _forward(msg_type: str, data: Dict[str, Any]):
                # 通过现有回调机制转发，保持兼容
                await self._notify_callbacks(msg_type, data)

            adapters.append(CallbackAdapter(_forward))
            composite = CompositeAdapter(adapters)

            # 启动抓取器
            self._fetcher = DouyinLiveFetcher(adapter=composite)
            result = await self._fetcher.start(live_id)

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
        停止监控（委派到 DouyinLiveFetcher）
        """
        try:
            if not self.is_monitoring:
                return {"success": False, "error": "未在监控中"}

            if self._fetcher is not None:
                try:
                    await self._fetcher.stop()
                except Exception as e:
                    self.logger.warning(f"停止抓取器时出错: {e}")

            self.is_monitoring = False
            self.current_room_id = None
            self.current_live_id = None
            self.message_callbacks.clear()
            self._fetcher = None

            self.logger.info("已停止直播间监控")
            return {"success": True, "message": "监控已停止"}

        except Exception as e:
            self.logger.error(f"停止监控失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _start_websocket_monitoring(self, room_id: str, user_unique_id: str, 
                                        internal_ext: str, cursor: str):
        """启动WebSocket监控"""
        try:
            wss_handler = DouyinHandler(self.wss_kwargs)
            
            # 开始接收弹幕
            await wss_handler.fetch_live_danmaku(
                room_id=room_id,
                user_unique_id=user_unique_id,
                internal_ext=internal_ext,
                cursor=cursor,
                wss_callbacks=self.wss_callbacks,
            )
            
        except Exception as e:
            self.logger.error(f"WebSocket监控错误: {e}")
            self.is_monitoring = False
    
    async def _handle_chat_message(self, message) -> None:
        """处理聊天消息"""
        try:
            chat_data = {
                "type": "chat",
                "id": str(message.msgId),
                "username": message.user.nickName,
                "content": message.content,
                "user_id": str(message.user.id),
                "user_level": getattr(message.user, 'level', 0),
                "timestamp": datetime.now().isoformat(),
                "room_id": self.current_room_id
            }
            
            self.logger.info(f"💬 {chat_data['username']}: {chat_data['content']}")
            
            # 调用外部回调
            await self._notify_callbacks("chat", chat_data)
            
        except Exception as e:
            self.logger.error(f"处理聊天消息失败: {e}")
    
    async def _handle_gift_message(self, message) -> None:
        """处理礼物消息"""
        try:
            gift_data = {
                "type": "gift",
                "id": str(message.msgId),
                "username": message.user.nickName,
                "gift_name": message.gift.name,
                "gift_count": message.comboCount,
                "gift_id": message.gift.id,
                "timestamp": datetime.now().isoformat(),
                "room_id": self.current_room_id
            }
            
            self.logger.info(f"🎁 {gift_data['username']} 送出 {gift_data['gift_name']} x{gift_data['gift_count']}")
            
            # 调用外部回调
            await self._notify_callbacks("gift", gift_data)
            
        except Exception as e:
            self.logger.error(f"处理礼物消息失败: {e}")
    
    async def _handle_like_message(self, message) -> None:
        """处理点赞消息"""
        try:
            like_data = {
                "type": "like",
                "id": str(message.msgId),
                "username": message.user.nickName,
                "like_count": message.count,
                "timestamp": datetime.now().isoformat(),
                "room_id": self.current_room_id
            }
            
            self.logger.debug(f"👍 {like_data['username']} 点赞 x{like_data['like_count']}")
            
            # 调用外部回调
            await self._notify_callbacks("like", like_data)
            
        except Exception as e:
            self.logger.error(f"处理点赞消息失败: {e}")
    
    async def _handle_member_message(self, message) -> None:
        """处理成员进入消息"""
        try:
            member_data = {
                "type": "member",
                "id": str(message.msgId),
                "username": message.user.nickName,
                "action": "enter",
                "timestamp": datetime.now().isoformat(),
                "room_id": self.current_room_id
            }
            
            self.logger.debug(f"👋 {member_data['username']} 进入直播间")
            
            # 调用外部回调
            await self._notify_callbacks("member", member_data)
            
        except Exception as e:
            self.logger.error(f"处理成员消息失败: {e}")
    
    async def _handle_social_message(self, message) -> None:
        """处理社交消息"""
        try:
            social_data = {
                "type": "social",
                "id": str(message.msgId),
                "username": message.user.nickName,
                "action": "follow",  # 或其他社交行为
                "timestamp": datetime.now().isoformat(),
                "room_id": self.current_room_id
            }
            
            self.logger.info(f"💖 {social_data['username']} 关注了主播")
            
            # 调用外部回调
            await self._notify_callbacks("social", social_data)
            
        except Exception as e:
            self.logger.error(f"处理社交消息失败: {e}")
    
    async def _handle_room_user_seq_message(self, message) -> None:
        """处理房间用户序列消息"""
        try:
            # 这种消息通常包含观众数量等信息
            seq_data = {
                "type": "room_stats",
                "online_count": getattr(message, 'total', 0),
                "timestamp": datetime.now().isoformat(),
                "room_id": self.current_room_id
            }
            
            self.logger.debug(f"📊 当前观众数: {seq_data['online_count']}")
            
            # 调用外部回调
            await self._notify_callbacks("room_stats", seq_data)
            
        except Exception as e:
            self.logger.error(f"处理房间统计失败: {e}")
    
    async def _notify_callbacks(self, message_type: str, data: Dict[str, Any]):
        """通知所有回调函数"""
        for callback_name, callback in self.message_callbacks.items():
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message_type, data)
                else:
                    callback(message_type, data)
            except Exception as e:
                self.logger.error(f"回调函数 {callback_name} 执行失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态（融合 fetcher 状态）"""
        status = {
            "is_monitoring": self.is_monitoring,
            "current_room_id": self.current_room_id,
            "current_live_id": self.current_live_id,
            "callbacks_count": len(self.message_callbacks),
        }
        try:
            if self._fetcher is not None:
                fs = self._fetcher.status()
                # 顶层状态与 fetcher 对齐
                status.update({
                    "is_monitoring": fs.is_running,
                    "current_room_id": fs.room_id,
                    "current_live_id": fs.live_id,
                })
                # 追加 fetcher_status 以满足 API 契约
                status["fetcher_status"] = {
                    "is_running": fs.is_running,
                    "room_id": fs.room_id,
                    "live_id": fs.live_id,
                    "callbacks_count": getattr(fs, "callbacks_count", 0),
                }
        except Exception:
            pass
        return status

# 全局服务实例
douyin_service: Optional[DouyinLiveService] = None

def get_douyin_service() -> DouyinLiveService:
    """获取抖音服务实例"""
    global douyin_service
    if douyin_service is None:
        douyin_service = DouyinLiveService()
    return douyin_service

if __name__ == "__main__":
    # 测试代码
    async def test_douyin():
        service = DouyinLiveService()
        
        def message_handler(msg_type, data):
            print(f"收到消息 [{msg_type}]: {data}")
        
        # 测试监控 (需要真实的live_id)
        # result = await service.start_monitoring("277303127629", message_handler)
        # print(f"监控结果: {result}")
        
        print("抖音服务初始化成功")
    
    asyncio.run(test_douyin())