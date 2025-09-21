"""
DouyinLiveWebFetcher API封装 - 异步API接口层

本模块实现DouyinLiveAPI类，提供：
- 统一的异步API接口
- 消息订阅和处理机制
- 连接管理和状态监控
- 错误处理和重连机制

API采用异步设计，支持多房间并发监控。
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List, Callable, AsyncGenerator, Union
from datetime import datetime, timedelta
import weakref
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod

from .models import (
    BaseMessage, MessageType, ConnectionState, SessionState, 
    RoomStatus, APIResponse, StateSnapshot, ConnectionStatus
)
from .adapters import get_adapter_manager, MessageAdapterManager
from .state_manager import get_state_manager, GlobalStateManager
from .exceptions import (
    DouyinAPIException, ConnectionError, MessageParseError,
    ConfigurationError, handle_exceptions
)
from .config import get_config_manager


# ================================
# 消息处理器接口
# ================================

class MessageHandler(ABC):
    """消息处理器接口"""
    
    @abstractmethod
    async def handle_message(self, message: BaseMessage) -> bool:
        """
        处理消息
        
        Args:
            message: 消息对象
            
        Returns:
            bool: 是否继续处理后续处理器
        """
        pass


# ================================
# 连接管理器
# ================================

class ConnectionManager:
    """连接管理器"""
    
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.logger = logging.getLogger(f"{__name__}.{room_id}")
        
        # 连接状态
        self._connection = None
        self._is_connected = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 5.0
        
        # 心跳机制
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._heartbeat_interval = 30.0
        self._last_heartbeat = None
        
        # 配置
        self.config = get_config_manager()
        self.state_manager = get_state_manager()
    
    async def connect(self) -> bool:
        """建立连接"""
        try:
            await self.state_manager.update_room_connection_state(
                self.room_id, ConnectionState.CONNECTING
            )
            
            # 这里应该实现实际的DouyinLiveWebFetcher连接逻辑
            # 由于我们没有实际的连接实现，这里模拟连接过程
            await asyncio.sleep(1)  # 模拟连接延迟
            
            self._is_connected = True
            self._reconnect_attempts = 0
            
            # 启动心跳
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            await self.state_manager.update_room_connection_state(
                self.room_id, ConnectionState(status=ConnectionStatus.CONNECTED),
                {'connected_at': datetime.now()}
            )
            
            self.logger.info(f"Connected to room: {self.room_id}")
            return True
            
        except Exception as e:
            await self.state_manager.update_room_connection_state(
                self.room_id, ConnectionState.ERROR
            )
            await self.state_manager.record_error(self.room_id, e)
            
            self.logger.error(f"Failed to connect to room {self.room_id}: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        try:
            self._is_connected = False
            
            # 停止心跳
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                self._heartbeat_task = None
            
            # 关闭连接
            if self._connection:
                # 这里应该实现实际的连接关闭逻辑
                self._connection = None
            
            await self.state_manager.update_room_connection_state(
                self.room_id, ConnectionState(status=ConnectionStatus.DISCONNECTED)
            )
            
            self.logger.info(f"Disconnected from room: {self.room_id}")
            
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
    
    async def reconnect(self) -> bool:
        """重连"""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            self.logger.error(f"Max reconnect attempts reached for room: {self.room_id}")
            return False
        
        self._reconnect_attempts += 1
        
        await self.state_manager.update_room_connection_state(
            self.room_id, ConnectionState.RECONNECTING,
            {'reconnect_attempt': self._reconnect_attempts}
        )
        
        self.logger.info(f"Reconnecting to room {self.room_id} (attempt {self._reconnect_attempts})")
        
        # 等待重连延迟
        await asyncio.sleep(self._reconnect_delay * self._reconnect_attempts)
        
        return await self.connect()
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._is_connected:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                
                # 发送心跳
                await self._send_heartbeat()
                self._last_heartbeat = datetime.now()
                
                # 更新统计信息
                await self.state_manager.get_room_manager(self.room_id).then(
                    lambda manager: manager.update_stats({
                        'last_heartbeat': self._last_heartbeat
                    })
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat error: {e}")
                # 心跳失败可能表示连接问题，尝试重连
                if self._is_connected:
                    asyncio.create_task(self.reconnect())
                break
    
    async def _send_heartbeat(self):
        """发送心跳"""
        # 这里应该实现实际的心跳发送逻辑
        # 由于我们没有实际的连接实现，这里只是记录日志
        self.logger.debug(f"Heartbeat sent to room: {self.room_id}")
    
    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self._is_connected
    
    @property
    def reconnect_attempts(self) -> int:
        """重连尝试次数"""
        return self._reconnect_attempts


# ================================
# 消息流管理器
# ================================

class MessageStreamManager:
    """消息流管理器"""
    
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.logger = logging.getLogger(f"{__name__}.{room_id}")
        
        # 消息队列
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._message_handlers: List[MessageHandler] = []
        
        # 消息处理任务
        self._processing_task: Optional[asyncio.Task] = None
        self._is_processing = False
        
        # 消息统计
        self._message_count = 0
        self._last_message_time = None
        
        # 组件依赖
        self.adapter_manager = get_adapter_manager()
        self.state_manager = get_state_manager()
    
    def add_handler(self, handler: MessageHandler):
        """添加消息处理器"""
        self._message_handlers.append(handler)
        self.logger.info(f"Added message handler: {handler.__class__.__name__}")
    
    def remove_handler(self, handler: MessageHandler):
        """移除消息处理器"""
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)
            self.logger.info(f"Removed message handler: {handler.__class__.__name__}")
    
    async def start_processing(self):
        """开始消息处理"""
        if self._is_processing:
            return
        
        self._is_processing = True
        self._processing_task = asyncio.create_task(self._process_messages())
        
        self.logger.info(f"Started message processing for room: {self.room_id}")
    
    async def stop_processing(self):
        """停止消息处理"""
        self._is_processing = False
        
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            self._processing_task = None
        
        self.logger.info(f"Stopped message processing for room: {self.room_id}")
    
    async def _process_messages(self):
        """处理消息循环"""
        while self._is_processing:
            try:
                # 等待消息
                message = await self._message_queue.get()
                
                # 更新统计
                self._message_count += 1
                self._last_message_time = datetime.now()
                
                # 记录消息到状态管理器
                await self.state_manager.record_message(self.room_id)
                
                # 处理消息
                await self._handle_message(message)
                
                # 标记任务完成
                self._message_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Message processing error: {e}")
                await self.state_manager.record_error(self.room_id, e)
    
    async def _handle_message(self, message: BaseMessage):
        """处理单个消息"""
        for handler in self._message_handlers:
            try:
                # 调用处理器
                should_continue = await handler.handle_message(message)
                
                # 如果处理器返回False，停止后续处理
                if not should_continue:
                    break
                    
            except Exception as e:
                self.logger.error(f"Handler {handler.__class__.__name__} error: {e}")
                continue
    
    async def put_raw_message(self, raw_data: Dict[str, Any]):
        """放入原始消息"""
        try:
            # 适配消息
            message = self.adapter_manager.adapt_message(raw_data, self.room_id)
            
            if message:
                await self._message_queue.put(message)
            else:
                self.logger.warning("Failed to adapt message")
                
        except Exception as e:
            self.logger.error(f"Failed to put raw message: {e}")
            await self.state_manager.record_error(self.room_id, e)
    
    async def put_message(self, message: BaseMessage):
        """放入已适配的消息"""
        await self._message_queue.put(message)
    
    async def process_message(self, message: BaseMessage):
        """处理单个消息（公共接口）"""
        await self._handle_message(message)
    
    @property
    def message_count(self) -> int:
        """消息计数"""
        return self._message_count
    
    @property
    def queue_size(self) -> int:
        """队列大小"""
        return self._message_queue.qsize()


# ================================
# DouyinLiveAPI主类
# ================================

class DouyinLiveAPI:
    """抖音直播API封装"""
    
    def __init__(self, room_id: str):
        """
        初始化API实例
        
        Args:
            room_id: 直播间ID
        """
        self.room_id = str(room_id)
        self.logger = logging.getLogger(f"{__name__}.{self.room_id}")
        
        # 组件管理器
        self.connection_manager = ConnectionManager(self.room_id)
        self.message_stream = MessageStreamManager(self.room_id)
        
        # 依赖组件
        self.config = get_config_manager()
        self.state_manager = get_state_manager()
        self.adapter_manager = get_adapter_manager()
        
        # 回调函数
        self._message_callbacks: List[Callable[[BaseMessage], None]] = []
        self._state_callbacks: List[Callable[[str, Any], None]] = []
        
        # 运行状态
        self._is_running = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    # ================================
    # 连接管理
    # ================================
    
    @handle_exceptions(reraise=True)
    async def connect(self) -> APIResponse:
        """
        连接到直播间
        
        Returns:
            APIResponse: 连接结果
        """
        try:
            success = await self.connection_manager.connect()
            
            if success:
                # 启动消息处理
                await self.message_stream.start_processing()
                
                return APIResponse(
                    success=True,
                    message="Connected successfully",
                    data={'room_id': self.room_id, 'connected_at': datetime.now()}
                )
            else:
                return APIResponse(
                    success=False,
                    message="Failed to connect",
                    error_code="CONNECTION_FAILED"
                )
                
        except Exception as e:
            self.logger.error(f"Connect error: {e}")
            return APIResponse(
                success=False,
                message=str(e),
                error_code="CONNECTION_ERROR"
            )
    
    @handle_exceptions(reraise=True)
    async def disconnect(self) -> APIResponse:
        """
        断开连接
        
        Returns:
            APIResponse: 断开结果
        """
        try:
            # 停止监控
            await self.stop_monitoring()
            
            # 停止消息处理
            await self.message_stream.stop_processing()
            
            # 断开连接
            await self.connection_manager.disconnect()
            
            return APIResponse(
                success=True,
                message="Disconnected successfully",
                data={'room_id': self.room_id, 'disconnected_at': datetime.now()}
            )
            
        except Exception as e:
            self.logger.error(f"Disconnect error: {e}")
            return APIResponse(
                success=False,
                message=str(e),
                error_code="DISCONNECT_ERROR"
            )
    
    @handle_exceptions(reraise=True)
    async def reconnect(self) -> APIResponse:
        """
        重新连接
        
        Returns:
            APIResponse: 重连结果
        """
        try:
            success = await self.connection_manager.reconnect()
            
            if success:
                return APIResponse(
                    success=True,
                    message="Reconnected successfully",
                    data={'room_id': self.room_id, 'reconnected_at': datetime.now()}
                )
            else:
                return APIResponse(
                    success=False,
                    message="Failed to reconnect",
                    error_code="RECONNECT_FAILED"
                )
                
        except Exception as e:
            self.logger.error(f"Reconnect error: {e}")
            return APIResponse(
                success=False,
                message=str(e),
                error_code="RECONNECT_ERROR"
            )
    
    # ================================
    # 消息监控
    # ================================
    
    async def start_monitoring(self) -> APIResponse:
        """
        开始监控消息
        
        Returns:
            APIResponse: 启动结果
        """
        if self._is_running:
            return APIResponse(
                success=False,
                message="Already monitoring",
                error_code="ALREADY_RUNNING"
            )
        
        try:
            # 确保已连接
            if not self.connection_manager.is_connected:
                connect_result = await self.connect()
                if not connect_result.success:
                    return connect_result
            
            self._is_running = True
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            
            await self.state_manager.update_room_session_state(
                self.room_id, SessionState(
                    session_id=f"session_{self.room_id}",
                    room_id=self.room_id,
                    user_id="",
                    start_time=datetime.now(),
                    last_activity=datetime.now(),
                    is_active=True
                )
            )
            
            self.logger.info(f"Started monitoring room: {self.room_id}")
            
            return APIResponse(
                success=True,
                message="Monitoring started",
                data={'room_id': self.room_id, 'started_at': datetime.now()}
            )
            
        except Exception as e:
            self.logger.error(f"Start monitoring error: {e}")
            return APIResponse(
                success=False,
                message=str(e),
                error_code="START_MONITORING_ERROR"
            )
    
    async def stop_monitoring(self) -> APIResponse:
        """
        停止监控消息
        
        Returns:
            APIResponse: 停止结果
        """
        if not self._is_running:
            return APIResponse(
                success=False,
                message="Not monitoring",
                error_code="NOT_RUNNING"
            )
        
        try:
            self._is_running = False
            
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
                self._monitor_task = None
            
            await self.state_manager.update_room_session_state(
                self.room_id, SessionState(
                    session_id=f"session_{self.room_id}",
                    room_id=self.room_id,
                    user_id="",
                    start_time=datetime.now(),
                    last_activity=datetime.now(),
                    is_active=False
                )
            )
            
            self.logger.info(f"Stopped monitoring room: {self.room_id}")
            
            return APIResponse(
                success=True,
                message="Monitoring stopped",
                data={'room_id': self.room_id, 'stopped_at': datetime.now()}
            )
            
        except Exception as e:
            self.logger.error(f"Stop monitoring error: {e}")
            return APIResponse(
                success=False,
                message=str(e),
                error_code="STOP_MONITORING_ERROR"
            )
    
    async def _monitor_loop(self):
        """监控循环"""
        while self._is_running:
            try:
                # 这里应该实现实际的消息获取逻辑
                # 由于我们没有实际的DouyinLiveWebFetcher实现，这里模拟消息接收
                await asyncio.sleep(1)
                
                # 模拟接收到消息
                if self._is_running:
                    await self._simulate_message_reception()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")
                await self.state_manager.record_error(self.room_id, e)
                
                # 如果连接断开，尝试重连
                if not self.connection_manager.is_connected:
                    await self.connection_manager.reconnect()
    
    async def _simulate_message_reception(self):
        """模拟消息接收（用于测试）"""
        # 这是一个模拟函数，实际实现中应该从DouyinLiveWebFetcher接收真实消息
        import random
        
        message_types = ['chat', 'gift', 'like', 'member']
        message_type = random.choice(message_types)
        
        raw_message = {
            'type': message_type,
            'user': {
                'id': f'user_{random.randint(1000, 9999)}',
                'nickname': f'用户{random.randint(1, 100)}',
                'level': random.randint(1, 50)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        if message_type == 'chat':
            raw_message['content'] = f'测试消息 {random.randint(1, 1000)}'
        elif message_type == 'gift':
            raw_message['gift'] = {
                'id': f'gift_{random.randint(1, 10)}',
                'name': f'礼物{random.randint(1, 10)}',
                'count': random.randint(1, 5),
                'price': random.randint(1, 100)
            }
        elif message_type == 'like':
            raw_message['count'] = random.randint(1, 10)
        
        # 放入消息流
        await self.message_stream.put_raw_message(raw_message)
    
    # ================================
    # 消息处理
    # ================================
    
    def add_message_handler(self, handler: MessageHandler):
        """
        添加消息处理器
        
        Args:
            handler: 消息处理器
        """
        self.message_stream.add_handler(handler)
    
    def remove_message_handler(self, handler: MessageHandler):
        """
        移除消息处理器
        
        Args:
            handler: 消息处理器
        """
        self.message_stream.remove_handler(handler)
    
    def add_message_callback(self, callback: Callable[[BaseMessage], None]):
        """
        添加消息回调函数
        
        Args:
            callback: 回调函数
        """
        self._message_callbacks.append(callback)
        
        # 创建处理器包装器
        class CallbackHandler(MessageHandler):
            def __init__(self, cb):
                self.callback = cb
            
            async def handle_message(self, message: BaseMessage) -> bool:
                try:
                    if asyncio.iscoroutinefunction(self.callback):
                        await self.callback(message)
                    else:
                        self.callback(message)
                except Exception as e:
                    logging.getLogger(__name__).error(f"Callback error: {e}")
                return True
        
        self.add_message_handler(CallbackHandler(callback))
    
    # ================================
    # 状态查询
    # ================================
    
    async def get_connection_state(self) -> ConnectionState:
        """获取连接状态"""
        snapshot = await self.state_manager.get_room_snapshot(self.room_id)
        return snapshot.connection_state if snapshot else ConnectionState(status=ConnectionStatus.DISCONNECTED)
    
    async def get_session_state(self) -> SessionState:
        """获取会话状态"""
        snapshot = await self.state_manager.get_room_snapshot(self.room_id)
        return snapshot.session_state if snapshot else SessionState(
            session_id=f"session_{self.room_id}",
            room_id=self.room_id,
            user_id="",
            start_time=datetime.now(),
            last_activity=datetime.now(),
            is_active=False
        )
    
    async def get_room_status(self) -> RoomStatus:
        """获取房间状态"""
        snapshot = await self.state_manager.get_room_snapshot(self.room_id)
        return snapshot.room_status if snapshot else RoomStatus.UNKNOWN
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        snapshot = await self.state_manager.get_room_snapshot(self.room_id)
        
        if not snapshot:
            return {}
        
        return {
            'room_id': self.room_id,
            'connection_state': snapshot.connection_state.value,
            'session_state': snapshot.session_state.value,
            'room_status': snapshot.room_status.value,
            'message_count': snapshot.message_count,
            'error_count': snapshot.error_count,
            'reconnect_count': snapshot.reconnect_count,
            'user_count': snapshot.user_count,
            'connected_at': snapshot.connected_at.isoformat() if snapshot.connected_at else None,
            'last_message_at': snapshot.last_message_at.isoformat() if snapshot.last_message_at else None,
            'queue_size': self.message_stream.queue_size,
            'stats': snapshot.stats
        }
    
    # ================================
    # 消息流接口
    # ================================
    
    async def get_messages(self, limit: int = 100, 
                          message_types: Optional[List[MessageType]] = None) -> List[BaseMessage]:
        """
        获取消息列表（这里应该从缓存或数据库获取）
        
        Args:
            limit: 消息数量限制
            message_types: 消息类型过滤
            
        Returns:
            List[BaseMessage]: 消息列表
        """
        # 这里应该实现从缓存或数据库获取消息的逻辑
        # 目前返回空列表
        return []
    
    @asynccontextmanager
    async def message_stream_context(self):
        """消息流上下文管理器"""
        try:
            await self.start_monitoring()
            yield self
        finally:
            await self.stop_monitoring()
    
    # ================================
    # 生命周期管理
    # ================================
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.disconnect()
    
    @property
    def is_connected(self) -> bool:
        """是否已连接"""
        return self.connection_manager.is_connected
    
    @property
    def is_monitoring(self) -> bool:
        """是否正在监控"""
        return self._is_running


# ================================
# API工厂类
# ================================

class DouyinLiveAPIFactory:
    """DouyinLiveAPI工厂类"""
    
    _instances: Dict[str, DouyinLiveAPI] = {}
    _lock = asyncio.Lock()
    
    @classmethod
    async def get_api(cls, room_id: str) -> DouyinLiveAPI:
        """
        获取API实例（单例模式）
        
        Args:
            room_id: 直播间ID
            
        Returns:
            DouyinLiveAPI: API实例
        """
        room_id = str(room_id)
        
        async with cls._lock:
            if room_id not in cls._instances:
                cls._instances[room_id] = DouyinLiveAPI(room_id)
            
            return cls._instances[room_id]
    
    @classmethod
    async def remove_api(cls, room_id: str) -> bool:
        """
        移除API实例
        
        Args:
            room_id: 直播间ID
            
        Returns:
            bool: 是否成功移除
        """
        room_id = str(room_id)
        
        async with cls._lock:
            if room_id in cls._instances:
                api = cls._instances[room_id]
                
                # 确保断开连接
                if api.is_connected:
                    await api.disconnect()
                
                del cls._instances[room_id]
                return True
            
            return False
    
    @classmethod
    async def get_all_apis(cls) -> Dict[str, DouyinLiveAPI]:
        """获取所有API实例"""
        async with cls._lock:
            return cls._instances.copy()
    
    @classmethod
    async def cleanup_all(cls):
        """清理所有API实例"""
        async with cls._lock:
            for api in cls._instances.values():
                try:
                    if api.is_connected:
                        await api.disconnect()
                except Exception as e:
                    logging.getLogger(__name__).error(f"Cleanup error: {e}")
            
            cls._instances.clear()


# ================================
# 便捷函数
# ================================

async def create_api(room_id: str) -> DouyinLiveAPI:
    """
    创建API实例
    
    Args:
        room_id: 直播间ID
        
    Returns:
        DouyinLiveAPI: API实例
    """
    return await DouyinLiveAPIFactory.get_api(room_id)


async def connect_to_room(room_id: str) -> DouyinLiveAPI:
    """
    连接到直播间
    
    Args:
        room_id: 直播间ID
        
    Returns:
        DouyinLiveAPI: 已连接的API实例
    """
    api = await create_api(room_id)
    await api.connect()
    return api


# ================================
# API工厂类（兼容性别名）
# ================================

class APIFactory:
    """API工厂类，提供统一的API创建接口"""
    
    @staticmethod
    async def create_api(room_id: str) -> DouyinLiveAPI:
        """
        创建API实例
        
        Args:
            room_id: 直播间ID
            
        Returns:
            DouyinLiveAPI: API实例
        """
        return await DouyinLiveAPIFactory.get_api(room_id)
    
    @staticmethod
    async def create_connection_manager(room_id: str = "default") -> ConnectionManager:
        """
        创建连接管理器
        
        Args:
            room_id: 房间ID，默认为"default"
            
        Returns:
            ConnectionManager: 连接管理器实例
        """
        return ConnectionManager(room_id)
    
    @staticmethod
    async def create_message_stream_manager(room_id: str = "default") -> MessageStreamManager:
        """
        创建消息流管理器
        
        Args:
            room_id: 房间ID，默认为"default"
            
        Returns:
            MessageStreamManager: 消息流管理器实例
        """
        return MessageStreamManager(room_id)


# ================================
# 便捷创建函数
# ================================

async def create_connection_manager(room_id: str = "default") -> ConnectionManager:
    """创建连接管理器"""
    return ConnectionManager(room_id)


async def create_message_stream_manager(room_id: str = "default") -> MessageStreamManager:
    """创建消息流管理器"""
    return MessageStreamManager(room_id)