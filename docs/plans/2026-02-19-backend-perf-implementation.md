# 后端性能优化实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 优化后端性能，降低内存占用30-40%，消除阻塞操作，提升响应速度

**Architecture:** 单进程异步架构，使用 asyncio 原生并发 + ThreadPoolExecutor 处理CPU密集型操作，内存池复用音频缓冲区，调整GC阈值减少暂停

**Tech Stack:** Python asyncio, threading.ThreadPoolExecutor, numpy, gc, psutil (已有)

**设计文档:** `docs/plans/2026-02-19-backend-perf-design.md`

---

## Task 1: 音频缓冲区内存池 - 测试先行

**Files:**
- Create: `tests/utils/__init__.py`
- Create: `tests/utils/test_audio_buffer_pool.py`

### Step 1: 创建测试目录

Run: `mkdir -p tests/utils`
Expected: Directory created

### Step 2: 创建 __init__.py

Create `tests/utils/__init__.py`:

```python
# -*- coding: utf-8 -*-
"""Tests for server/utils modules"""
```

### Step 3: 编写 AudioBufferPool 单元测试

Create `tests/utils/test_audio_buffer_pool.py`:

```python
# -*- coding: utf-8 -*-
"""AudioBufferPool 单元测试"""

import pytest
import numpy as np


class TestAudioBufferPool:
    """AudioBufferPool 测试用例"""

    def test_acquire_creates_new_buffer(self):
        """测试首次获取创建新缓冲区"""
        # 在测试内部导入，避免模块不存在时导入失败
        from server.utils.audio_buffer_pool import AudioBufferPool

        pool = AudioBufferPool(buffer_size=100, pool_size=5)

        buf = pool.acquire()

        assert buf.shape == (100,)
        assert buf.dtype == np.int16
        stats = pool.get_stats()
        assert stats['misses'] == 1
        assert stats['hits'] == 0

    def test_release_returns_buffer_to_pool(self):
        """测试归还缓冲区进入池"""
        from server.utils.audio_buffer_pool import AudioBufferPool

        pool = AudioBufferPool(buffer_size=100, pool_size=5)
        buf = pool.acquire()

        pool.release(buf)

        stats = pool.get_stats()
        assert stats['pool_size'] == 1

    def test_acquire_reuses_released_buffer(self):
        """测试获取复用已归还的缓冲区"""
        from server.utils.audio_buffer_pool import AudioBufferPool

        pool = AudioBufferPool(buffer_size=100, pool_size=5)
        buf1 = pool.acquire()
        pool.release(buf1)

        buf2 = pool.acquire()

        stats = pool.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1

    def test_pool_overflow_drops_excess_buffers(self):
        """测试池满后丢弃多余缓冲区"""
        from server.utils.audio_buffer_pool import AudioBufferPool

        pool = AudioBufferPool(buffer_size=100, pool_size=2)

        bufs = [pool.acquire() for _ in range(3)]

        for buf in bufs:
            pool.release(buf)

        stats = pool.get_stats()
        assert stats['pool_size'] == 2  # 只保留2个

    def test_released_buffer_is_cleared(self):
        """测试归还的缓冲区被清空"""
        from server.utils.audio_buffer_pool import AudioBufferPool

        pool = AudioBufferPool(buffer_size=100, pool_size=5)
        buf = pool.acquire()
        buf.fill(42)  # 填充非零值

        pool.release(buf)
        buf2 = pool.acquire()  # 应该获取同一个

        assert np.all(buf2 == 0)  # 应该被清空

    def test_get_stats_returns_correct_info(self):
        """测试统计信息正确"""
        from server.utils.audio_buffer_pool import AudioBufferPool

        pool = AudioBufferPool(buffer_size=100, pool_size=5)

        buf1 = pool.acquire()
        buf2 = pool.acquire()
        pool.release(buf1)

        buf3 = pool.acquire()  # hit

        stats = pool.get_stats()

        assert stats['hits'] == 1
        assert stats['misses'] == 2
        assert stats['pool_size'] == 0
        assert 'hit_rate' in stats
```

### Step 4: 运行测试确认失败

Run: `pytest tests/utils/test_audio_buffer_pool.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'server.utils.audio_buffer_pool'"

### Step 5: 提交测试文件

```bash
git add tests/utils/__init__.py tests/utils/test_audio_buffer_pool.py
git commit -m "test: add AudioBufferPool unit tests

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 2: 实现 AudioBufferPool

**Files:**
- Create: `server/utils/audio_buffer_pool.py`

### Step 1: 实现 AudioBufferPool

Create `server/utils/audio_buffer_pool.py`:

```python
# -*- coding: utf-8 -*-
"""
音频缓冲区内存池
复用固定大小的numpy数组，减少内存分配和GC压力
"""

import threading
from typing import Dict, Any
import logging

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

logger = logging.getLogger(__name__)


class AudioBufferPool:
    """
    音频缓冲区对象池

    用于复用固定大小的numpy数组，减少频繁的内存分配和GC压力。

    使用示例:
        pool = AudioBufferPool(buffer_size=25600, pool_size=50)

        buf = pool.acquire()
        try:
            # 使用 buf 处理音频数据
            buf[:] = audio_data
        finally:
            pool.release(buf)
    """

    def __init__(self, buffer_size: int = 25600, pool_size: int = 50):
        """
        初始化音频缓冲区池

        Args:
            buffer_size: 单个缓冲区大小（样本数）
                默认 25600 = 1.6秒 * 16kHz
            pool_size: 池大小（保留的缓冲区数量）
                默认 50 个 ≈ 2.5MB
        """
        if np is None:
            raise ImportError("numpy is required for AudioBufferPool")

        self.buffer_size = buffer_size
        self.pool_size = pool_size
        self._pool: list = []  # 空闲缓冲区列表
        self._lock = threading.Lock()
        self._stats: Dict[str, int] = {
            'hits': 0,       # 命中次数（从池中获取）
            'misses': 0,     # 未命中次数（新分配）
            'total_allocs': 0  # 总分配次数
        }

        logger.info(
            f"AudioBufferPool 初始化: buffer_size={buffer_size}, "
            f"pool_size={pool_size}, "
            f"单块大小={buffer_size * 2 / 1024:.1f}KB"
        )

    def acquire(self) -> "np.ndarray":
        """
        获取一个缓冲区

        如果池中有空闲缓冲区则复用，否则分配新的。

        Returns:
            numpy.ndarray: 形状为 (buffer_size,) 的 int16 数组
        """
        with self._lock:
            if self._pool:
                self._stats['hits'] += 1
                return self._pool.pop()
            else:
                self._stats['misses'] += 1
                self._stats['total_allocs'] += 1
                return np.zeros(self.buffer_size, dtype=np.int16)

    def release(self, buffer: "np.ndarray") -> None:
        """
        释放缓冲区（归还到池）

        如果池未满，清空数据后归还；否则直接丢弃（让GC回收）。

        Args:
            buffer: 要释放的缓冲区
        """
        with self._lock:
            if len(self._pool) < self.pool_size:
                # 清空数据
                buffer.fill(0)
                self._pool.append(buffer)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取池统计信息

        Returns:
            包含 hits, misses, hit_rate, pool_size 等字段的字典
        """
        with self._lock:
            total = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total if total > 0 else 0.0
            return {
                **self._stats,
                'hit_rate': f"{hit_rate:.1%}",
                'pool_size': len(self._pool),
                'max_pool_size': self.pool_size,
            }

    def clear(self) -> int:
        """
        清空池中所有缓冲区

        Returns:
            清除的缓冲区数量
        """
        with self._lock:
            count = len(self._pool)
            self._pool.clear()
            return count


# 全局单例（延迟初始化）
_audio_pool: AudioBufferPool = None  # type: ignore
_pool_lock = threading.Lock()


def get_audio_pool(
    buffer_size: int = 25600,
    pool_size: int = 50,
    force_reinit: bool = False
) -> AudioBufferPool:
    """
    获取全局音频缓冲区池单例

    Args:
        buffer_size: 缓冲区大小（样本数）
        pool_size: 池大小
        force_reinit: 是否强制重新初始化

    Returns:
        AudioBufferPool 实例
    """
    global _audio_pool

    if _audio_pool is None or force_reinit:
        with _pool_lock:
            if _audio_pool is None or force_reinit:
                _audio_pool = AudioBufferPool(
                    buffer_size=buffer_size,
                    pool_size=pool_size
                )

    return _audio_pool


# 便捷别名
audio_pool = property(lambda self: get_audio_pool())
```

### Step 2: 运行测试确认通过

Run: `pytest tests/utils/test_audio_buffer_pool.py -v`
Expected: All tests PASS

### Step 3: 提交实现

```bash
git add server/utils/audio_buffer_pool.py
git commit -m "feat: add AudioBufferPool for memory optimization

- Pool numpy arrays to reduce memory allocation
- Support acquire/release pattern
- Track hit/miss statistics

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 3: 异步任务管理器 - 测试先行

**Files:**
- Create: `tests/utils/test_async_task_manager.py`

### Step 1: 编写 AsyncTaskManager 单元测试

Create `tests/utils/test_async_task_manager.py`:

```python
# -*- coding: utf-8 -*-
"""AsyncTaskManager 单元测试"""

import pytest
import asyncio


class TestAsyncTaskManager:
    """AsyncTaskManager 测试用例"""

    @pytest.mark.asyncio
    async def test_submit_task_returns_task(self):
        """测试提交任务返回Task对象"""
        from server.utils.async_task_manager import AsyncTaskManager

        manager = AsyncTaskManager(max_concurrent_tasks=5)

        async def simple_task():
            return 42

        task = await manager.submit_task("test-1", simple_task())

        assert isinstance(task, asyncio.Task)

    @pytest.mark.asyncio
    async def test_task_executes_and_returns_result(self):
        """测试任务执行并返回结果"""
        from server.utils.async_task_manager import AsyncTaskManager

        manager = AsyncTaskManager(max_concurrent_tasks=5)

        async def compute():
            return 1 + 1

        task = await manager.submit_task("test-2", compute())
        result = await task

        assert result == 2

    @pytest.mark.asyncio
    async def test_callback_is_called_on_completion(self):
        """测试任务完成后调用回调"""
        from server.utils.async_task_manager import AsyncTaskManager

        manager = AsyncTaskManager(max_concurrent_tasks=5)
        callback_result = []

        async def my_task():
            return "done"

        async def callback(result):
            callback_result.append(result)

        await manager.submit_task("test-3", my_task(), callback=callback)

        # 等待任务完成
        await asyncio.sleep(0.1)

        assert callback_result == ["done"]

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self):
        """测试信号量限制并发数"""
        from server.utils.async_task_manager import AsyncTaskManager

        manager = AsyncTaskManager(max_concurrent_tasks=2)
        concurrent_count = 0
        max_concurrent = 0

        async def counting_task():
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.05)
            concurrent_count -= 1
            return concurrent_count

        # 提交5个任务
        tasks = []
        for i in range(5):
            task = await manager.submit_task(f"test-{i}", counting_task())
            tasks.append(task)

        # 等待所有任务完成
        await asyncio.gather(*tasks)

        assert max_concurrent <= 2

    @pytest.mark.asyncio
    async def test_get_active_task_count(self):
        """测试获取活跃任务数"""
        from server.utils.async_task_manager import AsyncTaskManager

        manager = AsyncTaskManager(max_concurrent_tasks=5)

        async def slow_task():
            await asyncio.sleep(0.1)
            return "done"

        # 提交2个任务
        await manager.submit_task("test-1", slow_task())
        await manager.submit_task("test-2", slow_task())

        # 立即检查（任务还在执行）
        count = manager.get_active_task_count()
        assert count == 2

        # 等待完成
        await asyncio.sleep(0.2)

        count = manager.get_active_task_count()
        assert count == 0
```

### Step 2: 运行测试确认失败

Run: `pytest tests/utils/test_async_task_manager.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'server.utils.async_task_manager'"

### Step 3: 提交测试文件

```bash
git add tests/utils/test_async_task_manager.py
git commit -m "test: add AsyncTaskManager unit tests

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: 实现 AsyncTaskManager

**Files:**
- Create: `server/utils/async_task_manager.py`

### Step 1: 实现 AsyncTaskManager

Create `server/utils/async_task_manager.py`:

```python
# -*- coding: utf-8 -*-
"""
异步任务管理器
在单进程内管理异步任务，限制并发数，支持回调
"""

import asyncio
from typing import Dict, Any, Callable, Optional, Coroutine
import logging

logger = logging.getLogger(__name__)


class AsyncTaskManager:
    """
    单机异步任务管理器

    在主进程内管理异步任务，使用 Semaphore 限制并发数。
    适用于单机应用场景，无需独立 worker 进程。

    使用示例:
        manager = AsyncTaskManager(max_concurrent_tasks=10)

        async def my_task():
            await asyncio.sleep(1)
            return "done"

        async def on_complete(result):
            print(f"Task completed: {result}")

        task = await manager.submit_task("task-1", my_task(), callback=on_complete)
    """

    def __init__(self, max_concurrent_tasks: int = 10):
        """
        初始化异步任务管理器

        Args:
            max_concurrent_tasks: 最大并发任务数
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._task_counter = 0

        logger.info(
            f"AsyncTaskManager 初始化: max_concurrent_tasks={max_concurrent_tasks}"
        )

    async def submit_task(
        self,
        task_id: str,
        coro: Coroutine,
        callback: Optional[Callable[[Any], Coroutine]] = None
    ) -> asyncio.Task:
        """
        提交异步任务

        Args:
            task_id: 任务唯一标识
            coro: 协程对象
            callback: 完成回调（可选）

        Returns:
            asyncio.Task 对象
        """
        async def wrapped_task():
            async with self._semaphore:
                try:
                    result = await coro
                    if callback:
                        try:
                            await callback(result)
                        except Exception as e:
                            logger.error(f"Callback failed for task {task_id}: {e}")
                    return result
                except Exception as e:
                    logger.error(f"Task {task_id} failed: {e}")
                    raise
                finally:
                    self._active_tasks.pop(task_id, None)

        task = asyncio.create_task(wrapped_task())
        self._active_tasks[task_id] = task
        self._task_counter += 1

        logger.debug(f"Task submitted: {task_id}, active={len(self._active_tasks)}")
        return task

    async def get_task_result(
        self,
        task_id: str,
        timeout: float = 30.0
    ) -> Any:
        """
        获取任务结果

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）

        Returns:
            任务结果

        Raises:
            ValueError: 任务不存在
            asyncio.TimeoutError: 超时
        """
        task = self._active_tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        return await asyncio.wait_for(task, timeout=timeout)

    def get_active_task_count(self) -> int:
        """
        获取活跃任务数

        Returns:
            当前正在执行的任务数
        """
        return len(self._active_tasks)

    def get_active_task_ids(self) -> list:
        """
        获取所有活跃任务ID

        Returns:
            任务ID列表
        """
        return list(self._active_tasks.keys())

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            包含活跃任务数、最大并发数等信息的字典
        """
        return {
            'active_tasks': len(self._active_tasks),
            'max_concurrent': self.max_concurrent_tasks,
            'total_submitted': self._task_counter,
        }

    async def cancel_all(self) -> int:
        """
        取消所有活跃任务

        Returns:
            取消的任务数
        """
        count = 0
        for task_id, task in list(self._active_tasks.items()):
            if not task.done():
                task.cancel()
                count += 1
                logger.info(f"Task cancelled: {task_id}")

        return count


# 全局单例
_task_manager: Optional[AsyncTaskManager] = None


def get_task_manager(max_concurrent_tasks: int = 10) -> AsyncTaskManager:
    """
    获取全局任务管理器单例

    Args:
        max_concurrent_tasks: 最大并发任务数

    Returns:
        AsyncTaskManager 实例
    """
    global _task_manager

    if _task_manager is None:
        _task_manager = AsyncTaskManager(max_concurrent_tasks=max_concurrent_tasks)

    return _task_manager
```

### Step 2: 运行测试确认通过

Run: `pytest tests/utils/test_async_task_manager.py -v`
Expected: All tests PASS

### Step 3: 提交实现

```bash
git add server/utils/async_task_manager.py
git commit -m "feat: add AsyncTaskManager for non-blocking operations

- Manage async tasks with semaphore concurrency control
- Support completion callbacks
- Track active tasks and statistics

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: GC 优化和性能监控端点

**Files:**
- Modify: `server/app/main.py` (添加GC优化启动)
- Modify: `server/app/services/memory_monitor.py` (增强监控)
- Create: `tests/test_gc_optimization.py`

### Step 1: 编写 GC 优化测试

Create `tests/test_gc_optimization.py`:

```python
# -*- coding: utf-8 -*-
"""GC 优化测试"""

import gc
import pytest


class TestGCOptimization:
    """GC 优化测试用例"""

    def test_gc_threshold_is_adjusted(self):
        """测试 GC 阈值已调整"""
        # 导入 main 模块会触发 GC 优化
        from server.app.main import app

        threshold = gc.get_threshold()

        # 阈值应该大于默认值 (700, 10, 10)
        assert threshold[0] >= 2000, f"0代阈值应该>=2000, 实际={threshold[0]}"
        assert threshold[1] >= 20, f"1代阈值应该>=20, 实际={threshold[1]}"
        assert threshold[2] >= 20, f"2代阈值应该>=20, 实际={threshold[2]}"

    def test_gc_collect_works(self):
        """测试手动 GC 正常工作"""
        # 创建一些临时对象
        _ = [i for i in range(10000)]

        collected = gc.collect()

        assert isinstance(collected, int)
        assert collected >= 0
```

### Step 2: 修改 main.py 添加 GC 优化

Edit `server/app/main.py`, 在文件顶部的 import 区域后添加:

```python
# 在 import 语句后添加 (约第14行后)
# ========== GC 优化 ==========
import gc

# 调整 GC 阈值（减少 GC 暂停频率）
# 默认: (700, 10, 10) → 优化后: (2000, 20, 20)
# 0代阈值从700提高到2000，减少触发频率
_gc_threshold = gc.get_threshold()
if os.getenv("GC_OPTIMIZATION_ENABLED", "true").lower() != "false":
    gc.set_threshold(2000, 20, 20)
    logging.info(f"🔧 GC 阈值优化: {_gc_threshold} → {gc.get_threshold()}")
else:
    logging.info(f"⏭️ GC 优化已禁用，使用默认阈值: {_gc_threshold}")
```

### Step 3: 运行 GC 测试

Run: `pytest tests/test_gc_optimization.py -v`
Expected: Tests PASS

### Step 4: 提交 GC 优化

```bash
git add server/app/main.py tests/test_gc_optimization.py
git commit -m "feat: add GC threshold optimization

- Increase GC thresholds to reduce pause frequency
- Add environment variable to disable optimization
- Add tests for GC optimization

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: 增强内存监控服务

**Files:**
- Modify: `server/app/services/memory_monitor.py`

### Step 1: 修改内存监控阈值和检查间隔

Edit `server/app/services/memory_monitor.py`, 修改 `MemoryMonitorState` 类 (约第34-42行):

```python
@dataclass
class MemoryMonitorState:
    """内存监控状态"""
    enabled: bool = True
    check_interval_sec: int = 60  # 改为60秒检查一次（原300秒）
    warning_threshold_mb: float = 3072  # 3GB警告（原3500）
    critical_threshold_mb: float = 3584  # 3.5GB严重警告（原4000）
    gc_count: int = 0
    snapshots: List[MemorySnapshot] = field(default_factory=list)
    max_snapshots: int = 100  # 最多保留100个快照
```

### Step 2: 增强 _perform_gc 方法

Edit `server/app/services/memory_monitor.py`, 修改 `_perform_gc` 方法 (约第157-174行):

```python
    async def _perform_gc(self):
        """执行垃圾回收"""
        try:
            # 获取当前内存
            if psutil:
                process = psutil.Process()
                mem_before = process.memory_info().rss / 1024 / 1024
            else:
                mem_before = 0

            logger.info(f"🧹 开始执行垃圾回收... (当前内存: {mem_before:.0f}MB)")

            # 在线程池中执行GC，避免阻塞事件循环
            loop = asyncio.get_event_loop()
            collected = await loop.run_in_executor(None, gc.collect)

            self._state.gc_count += 1

            # GC后再次检查内存
            if psutil:
                process = psutil.Process()
                mem_after = process.memory_info().rss / 1024 / 1024
                freed = mem_before - mem_after
                logger.info(
                    f"✅ 垃圾回收完成: 回收 {collected} 个对象, "
                    f"释放 {freed:.0f}MB, 当前内存: {mem_after:.0f}MB "
                    f"(GC次数: {self._state.gc_count})"
                )
        except Exception as e:
            logger.error(f"执行垃圾回收失败: {e}")
```

### Step 3: 添加内存池状态到监控

Edit `server/app/services/memory_monitor.py`, 在 `get_status` 方法中添加内存池状态 (约第176-205行):

在 `get_status` 方法的 return 语句前添加:

```python
    def get_status(self) -> Dict[str, Any]:
        """获取内存监控状态"""
        # ... 现有代码 ...

        # 新增：获取内存池状态
        pool_stats = None
        try:
            from server.utils.audio_buffer_pool import get_audio_pool
            pool = get_audio_pool()
            pool_stats = pool.get_stats()
        except Exception as e:
            logger.debug(f"获取内存池状态失败: {e}")

        return {
            "enabled": self._state.enabled,
            "check_interval_sec": self._state.check_interval_sec,
            "warning_threshold_mb": self._state.warning_threshold_mb,
            "critical_threshold_mb": self._state.critical_threshold_mb,
            "gc_count": self._state.gc_count,
            "snapshots_count": len(self._state.snapshots),
            "current_memory": current_memory,
            "buffer_pool": pool_stats,  # 新增
        }
```

### Step 4: 提交内存监控增强

```bash
git add server/app/services/memory_monitor.py
git commit -m "feat: enhance memory monitoring

- Reduce check interval to 60s for faster response
- Lower thresholds (3GB warning, 3.5GB critical)
- Log memory freed by GC
- Add buffer pool stats to monitoring

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: 添加性能监控 API 端点

**Files:**
- Modify: `server/app/main.py`

### Step 1: 添加性能监控端点

Edit `server/app/main.py`, 在 health_check 端点后添加 (约第390行后):

```python
@app.get("/api/health/performance")
async def performance_health():
    """
    性能健康检查端点

    返回内存、GC、缓冲池、任务队列等性能指标
    """
    import gc

    result = {
        "status": "healthy",
        "memory": None,
        "gc": None,
        "buffer_pool": None,
        "task_manager": None,
    }

    # 内存信息
    try:
        import psutil
        process = psutil.Process()
        mem_info = process.memory_info()
        result["memory"] = {
            "rss_mb": round(mem_info.rss / 1024 / 1024, 2),
            "vms_mb": round(mem_info.vms / 1024 / 1024, 2),
            "percent": round(process.memory_percent(), 2),
        }

        # 判断健康状态
        if mem_info.rss / 1024 / 1024 > 3584:  # 3.5GB
            result["status"] = "critical"
        elif mem_info.rss / 1024 / 1024 > 3072:  # 3GB
            result["status"] = "warning"
    except Exception as e:
        result["memory"] = {"error": str(e)}

    # GC 信息
    try:
        result["gc"] = {
            "threshold": gc.get_threshold(),
            "count": gc.get_count(),
            "enabled": gc.isenabled(),
        }
    except Exception as e:
        result["gc"] = {"error": str(e)}

    # 缓冲池信息
    try:
        from server.utils.audio_buffer_pool import get_audio_pool
        pool = get_audio_pool()
        result["buffer_pool"] = pool.get_stats()
    except Exception as e:
        result["buffer_pool"] = {"error": str(e)}

    # 任务管理器信息
    try:
        from server.utils.async_task_manager import get_task_manager
        manager = get_task_manager()
        result["task_manager"] = manager.get_stats()
    except Exception as e:
        result["task_manager"] = {"error": str(e)}

    return result
```

### Step 2: 测试端点

Run: `curl http://localhost:11111/api/health/performance`
Expected: JSON with memory, gc, buffer_pool, task_manager fields

### Step 3: 提交端点

```bash
git add server/app/main.py
git commit -m "feat: add /api/health/performance endpoint

- Return memory, GC, buffer pool, task manager stats
- Include health status based on memory thresholds

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 8: 添加配置开关

**Files:**
- Modify: `server/config.py`

### Step 1: 添加性能优化配置

Edit `server/config.py`, 在配置类中添加性能优化开关。先查看现有配置结构：

Run: `head -100 server/config.py`

在合适的配置类中添加:

```python
@dataclass
class PerformanceConfig:
    """性能优化配置"""
    # 内存池
    audio_buffer_pool_enabled: bool = True
    audio_buffer_pool_size: int = 50
    audio_buffer_size: int = 25600  # 1.6s * 16kHz

    # 异步任务
    async_task_enabled: bool = True
    max_concurrent_tasks: int = 10

    # GC 优化
    gc_optimization_enabled: bool = True
    gc_threshold_0: int = 2000
    gc_threshold_1: int = 20
    gc_threshold_2: int = 20
```

### Step 2: 提交配置

```bash
git add server/config.py
git commit -m "feat: add PerformanceConfig for feature toggles

- Add config for buffer pool, async tasks, GC optimization
- Support disabling features via config

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 9: 集成测试

**Files:**
- Create: `tests/integration/test_performance.py`

### Step 1: 创建集成测试

Create `tests/integration/test_performance.py`:

```python
# -*- coding: utf-8 -*-
"""性能优化集成测试"""

import pytest
import asyncio
import gc
import psutil


class TestPerformanceIntegration:
    """性能集成测试"""

    @pytest.mark.asyncio
    async def test_buffer_pool_reduces_memory_allocation(self):
        """测试缓冲池减少内存分配"""
        from server.utils.audio_buffer_pool import get_audio_pool

        pool = get_audio_pool(buffer_size=25600, pool_size=50, force_reinit=True)

        process = psutil.Process()
        initial_mem = process.memory_info().rss / 1024 / 1024

        # 模拟1000次获取/释放
        for _ in range(1000):
            buf = pool.acquire()
            # 模拟处理
            buf[0] = 1
            pool.release(buf)

        # 强制GC
        gc.collect()

        final_mem = process.memory_info().rss / 1024 / 1024
        mem_growth = final_mem - initial_mem

        stats = pool.get_stats()

        # 内存增长应该很小（<50MB）
        assert mem_growth < 50, f"Memory grew by {mem_growth}MB"

        # 命中率应该很高
        hit_rate = float(stats['hit_rate'].rstrip('%')) / 100
        assert hit_rate > 0.8, f"Hit rate {hit_rate} is too low"

    @pytest.mark.asyncio
    async def test_task_manager_handles_concurrency(self):
        """测试任务管理器处理并发"""
        from server.utils.async_task_manager import get_task_manager

        manager = get_task_manager(max_concurrent_tasks=5)

        execution_order = []

        async def tracked_task(task_id: int):
            execution_order.append(f"start-{task_id}")
            await asyncio.sleep(0.05)
            execution_order.append(f"end-{task_id}")
            return task_id

        # 提交10个任务
        tasks = []
        for i in range(10):
            task = await manager.submit_task(f"task-{i}", tracked_task(i))
            tasks.append(task)

        # 等待完成
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert set(results) == set(range(10))

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_valid_data(self):
        """测试健康检查端点返回有效数据"""
        from server.app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        response = client.get("/api/health/performance")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "memory" in data
        assert "gc" in data
        assert "buffer_pool" in data
        assert "task_manager" in data
```

### Step 2: 运行集成测试

Run: `pytest tests/integration/test_performance.py -v`
Expected: All tests PASS

### Step 3: 提交集成测试

```bash
git add tests/integration/test_performance.py
git commit -m "test: add performance integration tests

- Test buffer pool reduces memory allocation
- Test task manager handles concurrency
- Test health endpoint returns valid data

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 10: 文档更新和最终验证

### Step 1: 运行所有测试

Run: `pytest tests/ -v --tb=short`
Expected: All tests PASS

### Step 2: 运行后端服务验证

Run: `npm run dev:backend`

In another terminal:
Run: `curl http://localhost:11111/api/health/performance`

Expected: JSON with healthy status and all metrics

### Step 3: 提交最终更改

```bash
git add -A
git commit -m "docs: complete backend performance optimization

- AudioBufferPool for memory reuse
- AsyncTaskManager for non-blocking operations
- GC threshold optimization
- Enhanced memory monitoring
- Performance health endpoint

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## 验收清单

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] `/api/health/performance` 端点正常工作
- [ ] 内存占用下降（运行30分钟后检查）
- [ ] 缓冲池命中率 > 80%
- [ ] GC 暂停频率降低
- [ ] 无回归 bug

## 回滚方案

如遇问题，可通过环境变量禁用各功能：

```bash
# .env
GC_OPTIMIZATION_ENABLED=false
AUDIO_BUFFER_POOL_ENABLED=false
ASYNC_TASK_ENABLED=false
```
