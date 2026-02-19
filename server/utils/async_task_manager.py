# -*- coding: utf-8 -*-
"""
AsyncTaskManager - 异步任务管理器

用于在单进程内管理异步任务，限制并发数，支持回调。
"""

import asyncio
from typing import Any, Callable, Coroutine, Dict, Optional
from loguru import logger


class AsyncTaskManager:
    """
    异步任务管理器

    使用信号量限制并发任务数，支持任务完成后调用回调。
    """

    def __init__(self, max_concurrent: int = 10):
        """
        初始化异步任务管理器

        Args:
            max_concurrent: 最大并发任务数，默认10
        """
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._task_counter = 0
        logger.info(f"AsyncTaskManager initialized with max_concurrent={max_concurrent}")

    def submit(
        self,
        coro: Coroutine,
        callback: Optional[Callable[[Any], Any]] = None
    ) -> asyncio.Task:
        """
        提交异步任务

        Args:
            coro: 协程对象
            callback: 可选的回调函数，任务完成后调用

        Returns:
            asyncio.Task 对象
        """
        # 生成任务ID
        self._task_counter += 1
        task_id = f"task_{self._task_counter}"

        async def wrapped_task():
            async with self._semaphore:
                try:
                    result = await coro
                    if callback is not None:
                        try:
                            callback_result = callback(result)
                            # 如果回调返回协程，需要 await
                            if asyncio.iscoroutine(callback_result):
                                await callback_result
                        except Exception as e:
                            logger.error(f"Callback execution failed: {e}")
                    return result
                except Exception as e:
                    logger.error(f"Task execution failed: {e}")
                    raise
                finally:
                    # 任务完成后从活跃任务中移除
                    if task_id in self._active_tasks:
                        del self._active_tasks[task_id]

        task = asyncio.create_task(wrapped_task())
        self._active_tasks[task_id] = task

        return task

    def get_active_task_count(self) -> int:
        """
        获取活跃任务数

        Returns:
            当前活跃的任务数量
        """
        return len(self._active_tasks)

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            包含统计信息的字典
        """
        return {
            "max_concurrent": self.max_concurrent,
            "active_tasks": len(self._active_tasks),
            "total_submitted": self._task_counter
        }

    async def cancel_all(self) -> int:
        """
        取消所有活跃任务

        Returns:
            被取消的任务数量
        """
        count = 0
        for task_id, task in list(self._active_tasks.items()):
            if not task.done():
                task.cancel()
                count += 1
        self._active_tasks.clear()
        logger.info(f"Cancelled {count} active tasks")
        return count


# 全局单例
_task_manager_instance: Optional[AsyncTaskManager] = None


def get_task_manager(max_concurrent: int = 10) -> AsyncTaskManager:
    """
    获取全局任务管理器单例

    Args:
        max_concurrent: 最大并发任务数，仅在首次创建时生效

    Returns:
        AsyncTaskManager 实例
    """
    global _task_manager_instance
    if _task_manager_instance is None:
        _task_manager_instance = AsyncTaskManager(max_concurrent=max_concurrent)
    return _task_manager_instance
