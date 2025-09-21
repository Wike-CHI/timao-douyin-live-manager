"""
DouyinLiveWebFetcher API封装 - 缓存管理器

本模块实现多层缓存策略：
- L1缓存：内存缓存（最快访问）
- L2缓存：Redis缓存（持久化）
- 缓存预热和失效策略
- 缓存统计和监控

支持消息缓存、状态缓存、用户信息缓存等多种数据类型。
"""

import logging
import asyncio
import json
import pickle
import hashlib
from typing import Dict, Any, Optional, List, Union, Callable, TypeVar, Generic
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import weakref

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from .models import BaseMessage, MessageType
from .config import get_config_manager
from .exceptions import CacheError, handle_exceptions


T = TypeVar('T')


# ================================
# 缓存配置
# ================================

@dataclass
class CacheConfig:
    """缓存配置"""
    
    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_ssl: bool = False
    
    # 连接池配置
    max_connections: int = 10
    connection_timeout: int = 5
    socket_timeout: int = 5
    
    # 缓存策略
    default_ttl: int = 3600  # 默认过期时间（秒）
    max_memory_cache_size: int = 1000  # 内存缓存最大条目数
    
    # 消息缓存配置
    message_cache_ttl: int = 1800  # 消息缓存30分钟
    message_cache_max_size: int = 10000  # 最大消息数
    
    # 状态缓存配置
    state_cache_ttl: int = 300  # 状态缓存5分钟
    
    # 用户缓存配置
    user_cache_ttl: int = 7200  # 用户信息缓存2小时
    
    # 统计缓存配置
    stats_cache_ttl: int = 60  # 统计信息缓存1分钟
    
    # 缓存键前缀
    key_prefix: str = "douyin_live"
    
    # 序列化配置
    use_compression: bool = True
    compression_threshold: int = 1024  # 超过1KB启用压缩


# ================================
# 缓存接口
# ================================

class CacheBackend(ABC):
    """缓存后端接口"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[bytes]:
        """获取缓存值"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: bytes, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass
    
    @abstractmethod
    async def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        pass
    
    @abstractmethod
    async def clear(self, pattern: Optional[str] = None) -> int:
        """清空缓存"""
        pass
    
    @abstractmethod
    async def keys(self, pattern: str) -> List[str]:
        """获取匹配的键列表"""
        pass


# ================================
# 内存缓存后端
# ================================

@dataclass
class CacheEntry:
    """缓存条目"""
    value: bytes
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_access: Optional[datetime] = None


class MemoryCacheBackend(CacheBackend):
    """内存缓存后端"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger(f"{__name__}.MemoryCache")
        
        # 统计信息
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    async def get(self, key: str) -> Optional[bytes]:
        """获取缓存值"""
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            # 检查是否过期
            if entry.expires_at and datetime.now() > entry.expires_at:
                del self._cache[key]
                self._misses += 1
                return None
            
            # 更新访问统计
            entry.access_count += 1
            entry.last_access = datetime.now()
            self._hits += 1
            
            return entry.value
    
    async def set(self, key: str, value: bytes, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        async with self._lock:
            # 检查容量限制
            if len(self._cache) >= self.max_size and key not in self._cache:
                await self._evict_lru()
            
            # 计算过期时间
            expires_at = None
            if ttl is not None:
                expires_at = datetime.now() + timedelta(seconds=ttl)
            
            # 创建缓存条目
            entry = CacheEntry(
                value=value,
                created_at=datetime.now(),
                expires_at=expires_at
            )
            
            self._cache[key] = entry
            return True
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                return False
            
            # 检查是否过期
            if entry.expires_at and datetime.now() > entry.expires_at:
                del self._cache[key]
                return False
            
            return True
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                return False
            
            entry.expires_at = datetime.now() + timedelta(seconds=ttl)
            return True
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """清空缓存"""
        async with self._lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                return count
            
            # 简单的模式匹配（只支持*通配符）
            import fnmatch
            keys_to_delete = [
                key for key in self._cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]
            
            for key in keys_to_delete:
                del self._cache[key]
            
            return len(keys_to_delete)
    
    async def keys(self, pattern: str) -> List[str]:
        """获取匹配的键列表"""
        async with self._lock:
            import fnmatch
            return [
                key for key in self._cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]
    
    async def _evict_lru(self):
        """LRU淘汰策略"""
        if not self._cache:
            return
        
        # 找到最少使用的条目
        lru_key = min(
            self._cache.keys(),
            key=lambda k: (
                self._cache[k].last_access or self._cache[k].created_at,
                self._cache[k].access_count
            )
        )
        
        del self._cache[lru_key]
        self._evictions += 1
        
        self.logger.debug(f"Evicted LRU key: {lru_key}")
    
    async def cleanup_expired(self):
        """清理过期条目"""
        async with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.expires_at and now > entry.expires_at
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                self.logger.debug(f"Cleaned up {len(expired_keys)} expired entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hits': self._hits,
            'misses': self._misses,
            'evictions': self._evictions,
            'hit_rate': self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0
        }


# ================================
# Redis缓存后端
# ================================

class RedisCacheBackend(CacheBackend):
    """Redis缓存后端"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.RedisCache")
        
        self._pool: Optional[redis.ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        
        # 统计信息
        self._hits = 0
        self._misses = 0
        self._errors = 0
    
    async def connect(self):
        """连接到Redis"""
        if not REDIS_AVAILABLE:
            raise CacheError("Redis not available. Please install redis package.")
        
        try:
            # 创建连接池
            self._pool = redis.ConnectionPool(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                ssl=self.config.redis_ssl,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.connection_timeout,
                decode_responses=False  # 我们处理bytes
            )
            
            # 创建客户端
            self._client = redis.Redis(connection_pool=self._pool)
            
            # 测试连接
            await self._client.ping()
            
            self.logger.info("Connected to Redis successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            raise CacheError(f"Redis connection failed: {e}")
    
    async def disconnect(self):
        """断开Redis连接"""
        if self._client:
            await self._client.close()
            self._client = None
        
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
        
        self.logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[bytes]:
        """获取缓存值"""
        if not self._client:
            await self.connect()
        
        try:
            value = await self._client.get(key)
            
            if value is None:
                self._misses += 1
                return None
            
            self._hits += 1
            return value
            
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: bytes, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        if not self._client:
            await self.connect()
        
        try:
            if ttl is not None:
                await self._client.setex(key, ttl, value)
            else:
                await self._client.set(key, value)
            
            return True
            
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self._client:
            await self.connect()
        
        try:
            result = await self._client.delete(key)
            return result > 0
            
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self._client:
            await self.connect()
        
        try:
            result = await self._client.exists(key)
            return result > 0
            
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Redis exists error: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """设置过期时间"""
        if not self._client:
            await self.connect()
        
        try:
            result = await self._client.expire(key, ttl)
            return result
            
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Redis expire error: {e}")
            return False
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """清空缓存"""
        if not self._client:
            await self.connect()
        
        try:
            if pattern is None:
                # 清空整个数据库
                await self._client.flushdb()
                return -1  # 无法准确计数
            
            # 删除匹配的键
            keys = await self._client.keys(pattern)
            if keys:
                deleted = await self._client.delete(*keys)
                return deleted
            
            return 0
            
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Redis clear error: {e}")
            return 0
    
    async def keys(self, pattern: str) -> List[str]:
        """获取匹配的键列表"""
        if not self._client:
            await self.connect()
        
        try:
            keys = await self._client.keys(pattern)
            return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
            
        except Exception as e:
            self._errors += 1
            self.logger.error(f"Redis keys error: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'hits': self._hits,
            'misses': self._misses,
            'errors': self._errors,
            'hit_rate': self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0,
            'connected': self._client is not None
        }


# ================================
# 多层缓存管理器
# ================================

class MultiLevelCacheManager:
    """多层缓存管理器"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.MultiLevelCache")
        
        # 缓存层
        self.l1_cache = MemoryCacheBackend(config.max_memory_cache_size)
        self.l2_cache = RedisCacheBackend(config) if REDIS_AVAILABLE else None
        
        # 清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval = 300  # 5分钟清理一次
    
    async def start(self):
        """启动缓存管理器"""
        # 连接Redis
        if self.l2_cache:
            try:
                await self.l2_cache.connect()
            except Exception as e:
                self.logger.warning(f"Redis connection failed, using memory cache only: {e}")
                self.l2_cache = None
        
        # 启动清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.logger.info("Cache manager started")
    
    async def stop(self):
        """停止缓存管理器"""
        # 停止清理任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        # 断开Redis连接
        if self.l2_cache:
            await self.l2_cache.disconnect()
        
        self.logger.info("Cache manager stopped")
    
    def _make_key(self, key: str, namespace: str = "") -> str:
        """生成缓存键"""
        parts = [self.config.key_prefix]
        if namespace:
            parts.append(namespace)
        parts.append(key)
        return ":".join(parts)
    
    def _serialize(self, value: Any) -> bytes:
        """序列化值"""
        try:
            # 尝试JSON序列化（更快，更小）
            if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                data = json.dumps(value, ensure_ascii=False).encode('utf-8')
            else:
                # 使用pickle序列化复杂对象
                data = pickle.dumps(value)
            
            # 压缩大数据
            if self.config.use_compression and len(data) > self.config.compression_threshold:
                import gzip
                data = gzip.compress(data)
                data = b'GZIP:' + data
            
            return data
            
        except Exception as e:
            self.logger.error(f"Serialization error: {e}")
            raise CacheError(f"Failed to serialize value: {e}")
    
    def _deserialize(self, data: bytes) -> Any:
        """反序列化值"""
        try:
            # 检查是否压缩
            if data.startswith(b'GZIP:'):
                import gzip
                data = gzip.decompress(data[5:])
            
            # 尝试JSON反序列化
            try:
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # 使用pickle反序列化
                return pickle.loads(data)
                
        except Exception as e:
            self.logger.error(f"Deserialization error: {e}")
            raise CacheError(f"Failed to deserialize value: {e}")
    
    async def get(self, key: str, namespace: str = "") -> Optional[Any]:
        """获取缓存值"""
        cache_key = self._make_key(key, namespace)
        
        # L1缓存查找
        data = await self.l1_cache.get(cache_key)
        if data is not None:
            try:
                return self._deserialize(data)
            except Exception as e:
                self.logger.warning(f"L1 cache deserialization error: {e}")
                await self.l1_cache.delete(cache_key)
        
        # L2缓存查找
        if self.l2_cache:
            data = await self.l2_cache.get(cache_key)
            if data is not None:
                try:
                    value = self._deserialize(data)
                    
                    # 回写到L1缓存
                    await self.l1_cache.set(cache_key, data, self.config.default_ttl)
                    
                    return value
                except Exception as e:
                    self.logger.warning(f"L2 cache deserialization error: {e}")
                    await self.l2_cache.delete(cache_key)
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, 
                  namespace: str = "") -> bool:
        """设置缓存值"""
        cache_key = self._make_key(key, namespace)
        ttl = ttl or self.config.default_ttl
        
        try:
            data = self._serialize(value)
            
            # 写入L1缓存
            l1_success = await self.l1_cache.set(cache_key, data, ttl)
            
            # 写入L2缓存
            l2_success = True
            if self.l2_cache:
                l2_success = await self.l2_cache.set(cache_key, data, ttl)
            
            return l1_success or l2_success
            
        except Exception as e:
            self.logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str, namespace: str = "") -> bool:
        """删除缓存"""
        cache_key = self._make_key(key, namespace)
        
        # 从两层缓存删除
        l1_result = await self.l1_cache.delete(cache_key)
        l2_result = True
        
        if self.l2_cache:
            l2_result = await self.l2_cache.delete(cache_key)
        
        return l1_result or l2_result
    
    async def exists(self, key: str, namespace: str = "") -> bool:
        """检查键是否存在"""
        cache_key = self._make_key(key, namespace)
        
        # 检查L1缓存
        if await self.l1_cache.exists(cache_key):
            return True
        
        # 检查L2缓存
        if self.l2_cache:
            return await self.l2_cache.exists(cache_key)
        
        return False
    
    async def clear(self, namespace: str = "") -> int:
        """清空缓存"""
        pattern = self._make_key("*", namespace)
        
        # 清空L1缓存
        l1_count = await self.l1_cache.clear(pattern)
        
        # 清空L2缓存
        l2_count = 0
        if self.l2_cache:
            l2_count = await self.l2_cache.clear(pattern)
        
        return max(l1_count, l2_count)
    
    async def _cleanup_loop(self):
        """清理循环"""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                
                # 清理L1缓存过期条目
                await self.l1_cache.cleanup_expired()
                
                self.logger.debug("Cache cleanup completed")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cache cleanup error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            'l1_cache': self.l1_cache.get_stats(),
            'l2_cache_available': self.l2_cache is not None
        }
        
        if self.l2_cache:
            stats['l2_cache'] = self.l2_cache.get_stats()
        
        return stats


# ================================
# 专用缓存管理器
# ================================

class MessageCacheManager:
    """消息缓存管理器"""
    
    def __init__(self, cache_manager: MultiLevelCacheManager):
        self.cache = cache_manager
        self.config = cache_manager.config
        self.logger = logging.getLogger(f"{__name__}.MessageCache")
        
        self.namespace = "messages"
    
    async def cache_message(self, room_id: str, message: BaseMessage) -> bool:
        """缓存消息"""
        key = f"{room_id}:{message.id}"
        
        # 转换为字典以便序列化
        message_data = {
            'id': message.id,
            'type': message.type.value,
            'room_id': message.room_id,
            'user_id': message.user_id,
            'user_name': message.user_name,
            'content': message.content,
            'timestamp': message.timestamp.isoformat(),
            'metadata': message.metadata
        }
        
        return await self.cache.set(
            key, message_data, 
            ttl=self.config.message_cache_ttl,
            namespace=self.namespace
        )
    
    async def get_message(self, room_id: str, message_id: str) -> Optional[BaseMessage]:
        """获取缓存的消息"""
        key = f"{room_id}:{message_id}"
        
        data = await self.cache.get(key, namespace=self.namespace)
        if not data:
            return None
        
        try:
            # 重构消息对象
            message = BaseMessage(
                id=data['id'],
                type=MessageType(data['type']),
                room_id=data['room_id'],
                user_id=data['user_id'],
                user_name=data['user_name'],
                content=data['content'],
                timestamp=datetime.fromisoformat(data['timestamp']),
                metadata=data.get('metadata', {})
            )
            
            return message
            
        except Exception as e:
            self.logger.error(f"Failed to reconstruct message: {e}")
            return None
    
    async def get_room_messages(self, room_id: str, limit: int = 100) -> List[BaseMessage]:
        """获取房间消息列表"""
        # 这里应该实现更复杂的查询逻辑
        # 目前只是示例实现
        pattern = f"{room_id}:*"
        keys = await self.cache.l2_cache.keys(
            self.cache._make_key(pattern, self.namespace)
        ) if self.cache.l2_cache else []
        
        messages = []
        for key in keys[:limit]:
            # 提取消息ID
            message_id = key.split(':')[-1]
            message = await self.get_message(room_id, message_id)
            if message:
                messages.append(message)
        
        # 按时间排序
        messages.sort(key=lambda m: m.timestamp, reverse=True)
        return messages[:limit]
    
    async def clear_room_messages(self, room_id: str) -> int:
        """清空房间消息缓存"""
        pattern = f"{room_id}:*"
        
        if self.cache.l2_cache:
            keys = await self.cache.l2_cache.keys(
                self.cache._make_key(pattern, self.namespace)
            )
            
            count = 0
            for key in keys:
                if await self.cache.delete(key.split(':')[-1], namespace=self.namespace):
                    count += 1
            
            return count
        
        return 0


# ================================
# 用户缓存管理器
# ================================

class UserCacheManager:
    """用户信息缓存管理器"""
    
    def __init__(self, cache_manager: MultiLevelCacheManager):
        self.cache = cache_manager
        self.namespace = "users"
        self.logger = logging.getLogger(f"{__name__}.UserCacheManager")
    
    async def cache_user_info(self, user_id: str, user_info: Dict[str, Any], ttl: int = 3600):
        """缓存用户信息"""
        key = f"info:{user_id}"
        await self.cache.set(key, user_info, ttl=ttl, namespace=self.namespace)
        self.logger.debug(f"Cached user info for {user_id}")
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        key = f"info:{user_id}"
        return await self.cache.get(key, namespace=self.namespace)
    
    async def cache_user_stats(self, user_id: str, stats: Dict[str, Any], ttl: int = 1800):
        """缓存用户统计信息"""
        key = f"stats:{user_id}"
        await self.cache.set(key, stats, ttl=ttl, namespace=self.namespace)
    
    async def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户统计信息"""
        key = f"stats:{user_id}"
        return await self.cache.get(key, namespace=self.namespace)
    
    async def clear_user_cache(self, user_id: str) -> int:
        """清空用户缓存"""
        pattern = f"*:{user_id}"
        count = 0
        
        if self.cache.l2_cache:
            keys = await self.cache.l2_cache.keys(
                self.cache._make_key(pattern, self.namespace)
            )
            
            for key in keys:
                cache_key = key.split(':')[-2] + ':' + key.split(':')[-1]
                if await self.cache.delete(cache_key, namespace=self.namespace):
                    count += 1
        
        return count


# ================================
# 房间缓存管理器
# ================================

class RoomCacheManager:
    """房间信息缓存管理器"""
    
    def __init__(self, cache_manager: MultiLevelCacheManager):
        self.cache = cache_manager
        self.namespace = "rooms"
        self.logger = logging.getLogger(f"{__name__}.RoomCacheManager")
    
    async def cache_room_info(self, room_id: str, room_info: Dict[str, Any], ttl: int = 1800):
        """缓存房间信息"""
        key = f"info:{room_id}"
        await self.cache.set(key, room_info, ttl=ttl, namespace=self.namespace)
        self.logger.debug(f"Cached room info for {room_id}")
    
    async def get_room_info(self, room_id: str) -> Optional[Dict[str, Any]]:
        """获取房间信息"""
        key = f"info:{room_id}"
        return await self.cache.get(key, namespace=self.namespace)
    
    async def cache_room_stats(self, room_id: str, stats: Dict[str, Any], ttl: int = 300):
        """缓存房间统计信息"""
        key = f"stats:{room_id}"
        await self.cache.set(key, stats, ttl=ttl, namespace=self.namespace)
    
    async def get_room_stats(self, room_id: str) -> Optional[Dict[str, Any]]:
        """获取房间统计信息"""
        key = f"stats:{room_id}"
        return await self.cache.get(key, namespace=self.namespace)
    
    async def cache_room_users(self, room_id: str, user_list: List[str], ttl: int = 600):
        """缓存房间用户列表"""
        key = f"users:{room_id}"
        await self.cache.set(key, user_list, ttl=ttl, namespace=self.namespace)
    
    async def get_room_users(self, room_id: str) -> Optional[List[str]]:
        """获取房间用户列表"""
        key = f"users:{room_id}"
        return await self.cache.get(key, namespace=self.namespace)
    
    async def clear_room_cache(self, room_id: str) -> int:
        """清空房间缓存"""
        pattern = f"*:{room_id}"
        count = 0
        
        if self.cache.l2_cache:
            keys = await self.cache.l2_cache.keys(
                self.cache._make_key(pattern, self.namespace)
            )
            
            for key in keys:
                cache_key = key.split(':')[-2] + ':' + key.split(':')[-1]
                if await self.cache.delete(cache_key, namespace=self.namespace):
                    count += 1
        
        return count


# ================================
# 全局缓存管理器
# ================================

class GlobalCacheManager:
    """全局缓存管理器，统一管理所有缓存"""
    
    def __init__(self, cache_manager: MultiLevelCacheManager):
        self.cache = cache_manager
        self.message_cache = MessageCacheManager(cache_manager)
        self.user_cache = UserCacheManager(cache_manager)
        self.room_cache = RoomCacheManager(cache_manager)
        self.logger = logging.getLogger(f"{__name__}.GlobalCacheManager")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = await self.cache.get_stats()
        
        # 添加各个缓存管理器的统计信息
        stats.update({
            'message_cache': 'active',
            'user_cache': 'active',
            'room_cache': 'active'
        })
        
        return stats
    
    async def clear_all_cache(self) -> Dict[str, int]:
        """清空所有缓存"""
        results = {}
        
        # 清空各个命名空间的缓存
        if self.cache.l2_cache:
            for namespace in ['messages', 'users', 'rooms']:
                pattern = f"{namespace}:*"
                keys = await self.cache.l2_cache.keys(pattern)
                count = 0
                
                for key in keys:
                    await self.cache.l2_cache.delete(key)
                    count += 1
                
                results[namespace] = count
        
        # 清空内存缓存
        if hasattr(self.cache, 'l1_cache'):
            self.cache.l1_cache.clear()
            results['memory'] = 'cleared'
        
        self.logger.info(f"Cleared all cache: {results}")
        return results
    
    async def warm_cache(self, room_id: str):
        """预热缓存"""
        self.logger.info(f"Warming cache for room {room_id}")
        
        # 这里可以实现具体的缓存预热逻辑
        # 例如预加载房间信息、用户信息等
        
        warmer = CacheWarmer(self.cache)
        await warmer.warm_message_cache(room_id)
        await warmer.warm_stats_cache(room_id)


# ================================
# 全局缓存实例管理
# ================================

_cache_manager: Optional[MultiLevelCacheManager] = None
_message_cache: Optional[MessageCacheManager] = None


async def get_cache_manager() -> MultiLevelCacheManager:
    """获取全局缓存管理器"""
    global _cache_manager
    
    if _cache_manager is None:
        config_manager = get_config_manager()
        
        # 从配置中获取缓存配置
        cache_config = CacheConfig()
        
        # 尝试从配置文件更新配置
        try:
            config_data = config_manager.get_config()
            
            if 'cache' in config_data:
                cache_section = config_data['cache']
                
                # 更新Redis配置
                if 'redis' in cache_section:
                    redis_config = cache_section['redis']
                    cache_config.redis_host = redis_config.get('host', cache_config.redis_host)
                    cache_config.redis_port = redis_config.get('port', cache_config.redis_port)
                    cache_config.redis_db = redis_config.get('db', cache_config.redis_db)
                    cache_config.redis_password = redis_config.get('password')
                
                # 更新缓存策略
                cache_config.default_ttl = cache_section.get('default_ttl', cache_config.default_ttl)
                cache_config.max_memory_cache_size = cache_section.get(
                    'max_memory_cache_size', cache_config.max_memory_cache_size
                )
                
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to load cache config: {e}")
        
        _cache_manager = MultiLevelCacheManager(cache_config)
        await _cache_manager.start()
    
    return _cache_manager


async def get_message_cache() -> MessageCacheManager:
    """获取消息缓存管理器"""
    global _message_cache
    
    if _message_cache is None:
        cache_manager = await get_cache_manager()
        _message_cache = MessageCacheManager(cache_manager)
    
    return _message_cache


async def cleanup_cache():
    """清理缓存资源"""
    global _cache_manager, _message_cache
    
    if _cache_manager:
        await _cache_manager.stop()
        _cache_manager = None
    
    _message_cache = None


# ================================
# 缓存装饰器
# ================================

def cache_result(ttl: int = 300, namespace: str = "", key_func: Optional[Callable] = None):
    """缓存结果装饰器"""
    
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 默认键生成策略
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
            
            # 尝试从缓存获取
            cache_manager = await get_cache_manager()
            cached_result = await cache_manager.get(cache_key, namespace=namespace)
            
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl=ttl, namespace=namespace)
            
            return result
        
        return wrapper
    
    return decorator


def cache_async_result(ttl: int = 300, namespace: str = "", key_func: Optional[Callable] = None):
    """异步缓存结果装饰器（与cache_result功能相同，为兼容性保留）"""
    return cache_result(ttl=ttl, namespace=namespace, key_func=key_func)


# ================================
# 缓存预加载器
# ================================

class CachePreloader:
    """缓存预加载器"""
    
    def __init__(self, cache_manager: MultiLevelCacheManager):
        self.cache = cache_manager
        self.logger = logging.getLogger(f"{__name__}.CachePreloader")
    
    async def preload_room_data(self, room_id: str):
        """预加载房间数据"""
        self.logger.info(f"Preloading data for room {room_id}")
        
        # 预加载房间基本信息
        await self._preload_room_info(room_id)
        
        # 预加载最近消息
        await self._preload_recent_messages(room_id)
        
        # 预加载统计信息
        await self._preload_room_stats(room_id)
    
    async def _preload_room_info(self, room_id: str):
        """预加载房间信息"""
        # 这里应该实现房间信息的预加载逻辑
        self.logger.debug(f"Preloading room info for {room_id}")
    
    async def _preload_recent_messages(self, room_id: str):
        """预加载最近消息"""
        # 这里应该实现最近消息的预加载逻辑
        self.logger.debug(f"Preloading recent messages for {room_id}")
    
    async def _preload_room_stats(self, room_id: str):
        """预加载房间统计"""
        # 这里应该实现房间统计的预加载逻辑
        self.logger.debug(f"Preloading room stats for {room_id}")


# ================================
# 缓存预热
# ================================

class CacheWarmer:
    """缓存预热器"""
    
    def __init__(self, cache_manager: MultiLevelCacheManager):
        self.cache = cache_manager
        self.logger = logging.getLogger(f"{__name__}.CacheWarmer")
    
    async def warm_user_cache(self, room_id: str, user_ids: List[str]):
        """预热用户缓存"""
        # 这里应该实现用户信息的预加载逻辑
        self.logger.info(f"Warming user cache for room {room_id}: {len(user_ids)} users")
    
    async def warm_message_cache(self, room_id: str):
        """预热消息缓存"""
        # 这里应该实现消息的预加载逻辑
        self.logger.info(f"Warming message cache for room {room_id}")
    
    async def warm_stats_cache(self, room_id: str):
        """预热统计缓存"""
        # 这里应该实现统计信息的预加载逻辑
        self.logger.info(f"Warming stats cache for room {room_id}")