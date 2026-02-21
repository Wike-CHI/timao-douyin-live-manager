# -*- coding: utf-8 -*-
"""
内存缓存管理器（已移除 Redis 依赖）

原为 Redis 缓存管理器，现已简化为纯内存实现。
保留常用接口以保持向后兼容。
"""

from typing import Any, Dict, Optional
import time
import logging

logger = logging.getLogger(__name__)


class RedisManager:
    """
    内存缓存管理器

    原为 Redis 缓存管理器，现已简化为纯内存实现。
    保留常用接口以保持向后兼容。
    """

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._hash_cache: Dict[str, Dict[str, Any]] = {}
        self._ttl: Dict[str, float] = {}
        logger.info("RedisManager 初始化（内存缓存模式）")

    def get(self, key: str, default: Any = None) -> Optional[Any]:
        """获取缓存值"""
        self._check_expired(key)
        return self._cache.get(key, default)

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存值"""
        self._cache[key] = value
        if ttl:
            self._ttl[key] = time.time() + ttl
        return True

    def delete(self, *keys: str) -> int:
        """删除缓存"""
        count = 0
        for key in keys:
            if key in self._cache:
                self._cache.pop(key, None)
                count += 1
            if key in self._hash_cache:
                self._hash_cache.pop(key, None)
                count += 1
            self._ttl.pop(key, None)
        return count

    def hget(self, name: str, key: str) -> Optional[str]:
        """获取哈希字段"""
        self._check_expired(name)
        if name in self._hash_cache:
            return self._hash_cache[name].get(key)
        return None

    def hgetall(self, name: str) -> Dict[str, str]:
        """获取所有哈希字段"""
        self._check_expired(name)
        return self._hash_cache.get(name, {}).copy()

    def hset(self, name: str, key: str = None, value: Any = None, mapping: dict = None) -> bool:
        """设置哈希字段"""
        if name not in self._hash_cache:
            self._hash_cache[name] = {}

        if mapping:
            self._hash_cache[name].update(mapping)
        elif key is not None and value is not None:
            self._hash_cache[name][key] = value
        return True

    def hdel(self, name: str, *keys: str) -> int:
        """删除哈希字段"""
        count = 0
        if name in self._hash_cache:
            if keys:
                for key in keys:
                    if key in self._hash_cache[name]:
                        del self._hash_cache[name][key]
                        count += 1
                if not self._hash_cache[name]:
                    del self._hash_cache[name]
            else:
                count = 1
                del self._hash_cache[name]
        return count

    def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        self._ttl[key] = time.time() + seconds
        return True

    def exists(self, *keys: str) -> int:
        """检查键是否存在"""
        count = 0
        for key in keys:
            self._check_expired(key)
            if key in self._cache or key in self._hash_cache:
                count += 1
        return count

    def is_enabled(self) -> bool:
        """缓存是否启用"""
        return True

    def ping(self) -> bool:
        """测试缓存可用性"""
        return True

    def ttl(self, key: str) -> int:
        """获取键的剩余过期时间"""
        self._check_expired(key)
        if key not in self._cache and key not in self._hash_cache:
            return -2
        if key not in self._ttl:
            return -1
        remaining = int(self._ttl[key] - time.time())
        return remaining if remaining >= 0 else -2

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """增加计数器"""
        self._check_expired(key)
        current = self._cache.get(key, 0)
        try:
            current_int = int(current)
        except (ValueError, TypeError):
            current_int = 0
        current_int += amount
        self._cache[key] = current_int
        return current_int

    def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """减少计数器"""
        return self.incr(key, -amount)

    def _check_expired(self, key: str):
        """检查并清理过期键"""
        if key in self._ttl and time.time() > self._ttl[key]:
            self._cache.pop(key, None)
            self._hash_cache.pop(key, None)
            self._ttl.pop(key, None)

    def close(self) -> None:
        """关闭缓存（内存实现无需操作）"""
        pass

    def flush_db(self) -> bool:
        """清空缓存"""
        self._cache.clear()
        self._hash_cache.clear()
        self._ttl.clear()
        return True


# 全局实例
_redis_manager: Optional[RedisManager] = None


def get_redis() -> RedisManager:
    """获取缓存管理器实例"""
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisManager()
    return _redis_manager


def init_redis(config: Any = None) -> RedisManager:
    """
    初始化缓存管理器（兼容旧接口）

    Args:
        config: 忽略，保留参数兼容性

    Returns:
        RedisManager 实例
    """
    return get_redis()


def close_redis() -> None:
    """关闭缓存连接"""
    global _redis_manager
    if _redis_manager:
        _redis_manager.close()
        _redis_manager = None
