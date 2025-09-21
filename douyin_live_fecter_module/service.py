#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
抖音直播抓取模块 - 基于项目内置的 DouyinLiveWebFetcher 实现
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
import sys
import os

# 添加DouyinLiveWebFetcher路径
DOUYIN_WEB_FETCHER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'DouyinLiveWebFetcher')
if DOUYIN_WEB_FETCHER_PATH not in sys.path:
    sys.path.insert(0, DOUYIN_WEB_FETCHER_PATH)

try:
    from liveMan import DouyinLiveWebFetcher
    DOUYIN_WEB_FETCHER_AVAILABLE = True
except ImportError as e:
    print(f"DouyinLiveWebFetcher不可用: {e}")
    DOUYIN_WEB_FETCHER_AVAILABLE = False


class FetcherStatus(Enum):
    """抓取器状态枚举"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class FetcherStatusInfo:
    """抓取器状态信息"""
    status: FetcherStatus
    room_id: Optional[str] = None
    live_id: Optional[str] = None
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    message_count: int = 0


class DouyinLiveFetcher:
    """
    抖音直播抓取器 - 基于 DouyinLiveWebFetcher 实现
    """
    
    def __init__(self, adapters: List[Any] = None):
        """
        初始化抓取器
        
        Args:
            adapters: 适配器列表，用于处理抓取到的数据
        """
        self.adapters = adapters or []
        self.logger = logging.getLogger(__name__)
        
        # 状态管理
        self._status = FetcherStatus.IDLE
        self._status_info = FetcherStatusInfo(status=self._status)
        self._fetcher_thread = None
        self._stop_event = threading.Event()
        
        # DouyinLiveWebFetcher实例
        self._web_fetcher = None
        self._current_live_id = None
        
        # 回调函数
        self._on_message_callback = None
        self._on_status_change_callback = None
        
        # 检查依赖可用性
        if not DOUYIN_WEB_FETCHER_AVAILABLE:
            self.logger.error("DouyinLiveWebFetcher不可用，无法启动抓取")
    
    def set_message_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """设置消息回调函数"""
        self._on_message_callback = callback
    
    def set_status_change_callback(self, callback: Callable[[FetcherStatusInfo], None]):
        """设置状态变化回调函数"""
        self._on_status_change_callback = callback
    
    def _update_status(self, status: FetcherStatus, **kwargs):
        """更新状态"""
        self._status = status
        self._status_info.status = status
        
        for key, value in kwargs.items():
            if hasattr(self._status_info, key):
                setattr(self._status_info, key, value)
        
        if self._on_status_change_callback:
            try:
                self._on_status_change_callback(self._status_info)
            except Exception as e:
                self.logger.error(f"状态变化回调执行失败: {e}")
    
    def _send_message(self, message_type: str, data: Dict[str, Any]):
        """发送消息到适配器"""
        self._status_info.message_count += 1
        
        # 调用回调函数
        if self._on_message_callback:
            try:
                self._on_message_callback(message_type, data)
            except Exception as e:
                self.logger.error(f"消息回调执行失败: {e}")
        
        # 发送到适配器
        for adapter in self.adapters:
            try:
                if hasattr(adapter, 'handle_message'):
                    adapter.handle_message(message_type, data)
                elif hasattr(adapter, 'on_message'):
                    adapter.on_message(message_type, data)
            except Exception as e:
                self.logger.error(f"适配器处理消息失败: {e}")
    
    def start_fetch(self, live_id: str, **kwargs) -> bool:
        """
        开始抓取直播数据
        
        Args:
            live_id: 直播间ID
            **kwargs: 其他参数（兼容性保留）
            
        Returns:
            bool: 启动是否成功
        """
        if not DOUYIN_WEB_FETCHER_AVAILABLE:
            self.logger.error("DouyinLiveWebFetcher不可用")
            self._update_status(FetcherStatus.ERROR, error_message="DouyinLiveWebFetcher不可用")
            return False
        
        if self._status != FetcherStatus.IDLE:
            self.logger.warning(f"抓取器状态为 {self._status.value}，无法启动")
            return False
        
        self._current_live_id = live_id
        self._stop_event.clear()
        
        # 启动抓取线程
        self._fetcher_thread = threading.Thread(
            target=self._fetch_worker,
            args=(live_id,),
            daemon=True
        )
        
        self._update_status(
            FetcherStatus.STARTING,
            live_id=live_id,
            start_time=time.time(),
            message_count=0
        )
        
        self._fetcher_thread.start()
        return True
    
    def stop_fetch(self) -> bool:
        """
        停止抓取
        
        Returns:
            bool: 停止是否成功
        """
        if self._status not in [FetcherStatus.RUNNING, FetcherStatus.STARTING]:
            self.logger.warning(f"抓取器状态为 {self._status.value}，无需停止")
            return False
        
        self._update_status(FetcherStatus.STOPPING)
        self._stop_event.set()
        
        # 停止WebFetcher
        if self._web_fetcher:
            try:
                self._web_fetcher.stop()
            except Exception as e:
                self.logger.error(f"停止WebFetcher失败: {e}")
        
        # 等待线程结束
        if self._fetcher_thread and self._fetcher_thread.is_alive():
            self._fetcher_thread.join(timeout=5.0)
        
        self._update_status(FetcherStatus.IDLE)
        return True
    
    def _fetch_worker(self, live_id: str):
        """抓取工作线程"""
        try:
            self.logger.info(f"开始抓取直播间 {live_id}")
            
            # 创建自定义的DouyinLiveWebFetcher
            class CustomDouyinLiveWebFetcher(DouyinLiveWebFetcher):
                def __init__(self, live_id, parent_fetcher):
                    super().__init__(live_id)
                    self.parent_fetcher = parent_fetcher
                
                def _parseChatMsg(self, payload):
                    """重写聊天消息处理"""
                    try:
                        from protobuf.douyin import ChatMessage
                        message = ChatMessage().parse(payload)
                        user_name = message.user.nick_name
                        user_id = message.user.id
                        content = message.content
                        
                        # 发送到适配器
                        self.parent_fetcher._send_message('chat', {
                            'user_id': str(user_id),
                            'user_name': user_name,
                            'content': content,
                            'timestamp': time.time()
                        })
                    except Exception as e:
                        self.parent_fetcher.logger.error(f"处理聊天消息失败: {e}")
                
                def _parseGiftMsg(self, payload):
                    """重写礼物消息处理"""
                    try:
                        from protobuf.douyin import GiftMessage
                        message = GiftMessage().parse(payload)
                        user_name = message.user.nick_name
                        user_id = message.user.id
                        gift_name = message.gift.name
                        gift_cnt = message.combo_count
                        
                        # 发送到适配器
                        self.parent_fetcher._send_message('gift', {
                            'user_id': str(user_id),
                            'user_name': user_name,
                            'gift_name': gift_name,
                            'gift_count': gift_cnt,
                            'timestamp': time.time()
                        })
                    except Exception as e:
                        self.parent_fetcher.logger.error(f"处理礼物消息失败: {e}")
                
                def _parseLikeMsg(self, payload):
                    """重写点赞消息处理"""
                    try:
                        from protobuf.douyin import LikeMessage
                        message = LikeMessage().parse(payload)
                        user_name = message.user.nick_name
                        user_id = message.user.id
                        count = message.count
                        
                        # 发送到适配器
                        self.parent_fetcher._send_message('like', {
                            'user_id': str(user_id),
                            'user_name': user_name,
                            'count': count,
                            'timestamp': time.time()
                        })
                    except Exception as e:
                        self.parent_fetcher.logger.error(f"处理点赞消息失败: {e}")
                
                def _parseMemberMsg(self, payload):
                    """重写进入直播间消息处理"""
                    try:
                        from protobuf.douyin import MemberMessage
                        message = MemberMessage().parse(payload)
                        user_name = message.user.nick_name
                        user_id = message.user.id
                        gender = ["女", "男"][message.user.gender] if message.user.gender in [0, 1] else "未知"
                        
                        # 发送到适配器
                        self.parent_fetcher._send_message('member', {
                            'user_id': str(user_id),
                            'user_name': user_name,
                            'gender': gender,
                            'action': 'enter',
                            'timestamp': time.time()
                        })
                    except Exception as e:
                        self.parent_fetcher.logger.error(f"处理进场消息失败: {e}")
                
                def _wsOnOpen(self, ws):
                    """WebSocket连接成功"""
                    super()._wsOnOpen(ws)
                    self.parent_fetcher._update_status(FetcherStatus.RUNNING)
                
                def _wsOnError(self, ws, error):
                    """WebSocket错误"""
                    super()._wsOnError(ws, error)
                    self.parent_fetcher._update_status(
                        FetcherStatus.ERROR,
                        error_message=str(error)
                    )
                
                def _wsOnClose(self, ws, *args):
                    """WebSocket关闭"""
                    super()._wsOnClose(ws, *args)
                    if not self.parent_fetcher._stop_event.is_set():
                        # 非主动停止，可能是连接断开
                        self.parent_fetcher.logger.warning("WebSocket连接意外断开")
            
            # 创建并启动WebFetcher
            self._web_fetcher = CustomDouyinLiveWebFetcher(live_id, self)
            
            # 获取房间状态
            try:
                self._web_fetcher.get_room_status()
                room_id = self._web_fetcher.room_id
                self._update_status(FetcherStatus.RUNNING, room_id=room_id)
            except Exception as e:
                self.logger.error(f"获取房间状态失败: {e}")
                self._update_status(FetcherStatus.ERROR, error_message=f"获取房间状态失败: {e}")
                return
            
            # 开始抓取
            self._web_fetcher.start()
            
        except Exception as e:
            self.logger.error(f"抓取过程中发生错误: {e}")
            self._update_status(FetcherStatus.ERROR, error_message=str(e))
        finally:
            if not self._stop_event.is_set():
                self._update_status(FetcherStatus.IDLE)
    
    def get_status(self) -> FetcherStatusInfo:
        """获取当前状态"""
        return self._status_info
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._status == FetcherStatus.RUNNING
    
    def get_room_info(self) -> Optional[Dict[str, Any]]:
        """获取房间信息"""
        if not self._web_fetcher:
            return None
        
        try:
            return {
                'live_id': self._current_live_id,
                'room_id': getattr(self._web_fetcher, 'room_id', None),
                'ttwid': getattr(self._web_fetcher, 'ttwid', None)
            }
        except Exception as e:
            self.logger.error(f"获取房间信息失败: {e}")
            return None


# 全局服务实例
douyin_live_fetcher_service = DouyinLiveFetcher()


if __name__ == "__main__":
    # 测试代码
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    def test_callback(message_type: str, data: Dict[str, Any]):
        print(f"收到消息 [{message_type}]: {data}")
    
    def status_callback(status_info: FetcherStatusInfo):
        print(f"状态变化: {status_info}")
    
    # 创建测试实例
    fetcher = DouyinLiveFetcher()
    fetcher.set_message_callback(test_callback)
    fetcher.set_status_change_callback(status_callback)
    
    # 测试启动（需要真实的live_id）
    test_live_id = "163823390463"  # 示例live_id
    print(f"测试启动抓取器，live_id: {test_live_id}")
    
    if fetcher.start_fetch(test_live_id):
        print("抓取器启动成功")
        try:
            # 运行一段时间
            time.sleep(30)
        except KeyboardInterrupt:
            print("用户中断")
        finally:
            print("停止抓取器")
            fetcher.stop_fetch()
    else:
        print("抓取器启动失败")
