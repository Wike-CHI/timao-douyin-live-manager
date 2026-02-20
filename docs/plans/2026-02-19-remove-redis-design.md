# 移除 Redis 依赖设计文档

**日期**: 2026-02-19
**作者**: Claude
**状态**: 设计阶段
**目标**: 完全移除 Redis 依赖，保留内存缓存和批量处理功能

---

## 1. 背景

### 1.1 当前状态

项目使用 Redis 作为可选缓存层，包含完善的内存回退机制：
- Redis 默认启用 (`REDIS_ENABLED=True`)
- 当 Redis 不可用时，自动回退到内存缓存
- Redis 用于：转写结果缓存、会话状态缓存、弹幕数据缓存、AI 分析缓存

### 1.2 移除原因

- 简化部署依赖
- 减少运维复杂度
- 单机应用不需要 Redis 的高性能特性

### 1.3 约束条件

- ✅ 保留批量处理逻辑
- ✅ 保留内存缓存功能
- ✅ 保持 API 接口兼容

---

## 2. 技术方案

### 2.1 整体策略

**简化 Redis 管理器为纯内存实现**，保持接口兼容性，最小化代码改动。

### 2.2 文件改动清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `server/utils/redis_manager.py` | 简化 | 保留类名和接口，删除 Redis 逻辑 |
| `server/app/services/live_audio_stream_service.py` | 修改 | 移除 Redis 批量写入，保留内存缓冲 |
| `server/app/services/live_session_manager.py` | 修改 | 移除 Redis 会话缓存 |
| `server/app/services/douyin_web_relay.py` | 修改 | 移除 Redis 弹幕缓存 |
| `server/app/services/ai_live_analyzer.py` | 修改 | 移除 Redis AI 缓存 |
| `server/app/main.py` | 修改 | 移除 Redis 初始化 |
| `server/config.py` | 修改 | 移除 RedisConfig |
| `requirements.txt` | 修改 | 移除 redis 依赖 |
| `.env` / `.env.example` | 修改 | 移除 Redis 配置项 |

---

## 3. 详细设计

### 3.1 简化 redis_manager.py

**保留**：
- 类名 `RedisManager`（保持接口兼容）
- 基本方法签名

**删除**：
- `redis.Redis` 连接代码
- Redis 特有方法：`rpush`, `lpush`, `zadd`, `sadd`, `smembers` 等
- 连接池配置

**简化后的接口**：

```python
# server/utils/redis_manager.py
"""内存缓存管理器（已移除 Redis 依赖）"""

from typing import Any, Dict, Optional, List
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
        return self._hash_cache.get(name, {})

    def hset(self, name: str, key: str = None, value: str = None, mapping: dict = None) -> bool:
        """设置哈希字段"""
        if name not in self._hash_cache:
            self._hash_cache[name] = {}

        if mapping:
            self._hash_cache[name].update(mapping)
        elif key and value is not None:
            self._hash_cache[name][key] = value
        return True

    def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        self._ttl[key] = time.time() + seconds
        return True

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

### 3.2 服务文件修改

#### live_audio_stream_service.py

**移除**：
- `_batch_transcription_worker` 中的 Redis 写入

**修改后**：
```python
async def _batch_transcription_worker(self):
    """将缓冲的转写结果批量处理"""
    while True:
        await asyncio.sleep(self._redis_batch_interval)

        async with self._redis_batch_lock:
            if not self._redis_batch_buffer:
                continue
            batch_to_write = self._redis_batch_buffer.copy()
            self._redis_batch_buffer.clear()

        # 处理转写结果（不再写入 Redis）
        self.logger.info(f"批量处理: {len(batch_to_write)}条转写记录")
```

#### live_session_manager.py

**移除**：
- `save_session_state` 中的 Redis 同步代码块
- `load_session_state` 中的 Redis 读取代码块
- `clear_session_state` 中的 Redis 清除代码块

#### douyin_web_relay.py

**移除**：
- `_batch_danmu_worker` 中的 Redis 写入
- `_update_hotwords_in_redis` 方法
- Redis 相关配置变量

#### ai_live_analyzer.py

**移除**：
- `_get_cached_analysis` 方法
- `_cache_analysis` 方法
- `_redis_cache_enabled` 和 `_redis_cache_ttl` 配置

### 3.3 配置修改

#### server/config.py

删除 `RedisConfig` 类和相关引用。

#### requirements.txt

删除：
```
redis>=4.0.0
```

#### .env.example

删除 Redis 相关配置项：
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

---

## 4. 实施步骤

1. **简化 redis_manager.py**
2. **修改 live_audio_stream_service.py**
3. **修改 live_session_manager.py**
4. **修改 douyin_web_relay.py**
5. **修改 ai_live_analyzer.py**
6. **修改 main.py**
7. **修改 config.py**
8. **更新 requirements.txt**
9. **更新 .env.example**
10. **运行测试验证**

---

## 5. 回滚方案

如果移除 Redis 后出现问题：

1. `git revert` 恢复到移除前的 commit
2. `pip install redis` 重新安装依赖
3. 从 `.env.example` 恢复 Redis 配置到 `.env`

---

## 6. 风险评估

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 接口不兼容 | 低 | 保持类名和方法签名 |
| 内存溢出 | 中 | 保留 TTL 机制 |
| 回归 bug | 中 | 充分测试 |

**总体风险**：低-中
