# 后端性能优化设计文档

**日期**: 2026-02-19
**作者**: Claude
**状态**: 设计阶段
**目标**: 优化后端性能，降低内存占用，消除阻塞操作

---

## 1. 背景

### 1.1 当前问题

| 问题 | 现状 | 影响 |
|------|------|------|
| 内存占用高 | 2.8-4.2GB（<8GB机器压力大） | PM2重启风险 |
| 线程阻塞 | SenseVoice/AI调用阻塞主线程 | WebSocket卡顿 |
| 异步不足 | 部分同步操作 | CPU利用率低 |

### 1.2 部署场景

- **规模**: 单机小规模（1-2个直播间）
- **硬件**: <8GB内存
- **架构**: 单进程应用（Electron + FastAPI）

### 1.3 优化目标

1. **改进异步处理** - 消除阻塞操作
2. **降低内存使用** - 减少30-40%内存占用
3. **降低语音识别延迟** - 提升用户体验

---

## 2. 技术方案

### 2.1 整体架构

**单进程异步架构**：

```
┌────────────────────────────────────────┐
│  FastAPI Main Process                  │
├────────────────────────────────────────┤
│  Event Loop (asyncio)                  │
│  ├─ WebSocket连接管理                  │
│  ├─ AsyncTaskManager (任务调度)        │
│  └─ 音频流处理主循环                   │
│                                        │
│  ThreadPool (4线程)                    │
│  └─ SenseVoice转录（CPU密集）          │
│                                        │
│  AudioBufferPool (内存池)              │
│  └─ 复用音频缓冲区                     │
│                                        │
│  MemoryMonitor (内存监控)              │
│  └─ 定期GC                             │
└────────────────────────────────────────┘
```

### 2.2 核心优化点

#### 优化1：异步任务管理器

**目标**: 非阻塞处理耗时操作

**实现**:
- 使用 `asyncio.create_task()` 创建后台任务
- 使用 `asyncio.Semaphore` 限制并发数（最多10个）
- 使用 `ThreadPoolExecutor` 处理CPU密集型操作

**关键代码**:

```python
# server/utils/async_task_manager.py
class AsyncTaskManager:
    def __init__(self, max_concurrent_tasks: int = 10):
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self._active_tasks: Dict[str, asyncio.Task] = {}

    async def submit_task(self, task_id: str, coro, callback=None):
        async def wrapped_task():
            async with self._semaphore:
                result = await coro
                if callback:
                    await callback(result)
                return result

        task = asyncio.create_task(wrapped_task())
        self._active_tasks[task_id] = task
        return task
```

**使用场景**:
| 操作 | 处理方式 |
|------|---------|
| SenseVoice转录 | `run_in_executor` → 线程池 |
| AI脚本生成 | `create_task` → 后台协程 |
| 直播复盘分析 | `create_task` → 后台协程 |

---

#### 优化2：音频缓冲区内存池

**目标**: 减少80%内存分配，降低GC压力

**音频数据特点**:
- 固定大小: 1.6秒 × 16kHz × 2字节 = 51.2KB/块
- 高频分配: 每1.6秒产生1块
- 当前问题: 每块新分配 → GC频繁

**实现**:

```python
# server/utils/audio_buffer_pool.py
class AudioBufferPool:
    def __init__(self, buffer_size: int = 25600, pool_size: int = 50):
        self._pool = []  # 空闲缓冲区
        self._lock = threading.Lock()

    def acquire(self) -> np.ndarray:
        with self._lock:
            if self._pool:
                return self._pool.pop()
            return np.zeros(self.buffer_size, dtype=np.int16)

    def release(self, buffer: np.ndarray):
        with self._lock:
            if len(self._pool) < self.pool_size:
                buffer.fill(0)
                self._pool.append(buffer)
```

**使用方式**:

```python
# 原代码（每次新分配）
audio_chunk = np.zeros(25600, dtype=np.int16)

# 新代码（池化复用）
audio_chunk = audio_pool.acquire()
try:
    # 处理音频
finally:
    audio_pool.release(audio_chunk)
```

**预期效果**:
- 命中率: 80-90%
- 内存分配减少: 80-90%
- GC压力降低: 显著

---

#### 优化3：GC优化策略

**Python GC原理**:
- 分代回收（0代、1代、2代）
- 默认阈值: (700, 10, 10)
- 问题: 0代阈值700太小 → 频繁GC

**优化方案**:

```python
# server/app/main.py 启动时
import gc

# 调整GC阈值（减少GC频率）
gc.set_threshold(2000, 20, 20)
```

**增强内存监控**:

```python
# server/app/services/memory_monitor.py
class MemoryMonitor:
    def __init__(self):
        self.warning_threshold = 3.0 * 1024   # 3GB
        self.critical_threshold = 3.5 * 1024  # 3.5GB
        self.check_interval = 60  # 60秒检查

    async def check_and_gc(self):
        mem_mb = psutil.Process().memory_info().rss / 1024 / 1024

        if mem_mb > self.critical_threshold:
            collected = gc.collect()  # 全量GC
            logger.warning(f"Critical memory: {mem_mb:.0f}MB")
        elif mem_mb > self.warning_threshold:
            collected = gc.collect(0)  # 轻量GC
            logger.info(f"Warning memory: {mem_mb:.0f}MB")
```

---

## 3. 错误处理与监控

### 3.1 任务失败处理

| 场景 | 处理策略 |
|------|---------|
| SenseVoice转录失败 | 重试3次，降级为空结果 |
| AI调用失败 | 重试2次，返回错误提示 |
| 任务超时（>30秒） | 强制终止，标记失败 |

**降级策略**:

```python
async def transcribe_audio_async(audio_chunk):
    try:
        result = await loop.run_in_executor(
            thread_pool,
            sensevoice_service.transcribe_sync,
            audio_chunk
        )
        return result
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return {'text': '', 'error': str(e), 'fallback': True}
```

### 3.2 监控端点

**新增API**:

```python
@app.get("/api/health/performance")
async def performance_health():
    return {
        "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
        "buffer_pool": audio_pool.get_stats(),
        "active_tasks": task_manager.get_active_task_count(),
        "gc": {
            "threshold": gc.get_threshold(),
            "count": gc.get_count(),
        }
    }
```

---

## 4. 实施计划

### 4.1 阶段划分

| 阶段 | 内容 | 工期 |
|------|------|------|
| 1. 准备工作 | 创建文件结构 | 0.5天 |
| 2. 内存池实施 | AudioBufferPool + 监控 | 1-2天 |
| 3. 异步任务管理 | AsyncTaskManager + 线程池 | 2-3天 |
| 4. GC优化 | 阈值调整 + 监控增强 | 1天 |
| 5. 测试验证 | 单元测试 + 集成测试 + 压力测试 | 2天 |

**总工期**: 6.5-8.5天

### 4.2 文件变更清单

**新增文件**:
- `server/utils/async_task_manager.py` - 异步任务管理器
- `server/utils/audio_buffer_pool.py` - 音频缓冲区内存池

**修改文件**:
- `server/app/main.py` - GC阈值调整 + 启动监控
- `server/app/services/live_audio_stream_service.py` - 使用内存池 + 异步任务
- `server/app/services/memory_monitor.py` - 增强监控逻辑

**依赖变更**:
- 无新增依赖（全部使用Python内置库）

---

## 5. 测试策略

### 5.1 单元测试

```python
# tests/utils/test_audio_buffer_pool.py
def test_buffer_pool_acquire_release():
    pool = AudioBufferPool(buffer_size=100, pool_size=5)

    buf = pool.acquire()
    assert buf.shape == (100,)
    assert pool.get_stats()['misses'] == 1

    pool.release(buf)
    assert pool.get_stats()['pool_size'] == 1

    buf2 = pool.acquire()
    assert pool.get_stats()['hits'] == 1

def test_buffer_pool_overflow():
    pool = AudioBufferPool(buffer_size=100, pool_size=2)

    bufs = [pool.acquire() for _ in range(3)]
    for buf in bufs:
        pool.release(buf)

    assert pool.get_stats()['pool_size'] == 2
```

### 5.2 内存泄漏测试

```python
def test_memory_leak_after_1000_iterations():
    initial_mem = psutil.Process().memory_info().rss / 1024 / 1024

    for _ in range(1000):
        buf = audio_pool.acquire()
        audio_pool.release(buf)

    gc.collect()
    final_mem = psutil.Process().memory_info().rss / 1024 / 1024

    assert final_mem - initial_mem < 50
```

### 5.3 压力测试

```bash
# 并发2个直播间，持续30分钟
python scripts/stress_test.py --sessions 2 --duration 1800
```

---

## 6. 回滚计划

### 6.1 配置开关

```bash
# .env
ASYNC_TASK_ENABLED=true      # false则同步调用
AUDIO_BUFFER_POOL_ENABLED=true  # false则每次新分配
GC_OPTIMIZATION_ENABLED=true    # false则默认GC
```

### 6.2 回滚操作

| 场景 | 操作 |
|------|------|
| 异步任务有问题 | `ASYNC_TASK_ENABLED=false` |
| 内存池有问题 | `AUDIO_BUFFER_POOL_ENABLED=false` |
| GC调整有问题 | `GC_OPTIMIZATION_ENABLED=false` |

---

## 7. 成功指标

| 指标 | 当前 | 目标 | 验证方式 |
|------|------|------|---------|
| 内存占用 | 2.8-4.2GB | <3.0GB | `/api/health/performance` |
| GC暂停频率 | 高 | <1次/分钟 | 日志监控 |
| 音频缓冲命中率 | 0% | >80% | `/api/health/performance` |
| WebSocket延迟 | 有卡顿 | <100ms | 前端监控 |

---

## 8. 风险评估

| 风险 | 级别 | 缓解措施 |
|------|------|---------|
| 线程池竞争 | 低 | Semaphore限制并发数 |
| 内存池溢出 | 低 | 池满后直接丢弃 |
| GC暂停过长 | 低 | 保守调整阈值 |
| 回归bug | 中 | 配置开关 + 充分测试 |

**总体风险**: 低-中

---

## 9. 参考资料

- [Python GC文档](https://docs.python.org/3/library/gc.html)
- [asyncio官方文档](https://docs.python.org/3/library/asyncio.html)
- [SenseVoice并发优化报告](../SenseVoice并发死锁优化报告.md)
- [内存优化部署指南](../内存优化部署指南.md)
