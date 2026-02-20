# 移除 Redis 依赖实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完全移除 Redis 依赖，保留内存缓存和批量处理功能

**Architecture:** 将 RedisManager 简化为纯内存实现，保持接口兼容性。移除各服务中的 Redis 调用，保留内存缓冲和批量处理逻辑。

**Tech Stack:** Python, asyncio, 内存缓存

---

## Task 1: 简化 redis_manager.py

**Files:**
- Modify: `server/utils/redis_manager.py`

**Step 1: 备份并重写 redis_manager.py**

将现有的 Redis 实现替换为纯内存实现：

```python
# server/utils/redis_manager.py
"""内存缓存管理器（已移除 Redis 依赖）"""

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

    def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        self._check_expired(key)
        return self._cache.get(key)

    def set(self, key: str, value: str, ttl: int = None) -> bool:
        """设置缓存值"""
        self._cache[key] = value
        if ttl:
            self._ttl[key] = time.time() + ttl
        return True

    def delete(self, key: str) -> bool:
        """删除缓存"""
        self._cache.pop(key, None)
        self._hash_cache.pop(key, None)
        self._ttl.pop(key, None)
        return True

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

    def hset(self, name: str, key: str = None, value: str = None, mapping: dict = None) -> bool:
        """设置哈希字段"""
        if name not in self._hash_cache:
            self._hash_cache[name] = {}

        if mapping:
            self._hash_cache[name].update(mapping)
        elif key and value is not None:
            self._hash_cache[name][key] = value
        return True

    def hdel(self, name: str, key: str = None) -> bool:
        """删除哈希字段"""
        if name in self._hash_cache:
            if key:
                self._hash_cache[name].pop(key, None)
            else:
                del self._hash_cache[name]
        return True

    def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        self._ttl[key] = time.time() + seconds
        return True

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        self._check_expired(key)
        return key in self._cache or key in self._hash_cache

    def is_enabled(self) -> bool:
        """缓存是否启用"""
        return True

    def _check_expired(self, key: str):
        """检查并清理过期键"""
        if key in self._ttl and time.time() > self._ttl[key]:
            self.delete(key)


# 全局实例
_redis_manager: Optional[RedisManager] = None


def get_redis() -> RedisManager:
    """获取缓存管理器实例"""
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisManager()
    return _redis_manager
```

**Step 2: 验证语法正确**

Run: `python -m py_compile server/utils/redis_manager.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add server/utils/redis_manager.py
git commit -m "refactor(cache): simplify RedisManager to pure memory implementation

Replace Redis-backed cache with in-memory implementation:
- Keep same class name and interface for backward compatibility
- Support string operations: get, set, delete, exists, expire
- Support hash operations: hget, hgetall, hset, hdel
- Add TTL support with automatic expiration check
- Remove all Redis-specific code (connection, pool, etc.)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: 修改 live_audio_stream_service.py

**Files:**
- Modify: `server/app/services/live_audio_stream_service.py`

**Step 1: 移除 Redis 批量写入逻辑**

查找并移除 `_batch_transcription_worker` 中的 Redis 写入代码，保留内存缓冲和批量处理逻辑：

1. 保留 `_redis_batch_buffer`、`_redis_batch_lock`、`_redis_batch_interval` 变量（只是名称，实际用于内存缓冲）
2. 移除实际的 Redis rpush/hset 调用
3. 保留批量处理框架，只记录日志或触发事件

**Step 2: 验证修改**

Run: `python -m py_compile server/app/services/live_audio_stream_service.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add server/app/services/live_audio_stream_service.py
git commit -m "refactor(live_audio): remove Redis batch write, keep memory buffer

- Remove Redis rpush/hset calls from _batch_transcription_worker
- Keep in-memory batch buffer and processing logic
- Batch processing now logs and clears buffer without Redis

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: 修改 live_session_manager.py

**Files:**
- Modify: `server/app/services/live_session_manager.py`

**Step 1: 移除 Redis 会话缓存**

查找并移除以下方法中的 Redis 调用：
- `save_session_state` - 移除 Redis 同步代码块
- `load_session_state` - 移除 Redis 读取代码块
- `clear_session_state` - 移除 Redis 清除代码块

保留 SQLite 数据库持久化逻辑。

**Step 2: 验证修改**

Run: `python -m py_compile server/app/services/live_session_manager.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add server/app/services/live_session_manager.py
git commit -m "refactor(session): remove Redis session cache, keep SQLite

- Remove Redis sync code from save_session_state
- Remove Redis read code from load_session_state
- Remove Redis clear code from clear_session_state
- SQLite persistence remains unchanged

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: 修改 douyin_web_relay.py

**Files:**
- Modify: `server/app/services/douyin_web_relay.py`

**Step 1: 移除 Redis 弹幕缓存**

1. 移除 `_batch_danmu_worker` 中的 Redis 写入代码
2. 移除 `_update_hotwords_in_redis` 方法（如果存在）
3. 移除 Redis 相关配置变量

**Step 2: 验证修改**

Run: `python -m py_compile server/app/services/douyin_web_relay.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add server/app/services/douyin_web_relay.py
git commit -m "refactor(douyin): remove Redis danmu cache

- Remove Redis writes from _batch_danmu_worker
- Remove _update_hotwords_in_redis method
- Remove Redis config variables

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: 修改 ai_live_analyzer.py

**Files:**
- Modify: `server/app/services/ai_live_analyzer.py`

**Step 1: 移除 Redis AI 缓存**

1. 移除 `_get_cached_analysis` 方法（如果存在 Redis 逻辑）
2. 移除 `_cache_analysis` 方法（如果存在 Redis 逻辑）
3. 移除 `_redis_cache_enabled` 和 `_redis_cache_ttl` 配置

**Step 2: 验证修改**

Run: `python -m py_compile server/app/services/ai_live_analyzer.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add server/app/services/ai_live_analyzer.py
git commit -m "refactor(ai): remove Redis AI analysis cache

- Remove Redis cache logic from _get_cached_analysis
- Remove Redis cache logic from _cache_analysis
- Remove _redis_cache_enabled and _redis_cache_ttl config

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: 修改 main.py 移除 Redis 初始化

**Files:**
- Modify: `server/app/main.py`

**Step 1: 移除 Redis 初始化代码**

查找并移除：
- Redis 连接初始化
- Redis 健康检查
- Redis 相关的 startup/shutdown 事件

**Step 2: 验证修改**

Run: `python -m py_compile server/app/main.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add server/app/main.py
git commit -m "refactor(main): remove Redis initialization

- Remove Redis connection init from startup
- Remove Redis health check
- Remove Redis shutdown cleanup

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: 修改 config.py 移除 RedisConfig

**Files:**
- Modify: `server/config.py`

**Step 1: 移除 RedisConfig 类**

删除 `RedisConfig` 数据类和相关引用。

**Step 2: 验证修改**

Run: `python -m py_compile server/config.py`
Expected: No output (success)

**Step 3: Commit**

```bash
git add server/config.py
git commit -m "refactor(config): remove RedisConfig class

- Remove RedisConfig dataclass
- Remove Redis environment variable parsing

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 8: 更新 requirements.txt

**Files:**
- Modify: `requirements.txt`

**Step 1: 移除 redis 依赖**

删除行：
```
redis>=4.0.0
```

**Step 2: Commit**

```bash
git add requirements.txt
git commit -m "chore(deps): remove redis dependency

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 9: 更新 .env.example

**Files:**
- Modify: `.env.example`

**Step 1: 移除 Redis 配置项**

删除以下配置：
```
REDIS_ENABLED=True
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_MAX_CONNECTIONS=50
REDIS_CACHE_TTL=3600
REDIS_BATCH_ENABLED=1
REDIS_BATCH_SIZE=100
REDIS_BATCH_INTERVAL=10.0
```

**Step 2: Commit**

```bash
git add .env.example
git commit -m "chore(env): remove Redis configuration from .env.example

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 10: 运行测试验证

**Files:**
- Run: All tests

**Step 1: 运行所有测试**

Run: `python -m pytest tests/ -v --tb=short`
Expected: All tests pass (may have some skipped)

**Step 2: 检查导入错误**

Run: `python -c "from server.utils.redis_manager import get_redis; r = get_redis(); print(r.set('test', 'value')); print(r.get('test'))"`
Expected: `True` `value`

**Step 3: 最终 Commit（如有遗漏修复）**

如果有任何遗漏的修复，在此提交。

---

## 执行顺序

Tasks 1-9 可以按顺序执行。Task 10 必须最后执行以验证所有更改。

---

## 回滚方案

如果移除 Redis 后出现问题：

1. `git revert` 恢复到移除前的 commit
2. `pip install redis` 重新安装依赖
3. 从 `.env.example` 恢复 Redis 配置到 `.env`
