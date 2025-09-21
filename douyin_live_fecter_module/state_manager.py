"""
DouyinLiveWebFetcher API封装 - 状态管理器

本模块实现状态管理器，负责：
- 管理直播间连接状态和会话状态
- 提供状态持久化和恢复功能
- 支持多房间状态管理
- 实现状态变更通知机制

状态管理器采用观察者模式，支持状态变更监听。
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import threading
from concurrent.futures import ThreadPoolExecutor

from .models import (
    ConnectionState, SessionState, RoomStatus, ConnectionStatus,
    StateChangeEvent, StateSnapshot
)
from .exceptions import (
    StateManagerError, DouyinAPIException, handle_exceptions
)
from .config import get_config_manager


# ================================
# 状态存储接口
# ================================

class StateStorage(ABC):
    """状态存储接口"""
    
    @abstractmethod
    async def save_state(self, room_id: str, state_data: Dict[str, Any]) -> bool:
        """保存状态数据"""
        pass
    
    @abstractmethod
    async def load_state(self, room_id: str) -> Optional[Dict[str, Any]]:
        """加载状态数据"""
        pass
    
    @abstractmethod
    async def delete_state(self, room_id: str) -> bool:
        """删除状态数据"""
        pass
    
    @abstractmethod
    async def list_states(self) -> List[str]:
        """列出所有状态的房间ID"""
        pass


# ================================
# 内存状态存储
# ================================

class MemoryStateStorage(StateStorage):
    """内存状态存储"""
    
    def __init__(self):
        self._states: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def save_state(self, room_id: str, state_data: Dict[str, Any]) -> bool:
        """保存状态到内存"""
        async with self._lock:
            self._states[room_id] = state_data.copy()
            return True
    
    async def load_state(self, room_id: str) -> Optional[Dict[str, Any]]:
        """从内存加载状态"""
        async with self._lock:
            return self._states.get(room_id, {}).copy() if room_id in self._states else None
    
    async def delete_state(self, room_id: str) -> bool:
        """从内存删除状态"""
        async with self._lock:
            if room_id in self._states:
                del self._states[room_id]
                return True
            return False
    
    async def list_states(self) -> List[str]:
        """列出所有状态的房间ID"""
        async with self._lock:
            return list(self._states.keys())


# ================================
# Redis状态存储
# ================================

class RedisStateStorage(StateStorage):
    """Redis状态存储"""
    
    def __init__(self, redis_client=None, key_prefix: str = "douyin_state"):
        self.redis_client = redis_client
        self.key_prefix = key_prefix
        self.logger = logging.getLogger(__name__)
    
    def _get_key(self, room_id: str) -> str:
        """获取Redis键名"""
        return f"{self.key_prefix}:{room_id}"
    
    async def save_state(self, room_id: str, state_data: Dict[str, Any]) -> bool:
        """保存状态到Redis"""
        if not self.redis_client:
            return False
        
        try:
            key = self._get_key(room_id)
            data = json.dumps(state_data, ensure_ascii=False, default=str)
            
            # 设置过期时间为24小时
            await self.redis_client.setex(key, 86400, data)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save state to Redis: {e}")
            return False
    
    async def load_state(self, room_id: str) -> Optional[Dict[str, Any]]:
        """从Redis加载状态"""
        if not self.redis_client:
            return None
        
        try:
            key = self._get_key(room_id)
            data = await self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to load state from Redis: {e}")
            return None
    
    async def delete_state(self, room_id: str) -> bool:
        """从Redis删除状态"""
        if not self.redis_client:
            return False
        
        try:
            key = self._get_key(room_id)
            result = await self.redis_client.delete(key)
            return result > 0
            
        except Exception as e:
            self.logger.error(f"Failed to delete state from Redis: {e}")
            return False
    
    async def list_states(self) -> List[str]:
        """列出所有状态的房间ID"""
        if not self.redis_client:
            return []
        
        try:
            pattern = f"{self.key_prefix}:*"
            keys = await self.redis_client.keys(pattern)
            
            # 提取房间ID
            room_ids = []
            prefix_len = len(self.key_prefix) + 1
            for key in keys:
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                room_ids.append(key[prefix_len:])
            
            return room_ids
            
        except Exception as e:
            self.logger.error(f"Failed to list states from Redis: {e}")
            return []


# ================================
# 状态观察者接口
# ================================

class StateObserver(ABC):
    """状态观察者接口"""
    
    @abstractmethod
    async def on_state_changed(self, event: StateChangeEvent):
        """状态变更回调"""
        pass


# ================================
# 房间状态管理器
# ================================

class RoomStateManager:
    """房间状态管理器"""
    
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.logger = logging.getLogger(f"{__name__}.{room_id}")
        
        # 状态数据
        self.connection_state = ConnectionState(status=ConnectionStatus.DISCONNECTED)
        self.session_state = SessionState(
            session_id=f"session_{room_id}",
            room_id=room_id,
            user_id="",
            start_time=datetime.now(),
            last_activity=datetime.now(),
            is_active=False
        )
        self.room_status = RoomStatus.UNKNOWN
        
        # 状态元数据
        self.connected_at: Optional[datetime] = None
        self.last_message_at: Optional[datetime] = None
        self.message_count = 0
        self.error_count = 0
        self.reconnect_count = 0
        
        # 会话信息
        self.session_id: Optional[str] = None
        self.user_count = 0
        self.room_title = ""
        self.anchor_name = ""
        
        # 性能统计
        self.stats = {
            'messages_per_second': 0.0,
            'avg_response_time': 0.0,
            'last_heartbeat': None,
            'bandwidth_usage': 0
        }
        
        # 状态锁
        self._lock = asyncio.Lock()
    
    async def update_connection_state(self, new_state: ConnectionState, metadata: Optional[Dict[str, Any]] = None):
        """更新连接状态"""
        async with self._lock:
            old_state = self.connection_state
            self.connection_state = new_state
            
            # 更新相关元数据
            if new_state.status == ConnectionStatus.CONNECTED:
                self.connected_at = datetime.now()
                self.error_count = 0
            elif new_state.status == ConnectionStatus.DISCONNECTED:
                self.connected_at = None
                self.session_id = None
            elif new_state == ConnectionState.ERROR:
                self.error_count += 1
            elif new_state == ConnectionState.RECONNECTING:
                self.reconnect_count += 1
            
            # 应用额外元数据
            if metadata:
                for key, value in metadata.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
            
            self.logger.info(f"Connection state changed: {old_state} -> {new_state}")
    
    async def update_session_state(self, new_state: SessionState, metadata: Optional[Dict[str, Any]] = None):
        """更新会话状态"""
        async with self._lock:
            old_state = self.session_state
            self.session_state = new_state
            
            # 应用元数据
            if metadata:
                for key, value in metadata.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
            
            self.logger.info(f"Session state changed: {old_state} -> {new_state}")
    
    async def update_room_status(self, new_status: RoomStatus, metadata: Optional[Dict[str, Any]] = None):
        """更新房间状态"""
        async with self._lock:
            old_status = self.room_status
            self.room_status = new_status
            
            # 应用元数据
            if metadata:
                for key, value in metadata.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
            
            self.logger.info(f"Room status changed: {old_status} -> {new_status}")
    
    async def record_message(self):
        """记录消息"""
        async with self._lock:
            self.message_count += 1
            self.last_message_at = datetime.now()
            
            # 计算消息频率
            if self.connected_at:
                duration = (datetime.now() - self.connected_at).total_seconds()
                if duration > 0:
                    self.stats['messages_per_second'] = self.message_count / duration
    
    async def record_error(self, error: Exception):
        """记录错误"""
        async with self._lock:
            self.error_count += 1
            self.logger.error(f"Error recorded: {error}")
    
    async def update_stats(self, stats: Dict[str, Any]):
        """更新统计信息"""
        async with self._lock:
            self.stats.update(stats)
    
    async def get_snapshot(self) -> StateSnapshot:
        """获取状态快照"""
        async with self._lock:
            return StateSnapshot(
                room_id=self.room_id,
                connection_state=self.connection_state,
                session_state=self.session_state,
                room_status=self.room_status,
                connected_at=self.connected_at,
                last_message_at=self.last_message_at,
                message_count=self.message_count,
                error_count=self.error_count,
                reconnect_count=self.reconnect_count,
                session_id=self.session_id,
                user_count=self.user_count,
                room_title=self.room_title,
                anchor_name=self.anchor_name,
                stats=self.stats.copy(),
                timestamp=datetime.now()
            )
    
    async def restore_from_snapshot(self, snapshot: StateSnapshot):
        """从快照恢复状态"""
        async with self._lock:
            self.connection_state = snapshot.connection_state
            self.session_state = snapshot.session_state
            self.room_status = snapshot.room_status
            self.connected_at = snapshot.connected_at
            self.last_message_at = snapshot.last_message_at
            self.message_count = snapshot.message_count
            self.error_count = snapshot.error_count
            self.reconnect_count = snapshot.reconnect_count
            self.session_id = snapshot.session_id
            self.user_count = snapshot.user_count
            self.room_title = snapshot.room_title
            self.anchor_name = snapshot.anchor_name
            self.stats = snapshot.stats.copy()
            
            self.logger.info(f"State restored from snapshot at {snapshot.timestamp}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'room_id': self.room_id,
            'connection_state': self.connection_state.value,
            'session_state': self.session_state.value,
            'room_status': self.room_status.value,
            'connected_at': self.connected_at.isoformat() if self.connected_at else None,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'message_count': self.message_count,
            'error_count': self.error_count,
            'reconnect_count': self.reconnect_count,
            'session_id': self.session_id,
            'user_count': self.user_count,
            'room_title': self.room_title,
            'anchor_name': self.anchor_name,
            'stats': self.stats
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RoomStateManager':
        """从字典创建实例"""
        room_id = data['room_id']
        manager = cls(room_id)
        
        manager.connection_state = ConnectionState(status=ConnectionStatus(data.get('connection_state', ConnectionStatus.DISCONNECTED.value)))
        manager.session_state = SessionState(
            session_id=data.get('session_id', f"session_{room_id}"),
            room_id=room_id,
            user_id=data.get('user_id', ""),
            start_time=datetime.fromisoformat(data.get('start_time', datetime.now().isoformat())),
            last_activity=datetime.fromisoformat(data.get('last_activity', datetime.now().isoformat())),
            is_active=data.get('is_active', False)
        )
        manager.room_status = RoomStatus(data.get('room_status', RoomStatus.UNKNOWN.value))
        
        # 解析时间字段
        if data.get('connected_at'):
            manager.connected_at = datetime.fromisoformat(data['connected_at'])
        if data.get('last_message_at'):
            manager.last_message_at = datetime.fromisoformat(data['last_message_at'])
        
        # 设置其他字段
        manager.message_count = data.get('message_count', 0)
        manager.error_count = data.get('error_count', 0)
        manager.reconnect_count = data.get('reconnect_count', 0)
        manager.session_id = data.get('session_id')
        manager.user_count = data.get('user_count', 0)
        manager.room_title = data.get('room_title', '')
        manager.anchor_name = data.get('anchor_name', '')
        manager.stats = data.get('stats', {})
        
        return manager


# ================================
# 全局状态管理器
# ================================

class GlobalStateManager:
    """全局状态管理器"""
    
    def __init__(self, storage: Optional[StateStorage] = None):
        self.logger = logging.getLogger(__name__)
        
        # 状态存储
        self.storage = storage or MemoryStateStorage()
        
        # 房间状态管理器
        self.room_managers: Dict[str, RoomStateManager] = {}
        
        # 观察者列表
        self.observers: List[StateObserver] = []
        
        # 全局锁
        self._lock = asyncio.Lock()
        
        # 后台任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._save_task: Optional[asyncio.Task] = None
        
        # 配置
        self.config = get_config_manager()
        
        # 启动后台任务
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """启动后台任务"""
        # 定期清理过期状态
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_states())
        
        # 定期保存状态
        self._save_task = asyncio.create_task(self._periodic_save())
    
    async def _cleanup_expired_states(self):
        """清理过期状态"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次
                
                current_time = datetime.now()
                expired_rooms = []
                
                async with self._lock:
                    for room_id, manager in self.room_managers.items():
                        # 检查是否长时间无活动
                        if (manager.last_message_at and 
                            current_time - manager.last_message_at > timedelta(hours=1)):
                            expired_rooms.append(room_id)
                
                # 清理过期房间
                for room_id in expired_rooms:
                    await self.remove_room(room_id)
                    self.logger.info(f"Cleaned up expired room: {room_id}")
                
            except Exception as e:
                self.logger.error(f"Cleanup task error: {e}")
    
    async def _periodic_save(self):
        """定期保存状态"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟保存一次
                await self.save_all_states()
                
            except Exception as e:
                self.logger.error(f"Periodic save error: {e}")
    
    async def get_room_manager(self, room_id: str) -> RoomStateManager:
        """获取房间状态管理器"""
        async with self._lock:
            if room_id not in self.room_managers:
                # 尝试从存储加载状态
                state_data = await self.storage.load_state(room_id)
                
                if state_data:
                    manager = RoomStateManager.from_dict(state_data)
                    self.logger.info(f"Restored room state from storage: {room_id}")
                else:
                    manager = RoomStateManager(room_id)
                    self.logger.info(f"Created new room state manager: {room_id}")
                
                self.room_managers[room_id] = manager
            
            return self.room_managers[room_id]
    
    async def remove_room(self, room_id: str) -> bool:
        """移除房间状态管理器"""
        async with self._lock:
            if room_id in self.room_managers:
                # 保存最终状态
                manager = self.room_managers[room_id]
                await self.storage.save_state(room_id, manager.to_dict())
                
                # 移除管理器
                del self.room_managers[room_id]
                
                # 通知观察者
                event = StateChangeEvent(
                    event_id=f"room_removed_{room_id}_{datetime.now().timestamp()}",
                    event_type="room_removed",
                    old_state=None,
                    new_state=None,
                    timestamp=datetime.now(),
                    context={'room_id': room_id, 'removed_at': datetime.now()}
                )
                await self._notify_observers(event)
                
                self.logger.info(f"Removed room state manager: {room_id}")
                return True
            
            return False
    
    async def add_observer(self, observer: StateObserver):
        """添加状态观察者"""
        self.observers.append(observer)
        self.logger.info(f"Added state observer: {observer.__class__.__name__}")
    
    async def remove_observer(self, observer: StateObserver):
        """移除状态观察者"""
        if observer in self.observers:
            self.observers.remove(observer)
            self.logger.info(f"Removed state observer: {observer.__class__.__name__}")
    
    async def _notify_observers(self, event: StateChangeEvent):
        """通知观察者"""
        for observer in self.observers:
            try:
                await observer.on_state_changed(event)
            except Exception as e:
                self.logger.error(f"Observer notification error: {e}")
    
    async def update_room_connection_state(self, room_id: str, new_state: ConnectionState, 
                                         metadata: Optional[Dict[str, Any]] = None):
        """更新房间连接状态"""
        manager = await self.get_room_manager(room_id)
        old_state = manager.connection_state
        
        await manager.update_connection_state(new_state, metadata)
        
        # 通知观察者
        event = StateChangeEvent(
            event_id=f"connection_state_changed_{room_id}_{datetime.now().timestamp()}",
            event_type="connection_state_changed",
            old_state=str(old_state.status) if old_state else None,
            new_state=str(new_state.status),
            timestamp=datetime.now(),
            context={'room_id': room_id, **(metadata or {})}
        )
        await self._notify_observers(event)
    
    async def update_room_session_state(self, room_id: str, new_state: SessionState,
                                      metadata: Optional[Dict[str, Any]] = None):
        """更新房间会话状态"""
        manager = await self.get_room_manager(room_id)
        old_state = manager.session_state
        
        await manager.update_session_state(new_state, metadata)
        
        # 通知观察者
        event = StateChangeEvent(
            event_id=f"session_state_changed_{room_id}_{datetime.now().timestamp()}",
            event_type="session_state_changed",
            old_state=str(old_state.session_id) if old_state else None,
            new_state=str(new_state.session_id),
            timestamp=datetime.now(),
            context={'room_id': room_id, **(metadata or {})}
        )
        await self._notify_observers(event)
    
    async def update_room_status(self, room_id: str, new_status: RoomStatus,
                               metadata: Optional[Dict[str, Any]] = None):
        """更新房间状态"""
        manager = await self.get_room_manager(room_id)
        old_status = manager.room_status
        
        await manager.update_room_status(new_status, metadata)
        
        # 通知观察者
        event = StateChangeEvent(
            event_id=f"room_status_changed_{room_id}_{datetime.now().timestamp()}",
            event_type="room_status_changed",
            old_state=str(old_status.value) if old_status else None,
            new_state=str(new_status.value),
            timestamp=datetime.now(),
            context={'room_id': room_id, **(metadata or {})}
        )
        await self._notify_observers(event)
    
    async def record_message(self, room_id: str):
        """记录消息"""
        manager = await self.get_room_manager(room_id)
        await manager.record_message()
    
    async def record_error(self, room_id: str, error: Exception):
        """记录错误"""
        manager = await self.get_room_manager(room_id)
        await manager.record_error(error)
    
    async def get_room_snapshot(self, room_id: str) -> Optional[StateSnapshot]:
        """获取房间状态快照"""
        if room_id in self.room_managers:
            manager = self.room_managers[room_id]
            return await manager.get_snapshot()
        return None
    
    async def get_all_snapshots(self) -> Dict[str, StateSnapshot]:
        """获取所有房间状态快照"""
        snapshots = {}
        
        async with self._lock:
            for room_id, manager in self.room_managers.items():
                snapshots[room_id] = await manager.get_snapshot()
        
        return snapshots
    
    async def save_all_states(self):
        """保存所有状态"""
        async with self._lock:
            for room_id, manager in self.room_managers.items():
                try:
                    await self.storage.save_state(room_id, manager.to_dict())
                except Exception as e:
                    self.logger.error(f"Failed to save state for room {room_id}: {e}")
    
    async def load_all_states(self):
        """加载所有状态"""
        try:
            room_ids = await self.storage.list_states()
            
            for room_id in room_ids:
                state_data = await self.storage.load_state(room_id)
                if state_data:
                    manager = RoomStateManager.from_dict(state_data)
                    async with self._lock:
                        self.room_managers[room_id] = manager
                    
                    self.logger.info(f"Loaded state for room: {room_id}")
            
            self.logger.info(f"Loaded {len(room_ids)} room states")
            
        except Exception as e:
            self.logger.error(f"Failed to load states: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            'total_rooms': len(self.room_managers),
            'connected_rooms': 0,
            'active_rooms': 0,
            'total_messages': 0,
            'total_errors': 0,
            'rooms': {}
        }
        
        async with self._lock:
            for room_id, manager in self.room_managers.items():
                snapshot = await manager.get_snapshot()
                
                if snapshot.connection_state.status == ConnectionStatus.CONNECTED:
                    stats['connected_rooms'] += 1
                
                if snapshot.last_message_at and \
                   datetime.now() - snapshot.last_message_at < timedelta(minutes=5):
                    stats['active_rooms'] += 1
                
                stats['total_messages'] += snapshot.message_count
                stats['total_errors'] += snapshot.error_count
                
                stats['rooms'][room_id] = {
                    'connection_state': snapshot.connection_state.value,
                    'session_state': snapshot.session_state.value,
                    'room_status': snapshot.room_status.value,
                    'message_count': snapshot.message_count,
                    'error_count': snapshot.error_count,
                    'user_count': snapshot.user_count,
                    'messages_per_second': snapshot.stats.get('messages_per_second', 0)
                }
        
        return stats
    
    async def cleanup(self):
        """清理资源"""
        # 取消后台任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._save_task:
            self._save_task.cancel()
        
        # 保存所有状态
        await self.save_all_states()
        
        self.logger.info("Global state manager cleaned up")


# ================================
# 全局状态管理器实例
# ================================

# 创建全局状态管理器实例
_state_manager: Optional[GlobalStateManager] = None


def get_state_manager() -> GlobalStateManager:
    """获取全局状态管理器实例"""
    global _state_manager
    
    if _state_manager is None:
        _state_manager = GlobalStateManager()
    
    return _state_manager


async def initialize_state_manager(storage: Optional[StateStorage] = None):
    """初始化状态管理器"""
    global _state_manager
    
    _state_manager = GlobalStateManager(storage)
    await _state_manager.load_all_states()
    
    return _state_manager


def init_state_manager(storage: Optional[StateStorage] = None) -> GlobalStateManager:
    """
    同步初始化状态管理器（兼容性函数）
    注意：这是一个同步函数，实际初始化需要异步调用
    """
    global _state_manager
    
    if _state_manager is None:
        _state_manager = GlobalStateManager(storage)
    
    return _state_manager