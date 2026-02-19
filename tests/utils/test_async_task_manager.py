# -*- coding: utf-8 -*-
"""
AsyncTaskManager 单元测试

测试异步任务管理器功能，用于在单进程内管理异步任务，限制并发数。

TDD 方法：先编写测试，再实现功能。
"""

import pytest
import asyncio


class TestAsyncTaskManager:
    """AsyncTaskManager 测试套件"""

    @pytest.mark.asyncio
    async def test_submit_task_returns_task(self):
        """测试提交任务返回 asyncio.Task 对象"""
        # 在测试内部导入，避免模块不存在时导入失败
        from server.utils.async_task_manager import AsyncTaskManager

        manager = AsyncTaskManager(max_concurrent=5)

        async def dummy_task():
            return "result"

        task = manager.submit(dummy_task())

        assert task is not None
        assert isinstance(task, asyncio.Task)

        # 等待任务完成
        await task

    @pytest.mark.asyncio
    async def test_task_executes_and_returns_result(self):
        """测试任务执行并返回结果"""
        from server.utils.async_task_manager import AsyncTaskManager

        manager = AsyncTaskManager(max_concurrent=5)

        async def compute_task():
            await asyncio.sleep(0.01)
            return 42

        task = manager.submit(compute_task())
        result = await task

        assert result == 42

    @pytest.mark.asyncio
    async def test_callback_is_called_on_completion(self):
        """测试任务完成后调用回调"""
        from server.utils.async_task_manager import AsyncTaskManager

        manager = AsyncTaskManager(max_concurrent=5)
        callback_results = []

        async def task_with_result():
            return "callback_test"

        def on_complete(result):
            callback_results.append(result)

        task = manager.submit(task_with_result(), callback=on_complete)
        await task

        # 等待回调执行
        await asyncio.sleep(0.01)

        assert len(callback_results) == 1
        assert callback_results[0] == "callback_test"

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self):
        """测试信号量限制并发数（提交5个任务，max_concurrent <= 2）"""
        from server.utils.async_task_manager import AsyncTaskManager

        max_concurrent = 2
        manager = AsyncTaskManager(max_concurrent=max_concurrent)

        concurrent_count = 0
        max_observed_concurrency = 0
        lock = asyncio.Lock()

        async def concurrent_task(task_id: int):
            nonlocal concurrent_count, max_observed_concurrency

            async with lock:
                concurrent_count += 1
                if concurrent_count > max_observed_concurrency:
                    max_observed_concurrency = concurrent_count

            await asyncio.sleep(0.05)

            async with lock:
                concurrent_count -= 1

            return task_id

        # 提交5个任务
        tasks = [manager.submit(concurrent_task(i)) for i in range(5)]

        # 等待所有任务完成
        results = await asyncio.gather(*tasks)

        # 验证所有任务都完成了
        assert len(results) == 5
        # 验证最大并发数不超过限制
        assert max_observed_concurrency <= max_concurrent

    @pytest.mark.asyncio
    async def test_get_active_task_count(self):
        """测试获取活跃任务数"""
        from server.utils.async_task_manager import AsyncTaskManager

        manager = AsyncTaskManager(max_concurrent=5)

        async def slow_task():
            await asyncio.sleep(0.1)
            return "done"

        # 初始应该没有活跃任务
        assert manager.get_active_task_count() == 0

        # 提交3个任务
        tasks = [manager.submit(slow_task()) for _ in range(3)]

        # 等待一小段时间让任务开始
        await asyncio.sleep(0.01)

        # 应该有3个活跃任务
        assert manager.get_active_task_count() == 3

        # 等待所有任务完成
        await asyncio.gather(*tasks)

        # 任务完成后应该没有活跃任务
        assert manager.get_active_task_count() == 0
