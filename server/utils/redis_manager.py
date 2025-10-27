# -*- coding: utf-8 -*-
"""
Redis 缓存管理器
"""

import json
import logging
import time
from typing import Optional, Any, Union, Dict, List, Set
from datetime import timedelta
import redis
from redis.connection import ConnectionPool
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from server.config import RedisConfig

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis 缓存管理器"""
    
    def __init__(self, config: Optional[RedisConfig] = None):
        """
        初始化 Redis 管理器
        
        Args:
            config: Redis 配置对象
        """
        self.config = config or RedisConfig()
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._enabled = self.config.enabled
        # 内存缓存回退（当 Redis 未启用或连接失败时）
        self._use_memory: bool = False
        self._mem_kv: Dict[str, Any] = {}
        self._mem_hash: Dict[str, Dict[str, Any]] = {}
        self._mem_list: Dict[str, List[Any]] = {}
        self._mem_set: Dict[str, Set[Any]] = {}
        self._mem_expiry: Dict[str, float] = {}
        
        if self._enabled:
            self._initialize()
        else:
            # 未启用时，默认使用内存缓存
            self._use_memory = True
    
    def _initialize(self) -> None:
        """初始化 Redis 连接"""
        try:
            # 创建连接池
            pool_kwargs = {
                'host': self.config.host,
                'port': self.config.port,
                'db': self.config.db,
                'max_connections': self.config.max_connections,
                'socket_timeout': self.config.socket_timeout,
                'socket_connect_timeout': self.config.socket_connect_timeout,
                'socket_keepalive': self.config.socket_keepalive,
                'retry_on_timeout': self.config.retry_on_timeout,
                'decode_responses': True,  # 自动解码为字符串
            }
            
            # 如果设置了密码
            if self.config.password:
                pool_kwargs['password'] = self.config.password
            
            self._pool = ConnectionPool(**pool_kwargs)
            self._client = redis.Redis(connection_pool=self._pool)
            
            # 测试连接
            self._client.ping()
            logger.info(f"✅ Redis 连接成功: {self.config.host}:{self.config.port}")
            
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"⚠️ Redis 连接失败，缓存功能已禁用: {e}")
            self._enabled = False
            self._client = None
            self._pool = None
            # 使用内存缓存作为回退
            self._use_memory = True
        except Exception as e:
            logger.error(f"❌ Redis 初始化失败: {e}")
            self._enabled = False
            self._client = None
            self._pool = None
            # 使用内存缓存作为回退
            self._use_memory = True
    
    def is_enabled(self) -> bool:
        """检查 Redis 是否可用"""
        return self._enabled and self._client is not None
    
    def _get_key(self, key: str) -> str:
        """获取完整的键名（添加前缀）"""
        return f"{self.config.key_prefix}{key}"

    # ===== 内存缓存辅助方法 =====
    def _now(self) -> float:
        return time.time()

    def _is_expired(self, key: str) -> bool:
        exp = self._mem_expiry.get(key)
        return exp is not None and exp <= self._now()

    def _cleanup_if_expired(self, key: str) -> None:
        if self._is_expired(key):
            self._mem_expiry.pop(key, None)
            self._mem_kv.pop(key, None)
            self._mem_hash.pop(key, None)
            self._mem_list.pop(key, None)
            self._mem_set.pop(key, None)

    def _set_expiry(self, key: str, ttl: Optional[int]) -> None:
        if ttl is None:
            ttl = self.config.default_ttl
        self._mem_expiry[key] = self._now() + max(0, int(ttl))
    
    def get(self, key: str, default: Any = None) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值
            
        Returns:
            缓存值或默认值
        """
        if not self.is_enabled():
            # 内存回退
            if self._use_memory:
                k = self._get_key(key)
                self._cleanup_if_expired(k)
                return self._mem_kv.get(k, default)
            return default
        
        try:
            value = self._client.get(self._get_key(key))
            if value is None:
                return default
            
            # 尝试 JSON 解析
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except RedisError as e:
            logger.warning(f"Redis get 失败 [{key}]: {e}")
            return default
    
    def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 表示使用默认值
            nx: 仅当键不存在时设置
            xx: 仅当键存在时设置
            
        Returns:
            是否设置成功
        """
        if not self.is_enabled():
            # 内存回退
            if self._use_memory:
                k = self._get_key(key)
                self._cleanup_if_expired(k)
                exists = k in self._mem_kv
                if nx and exists:
                    return False
                if xx and not exists:
                    return False
                self._mem_kv[k] = value
                self._set_expiry(k, ttl)
                return True
            return False
        
        try:
            # 序列化值
            if isinstance(value, (dict, list, tuple)):
                value = json.dumps(value, ensure_ascii=False)
            elif not isinstance(value, str):
                value = str(value)
            
            # 设置过期时间
            ex = ttl if ttl is not None else self.config.default_ttl
            
            # 设置值
            result = self._client.set(
                self._get_key(key),
                value,
                ex=ex,
                nx=nx,
                xx=xx
            )
            
            return bool(result)
            
        except RedisError as e:
            logger.warning(f"Redis set 失败 [{key}]: {e}")
            return False
    
    def delete(self, *keys: str) -> int:
        """
        删除缓存
        
        Args:
            *keys: 要删除的键
            
        Returns:
            删除的键数量
        """
        if not self.is_enabled() or not keys:
            if not self.is_enabled() and self._use_memory:
                count = 0
                for key in keys:
                    k = self._get_key(key)
                    self._cleanup_if_expired(k)
                    removed = False
                    if k in self._mem_kv:
                        self._mem_kv.pop(k, None)
                        removed = True
                    if k in self._mem_hash:
                        self._mem_hash.pop(k, None)
                        removed = True
                    if k in self._mem_list:
                        self._mem_list.pop(k, None)
                        removed = True
                    if k in self._mem_set:
                        self._mem_set.pop(k, None)
                        removed = True
                    self._mem_expiry.pop(k, None)
                    if removed:
                        count += 1
                return count
            return 0
        
        try:
            full_keys = [self._get_key(key) for key in keys]
            return self._client.delete(*full_keys)
        except RedisError as e:
            logger.warning(f"Redis delete 失败: {e}")
            return 0
    
    def exists(self, *keys: str) -> int:
        """
        检查键是否存在
        
        Args:
            *keys: 要检查的键
            
        Returns:
            存在的键数量
        """
        if not self.is_enabled() or not keys:
            if not self.is_enabled() and self._use_memory:
                cnt = 0
                for key in keys:
                    k = self._get_key(key)
                    self._cleanup_if_expired(k)
                    if k in self._mem_kv or k in self._mem_hash or k in self._mem_list or k in self._mem_set:
                        cnt += 1
                return cnt
            return 0
        
        try:
            full_keys = [self._get_key(key) for key in keys]
            return self._client.exists(*full_keys)
        except RedisError as e:
            logger.warning(f"Redis exists 失败: {e}")
            return 0
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        设置键的过期时间
        
        Args:
            key: 缓存键
            seconds: 过期时间（秒）
            
        Returns:
            是否设置成功
        """
        if not self.is_enabled():
            if self._use_memory:
                k = self._get_key(key)
                self._cleanup_if_expired(k)
                if k in self._mem_kv or k in self._mem_hash or k in self._mem_list or k in self._mem_set:
                    self._set_expiry(k, seconds)
                    return True
                return False
            return False
        
        try:
            return bool(self._client.expire(self._get_key(key), seconds))
        except RedisError as e:
            logger.warning(f"Redis expire 失败 [{key}]: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """
        获取键的剩余过期时间
        
        Args:
            key: 缓存键
            
        Returns:
            剩余时间（秒），-1 表示永不过期，-2 表示键不存在
        """
        if not self.is_enabled():
            if self._use_memory:
                k = self._get_key(key)
                self._cleanup_if_expired(k)
                if not (k in self._mem_kv or k in self._mem_hash or k in self._mem_list or k in self._mem_set):
                    return -2
                exp = self._mem_expiry.get(k)
                if exp is None:
                    return -1
                remaining = int(exp - self._now())
                return remaining if remaining >= 0 else -2
            return -2
        
        try:
            return self._client.ttl(self._get_key(key))
        except RedisError as e:
            logger.warning(f"Redis ttl 失败 [{key}]: {e}")
            return -2
    
    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        增加计数器
        
        Args:
            key: 缓存键
            amount: 增加量
            
        Returns:
            增加后的值
        """
        if not self.is_enabled():
            if self._use_memory:
                k = self._get_key(key)
                self._cleanup_if_expired(k)
                current = self._mem_kv.get(k, 0)
                try:
                    current_int = int(current)
                except (ValueError, TypeError):
                    current_int = 0
                current_int += amount
                self._mem_kv[k] = current_int
                # 不改变原有过期策略；如需设置过期请调用 expire
                return current_int
            return None
        
        try:
            return self._client.incr(self._get_key(key), amount)
        except RedisError as e:
            logger.warning(f"Redis incr 失败 [{key}]: {e}")
            return None
    
    def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        减少计数器
        
        Args:
            key: 缓存键
            amount: 减少量
            
        Returns:
            减少后的值
        """
        if not self.is_enabled():
            if self._use_memory:
                k = self._get_key(key)
                self._cleanup_if_expired(k)
                current = self._mem_kv.get(k, 0)
                try:
                    current_int = int(current)
                except (ValueError, TypeError):
                    current_int = 0
                current_int -= amount
                self._mem_kv[k] = current_int
                return current_int
            return None
        
        try:
            return self._client.decr(self._get_key(key), amount)
        except RedisError as e:
            logger.warning(f"Redis decr 失败 [{key}]: {e}")
            return None
    
    def hget(self, name: str, key: str) -> Optional[str]:
        """
        获取哈希表字段值
        
        Args:
            name: 哈希表名
            key: 字段名
            
        Returns:
            字段值
        """
        if not self.is_enabled():
            if self._use_memory:
                n = self._get_key(name)
                self._cleanup_if_expired(n)
                table = self._mem_hash.get(n)
                if not table:
                    return None
                val = table.get(key)
                return val if val is not None else None
            return None
        
        try:
            return self._client.hget(self._get_key(name), key)
        except RedisError as e:
            logger.warning(f"Redis hget 失败 [{name}.{key}]: {e}")
            return None
    
    def hset(self, name: str, key: str, value: Any) -> bool:
        """
        设置哈希表字段值
        
        Args:
            name: 哈希表名
            key: 字段名
            value: 字段值
            
        Returns:
            是否设置成功
        """
        if not self.is_enabled():
            if self._use_memory:
                n = self._get_key(name)
                self._cleanup_if_expired(n)
                table = self._mem_hash.get(n)
                if table is None:
                    table = {}
                    self._mem_hash[n] = table
                table[key] = value
                return True
            return False
        
        try:
            # 序列化值
            if isinstance(value, (dict, list, tuple)):
                value = json.dumps(value, ensure_ascii=False)
            elif not isinstance(value, str):
                value = str(value)
            
            return bool(self._client.hset(self._get_key(name), key, value))
        except RedisError as e:
            logger.warning(f"Redis hset 失败 [{name}.{key}]: {e}")
            return False
    
    def hgetall(self, name: str) -> dict:
        """
        获取哈希表所有字段
        
        Args:
            name: 哈希表名
            
        Returns:
            字段字典
        """
        if not self.is_enabled():
            if self._use_memory:
                n = self._get_key(name)
                self._cleanup_if_expired(n)
                table = self._mem_hash.get(n)
                return dict(table) if table else {}
            return {}
        
        try:
            return self._client.hgetall(self._get_key(name))
        except RedisError as e:
            logger.warning(f"Redis hgetall 失败 [{name}]: {e}")
            return {}
    
    def hdel(self, name: str, *keys: str) -> int:
        """
        删除哈希表字段
        
        Args:
            name: 哈希表名
            *keys: 要删除的字段名
            
        Returns:
            删除的字段数量
        """
        if not self.is_enabled() or not keys:
            if not self.is_enabled() and self._use_memory and keys:
                n = self._get_key(name)
                self._cleanup_if_expired(n)
                table = self._mem_hash.get(n)
                if not table:
                    return 0
                count = 0
                for k in keys:
                    if k in table:
                        del table[k]
                        count += 1
                if not table:
                    self._mem_hash.pop(n, None)
                return count
            return 0
        
        try:
            return self._client.hdel(self._get_key(name), *keys)
        except RedisError as e:
            logger.warning(f"Redis hdel 失败 [{name}]: {e}")
            return 0
    
    def lpush(self, key: str, *values: Any) -> Optional[int]:
        """
        向列表左侧添加元素
        
        Args:
            key: 列表键
            *values: 要添加的值
            
        Returns:
            列表长度
        """
        if not self.is_enabled() or not values:
            if not self.is_enabled() and self._use_memory and values:
                k = self._get_key(key)
                self._cleanup_if_expired(k)
                lst = self._mem_list.get(k)
                if lst is None:
                    lst = []
                    self._mem_list[k] = lst
                # 序列化与原实现保持一致
                serialized_values = []
                for value in values:
                    if isinstance(value, (dict, list, tuple)):
                        serialized_values.append(json.dumps(value, ensure_ascii=False))
                    elif not isinstance(value, str):
                        serialized_values.append(str(value))
                    else:
                        serialized_values.append(value)
                for v in serialized_values:
                    lst.insert(0, v)
                return len(lst)
            return None
        
        try:
            # 序列化值
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list, tuple)):
                    serialized_values.append(json.dumps(value, ensure_ascii=False))
                elif not isinstance(value, str):
                    serialized_values.append(str(value))
                else:
                    serialized_values.append(value)
            
            return self._client.lpush(self._get_key(key), *serialized_values)
        except RedisError as e:
            logger.warning(f"Redis lpush 失败 [{key}]: {e}")
            return None
    
    def rpush(self, key: str, *values: Any) -> Optional[int]:
        """
        向列表右侧添加元素
        
        Args:
            key: 列表键
            *values: 要添加的值
            
        Returns:
            列表长度
        """
        if not self.is_enabled() or not values:
            if not self.is_enabled() and self._use_memory and values:
                k = self._get_key(key)
                self._cleanup_if_expired(k)
                lst = self._mem_list.get(k)
                if lst is None:
                    lst = []
                    self._mem_list[k] = lst
                serialized_values = []
                for value in values:
                    if isinstance(value, (dict, list, tuple)):
                        serialized_values.append(json.dumps(value, ensure_ascii=False))
                    elif not isinstance(value, str):
                        serialized_values.append(str(value))
                    else:
                        serialized_values.append(value)
                lst.extend(serialized_values)
                return len(lst)
            return None
        
        try:
            # 序列化值
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list, tuple)):
                    serialized_values.append(json.dumps(value, ensure_ascii=False))
                elif not isinstance(value, str):
                    serialized_values.append(str(value))
                else:
                    serialized_values.append(value)
            
            return self._client.rpush(self._get_key(key), *serialized_values)
        except RedisError as e:
            logger.warning(f"Redis rpush 失败 [{key}]: {e}")
            return None
    
    def lrange(self, key: str, start: int = 0, end: int = -1) -> list:
        """
        获取列表范围内的元素
        
        Args:
            key: 列表键
            start: 起始索引
            end: 结束索引（-1 表示到末尾）
            
        Returns:
            元素列表
        """
        if not self.is_enabled():
            if self._use_memory:
                k = self._get_key(key)
                self._cleanup_if_expired(k)
                lst = self._mem_list.get(k, [])
                n = len(lst)
                s = start if start >= 0 else n + start
                e = end if end >= 0 else n + end
                s = max(s, 0)
                e = min(e, n - 1)
                if s > e or n == 0:
                    return []
                return lst[s:e + 1]
            return []
        
        try:
            return self._client.lrange(self._get_key(key), start, end)
        except RedisError as e:
            logger.warning(f"Redis lrange 失败 [{key}]: {e}")
            return []
    
    def ltrim(self, key: str, start: int, end: int) -> bool:
        """
        修剪列表，只保留指定范围内的元素
        
        Args:
            key: 列表键
            start: 起始索引
            end: 结束索引
            
        Returns:
            是否成功
        """
        if not self.is_enabled():
            if self._use_memory:
                k = self._get_key(key)
                self._cleanup_if_expired(k)
                lst = self._mem_list.get(k)
                if lst is None:
                    return True
                n = len(lst)
                s = start if start >= 0 else n + start
                e = end if end >= 0 else n + end
                s = max(s, 0)
                e = min(e, n - 1)
                if s > e or n == 0:
                    self._mem_list[k] = []
                    return True
                self._mem_list[k] = lst[s:e + 1]
                return True
            return False
        
        try:
            return bool(self._client.ltrim(self._get_key(key), start, end))
        except RedisError as e:
            logger.warning(f"Redis ltrim 失败 [{key}]: {e}")
            return False
    
    def sadd(self, key: str, *members: Any) -> Optional[int]:
        """
        向集合添加成员
        
        Args:
            key: 集合键
            *members: 要添加的成员
            
        Returns:
            添加的成员数量
        """
        if not self.is_enabled() or not members:
            if not self.is_enabled() and self._use_memory and members:
                k = self._get_key(key)
                self._cleanup_if_expired(k)
                s = self._mem_set.get(k)
                if s is None:
                    s = set()
                    self._mem_set[k] = s
                before = len(s)
                serialized_members = []
                for member in members:
                    if isinstance(member, (dict, list, tuple)):
                        serialized_members.append(json.dumps(member, ensure_ascii=False))
                    elif not isinstance(member, str):
                        serialized_members.append(str(member))
                    else:
                        serialized_members.append(member)
                for m in serialized_members:
                    s.add(m)
                return len(s) - before
            return None
        
        try:
            # 序列化值
            serialized_members = []
            for member in members:
                if isinstance(member, (dict, list, tuple)):
                    serialized_members.append(json.dumps(member, ensure_ascii=False))
                elif not isinstance(member, str):
                    serialized_members.append(str(member))
                else:
                    serialized_members.append(member)
            
            return self._client.sadd(self._get_key(key), *serialized_members)
        except RedisError as e:
            logger.warning(f"Redis sadd 失败 [{key}]: {e}")
            return None
    
    def smembers(self, key: str) -> set:
        """
        获取集合所有成员
        
        Args:
            key: 集合键
            
        Returns:
            成员集合
        """
        if not self.is_enabled():
            if self._use_memory:
                k = self._get_key(key)
                self._cleanup_if_expired(k)
                return set(self._mem_set.get(k, set()))
            return set()
        
        try:
            return self._client.smembers(self._get_key(key))
        except RedisError as e:
            logger.warning(f"Redis smembers 失败 [{key}]: {e}")
            return set()
    
    def srem(self, key: str, *members: Any) -> Optional[int]:
        """
        从集合删除成员
        
        Args:
            key: 集合键
            *members: 要删除的成员
            
        Returns:
            删除的成员数量
        """
        if not self.is_enabled() or not members:
            if not self.is_enabled() and self._use_memory and members:
                k = self._get_key(key)
                self._cleanup_if_expired(k)
                s = self._mem_set.get(k)
                if not s:
                    return 0
                serialized_members = []
                for member in members:
                    if isinstance(member, (dict, list, tuple)):
                        serialized_members.append(json.dumps(member, ensure_ascii=False))
                    elif not isinstance(member, str):
                        serialized_members.append(str(member))
                    else:
                        serialized_members.append(member)
                count = 0
                for m in serialized_members:
                    if m in s:
                        s.remove(m)
                        count += 1
                if not s:
                    self._mem_set.pop(k, None)
                return count
            return None
        
        try:
            # 序列化值
            serialized_members = []
            for member in members:
                if isinstance(member, (dict, list, tuple)):
                    serialized_members.append(json.dumps(member, ensure_ascii=False))
                elif not isinstance(member, str):
                    serialized_members.append(str(member))
                else:
                    serialized_members.append(member)
            
            return self._client.srem(self._get_key(key), *serialized_members)
        except RedisError as e:
            logger.warning(f"Redis srem 失败 [{key}]: {e}")
            return None
    
    def flush_db(self) -> bool:
        """
        清空当前数据库
        
        Returns:
            是否成功
        """
        if not self.is_enabled():
            if self._use_memory:
                # 清空内存数据
                self._mem_kv.clear()
                self._mem_hash.clear()
                self._mem_list.clear()
                self._mem_set.clear()
                self._mem_expiry.clear()
                return True
            return False
        
        try:
            return bool(self._client.flushdb())
        except RedisError as e:
            logger.error(f"Redis flushdb 失败: {e}")
            return False
    
    def ping(self) -> bool:
        """
        测试 Redis 连接
        
        Returns:
            是否连接正常
        """
        if not self.is_enabled():
            # 在使用内存回退时，认为“缓存后端可用”
            if self._use_memory:
                return True
            return False
        
        try:
            return self._client.ping()
        except RedisError as e:
            logger.warning(f"Redis ping 失败: {e}")
            return False
    
    def close(self) -> None:
        """关闭 Redis 连接"""
        if self._client:
            try:
                self._client.close()
                logger.info("Redis 连接已关闭")
            except Exception as e:
                logger.error(f"关闭 Redis 连接失败: {e}")
        
        if self._pool:
            try:
                self._pool.disconnect()
            except Exception as e:
                logger.error(f"关闭 Redis 连接池失败: {e}")


# 全局 Redis 管理器实例
redis_manager: Optional[RedisManager] = None


def init_redis(config: Optional[RedisConfig] = None) -> RedisManager:
    """
    初始化 Redis 管理器
    
    Args:
        config: Redis 配置
        
    Returns:
        Redis 管理器实例
    """
    global redis_manager
    redis_manager = RedisManager(config)
    return redis_manager


def get_redis() -> Optional[RedisManager]:
    """
    获取 Redis 管理器实例
    
    Returns:
        Redis 管理器实例
    """
    return redis_manager


def close_redis() -> None:
    """关闭 Redis 连接"""
    global redis_manager
    if redis_manager:
        redis_manager.close()
        redis_manager = None
