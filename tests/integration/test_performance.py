# -*- coding: utf-8 -*-
"""
性能优化集成测试

测试缓冲池、任务管理器和健康检查端点的集成功能。
"""

import gc
import os
import sys
import pytest
import asyncio
import numpy as np

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


class TestBufferPoolMemoryAllocation:
    """测试缓冲池减少内存分配"""

    def test_buffer_pool_reduces_memory_allocation(self):
        """
        测试缓冲池减少内存分配

        模拟 1000 次 acquire/release，验证：
        - 内存增长 < 50MB
        - 命中率 > 80%
        """
        from server.utils.audio_buffer_pool import AudioBufferPool

        # 强制 GC 回收，获取基准内存
        gc.collect()
        try:
            import psutil
            process = psutil.Process()
            initial_memory_mb = process.memory_info().rss / 1024 / 1024
        except ImportError:
            initial_memory_mb = 0

        # 创建缓冲池
        pool = AudioBufferPool(buffer_size=25600, max_pool_size=50)

        # 模拟 1000 次 acquire/release
        iterations = 1000
        buffers = []

        for _ in range(iterations):
            buffer = pool.acquire()
            # 模拟使用缓冲区
            buffer[0] = 0.5
            buffers.append(buffer)

            # 每获取 10 个就释放 10 个，模拟实际使用
            if len(buffers) >= 10:
                for buf in buffers:
                    pool.release(buf)
                buffers.clear()

        # 释放剩余的缓冲区
        for buf in buffers:
            pool.release(buf)

        # 强制 GC 后检查内存增长
        gc.collect()

        try:
            import psutil
            final_memory_mb = process.memory_info().rss / 1024 / 1024
            memory_growth_mb = final_memory_mb - initial_memory_mb

            # 验证内存增长 < 50MB
            assert memory_growth_mb < 50, f"内存增长过高: {memory_growth_mb:.2f}MB (应 < 50MB)"
        except ImportError:
            pass  # 如果没有 psutil，跳过内存检查

        # 验证命中率 > 80%
        stats = pool.get_stats()
        hit_rate_str = stats['hit_rate']  # 如 "80.0%"
        hit_rate_pct = float(hit_rate_str.replace('%', ''))

        assert hit_rate_pct > 80, f"命中率过低: {hit_rate_str} (应 > 80%)"
        print(f"Buffer pool stats: hits={stats['hits']}, misses={stats['misses']}, hit_rate={hit_rate_str}")


class TestTaskManagerConcurrency:
    """测试任务管理器处理并发"""

    @pytest.mark.asyncio
    async def test_task_manager_handles_concurrency(self):
        """
        测试任务管理器处理并发

        提交 10 个任务，验证：
        - 并发限制生效
        - 所有任务完成
        """
        from server.utils.async_task_manager import AsyncTaskManager

        max_concurrent = 3
        manager = AsyncTaskManager(max_concurrent=max_concurrent)

        # 并发计数器
        concurrent_count = 0
        max_observed_concurrency = 0
        lock = asyncio.Lock()
        task_results = []

        async def concurrent_task(task_id: int):
            nonlocal concurrent_count, max_observed_concurrency

            async with lock:
                concurrent_count += 1
                if concurrent_count > max_observed_concurrency:
                    max_observed_concurrency = concurrent_count

            # 模拟工作负载
            await asyncio.sleep(0.05)

            async with lock:
                concurrent_count -= 1

            return task_id

        # 提交 10 个任务
        num_tasks = 10
        tasks = [manager.submit(concurrent_task(i)) for i in range(num_tasks)]

        # 等待所有任务完成
        results = await asyncio.gather(*tasks)

        # 验证所有任务都完成了
        assert len(results) == num_tasks, f"任务数量不匹配: {len(results)} != {num_tasks}"
        assert set(results) == set(range(num_tasks)), "不是所有任务都完成了"

        # 验证并发限制生效
        assert max_observed_concurrency <= max_concurrent, (
            f"并发数超过限制: {max_observed_concurrency} > {max_concurrent}"
        )

        # 验证任务管理器统计
        stats = manager.get_stats()
        assert stats['total_submitted'] == num_tasks
        assert stats['active_tasks'] == 0  # 所有任务已完成

        print(f"Task manager stats: {stats}")
        print(f"Max observed concurrency: {max_observed_concurrency}")


class TestHealthEndpoint:
    """测试健康检查端点"""

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_valid_data(self):
        """
        测试健康检查端点

        调用 /api/health/performance，验证：
        - 返回 200
        - 返回包含 status, memory, gc, buffer_pool, task_manager
        """
        from fastapi.testclient import TestClient
        from server.app.main import app

        client = TestClient(app)

        # 调用健康检查端点
        response = client.get("/api/health/performance")

        # 验证返回 200
        assert response.status_code == 200, f"健康检查失败: {response.status_code}"

        # 解析响应
        data = response.json()

        # 验证返回包含必要字段
        required_fields = ['status', 'memory', 'gc', 'buffer_pool', 'task_manager']
        for field in required_fields:
            assert field in data, f"缺少必要字段: {field}"

        # 验证 status 是有效值
        valid_statuses = ['healthy', 'warning', 'critical']
        assert data['status'] in valid_statuses, f"无效的 status 值: {data['status']}"

        # 验证 memory 字段结构（如果有 psutil）
        if data['memory'] and 'error' not in data['memory']:
            assert 'rss_mb' in data['memory'], "memory 缺少 rss_mb 字段"
            assert 'percent' in data['memory'], "memory 缺少 percent 字段"

        # 验证 gc 字段结构
        if data['gc'] and 'error' not in data['gc']:
            assert 'threshold' in data['gc'], "gc 缺少 threshold 字段"
            assert 'count' in data['gc'], "gc 缺少 count 字段"

        # 验证 buffer_pool 字段结构
        if data['buffer_pool'] and 'error' not in data['buffer_pool']:
            assert 'hit_rate' in data['buffer_pool'], "buffer_pool 缺少 hit_rate 字段"

        # 验证 task_manager 字段结构
        if data['task_manager'] and 'error' not in data['task_manager']:
            assert 'max_concurrent' in data['task_manager'], "task_manager 缺少 max_concurrent 字段"
            assert 'active_tasks' in data['task_manager'], "task_manager 缺少 active_tasks 字段"

        print(f"Health check response: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
