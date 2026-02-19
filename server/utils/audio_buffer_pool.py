# -*- coding: utf-8 -*-
"""
音频缓冲区内存池

复用 numpy 数组，减少内存分配和 GC 压力，提升音频处理性能。
"""

import threading
from typing import Dict, Any, Optional
import numpy as np


class AudioBufferPool:
    """
    音频缓冲区内存池

    复用 numpy 数组以减少内存分配开销和 GC 压力。
    适用于频繁创建和销毁固定大小音频缓冲区的场景。

    Example:
        >>> pool = AudioBufferPool(buffer_size=25600, max_pool_size=50)
        >>> buffer = pool.acquire()
        >>> # 使用 buffer...
        >>> pool.release(buffer)
    """

    def __init__(self, buffer_size: int = 25600, max_pool_size: int = 50):
        """
        初始化音频缓冲区池

        Args:
            buffer_size: 单个缓冲区大小（样本数），默认 25600 = 1.6秒 * 16kHz
            max_pool_size: 池最大容量（保留的缓冲区数量），默认 50 个 ≈ 2.5MB
        """
        self.buffer_size = buffer_size
        self.max_pool_size = max_pool_size

        # 可用缓冲区列表
        self._pool: list[np.ndarray] = []

        # 统计信息
        self._total_created = 0
        self._stats = {'hits': 0, 'misses': 0, 'total_allocs': 0}

        # 线程安全锁
        self._lock = threading.Lock()

    def acquire(self) -> np.ndarray:
        """
        获取一个缓冲区

        如果池中有空闲缓冲区则复用，否则分配新的。

        Returns:
            np.ndarray: 形状为 (buffer_size,) 的 float32 数组
        """
        with self._lock:
            if self._pool:
                # 复用池中的缓冲区
                self._stats['hits'] += 1
                return self._pool.pop()
            else:
                # 创建新缓冲区
                buffer = np.zeros(self.buffer_size, dtype=np.float32)
                self._total_created += 1
                self._stats['misses'] += 1
                self._stats['total_allocs'] += 1
                return buffer

    def release(self, buffer: np.ndarray) -> None:
        """
        释放缓冲区（归还到池）

        如果池未满则清空数据后归还，否则直接丢弃（让 GC 回收）。

        Args:
            buffer: 要归还的缓冲区
        """
        with self._lock:
            # 检查池是否已满
            if len(self._pool) < self.max_pool_size:
                # 清空数据
                buffer.fill(0)
                # 归还到池
                self._pool.append(buffer)
            # 否则直接丢弃（不添加到池）

    def get_stats(self) -> Dict[str, Any]:
        """
        获取池统计信息

        Returns:
            Dict 包含:
                - hits: 从池中复用的次数
                - misses: 新分配的次数
                - hit_rate: 命中率（百分比字符串，如 "80.0%"）
                - pool_size: 当前池中缓冲区数量
        """
        with self._lock:
            total = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total if total > 0 else 0.0
            return {
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': f"{hit_rate:.1%}",  # 如 "80.0%"
                'pool_size': len(self._pool),
                # 保留旧字段以保持向后兼容
                'buffer_size': self.buffer_size,
                'max_pool_size': self.max_pool_size,
                'available_buffers': len(self._pool),
                'total_created': self._total_created
            }

    def clear(self) -> int:
        """
        清空池中所有缓冲区

        Returns:
            int: 清空前池中的缓冲区数量
        """
        with self._lock:
            count = len(self._pool)
            self._pool.clear()
            return count


# 全局单例
_audio_pool: Optional[AudioBufferPool] = None
_audio_pool_lock = threading.Lock()


def get_audio_pool() -> AudioBufferPool:
    """
    获取全局音频缓冲区池单例

    Returns:
        AudioBufferPool: 全局音频缓冲区池实例
    """
    global _audio_pool

    if _audio_pool is None:
        with _audio_pool_lock:
            # 双重检查锁定
            if _audio_pool is None:
                _audio_pool = AudioBufferPool(
                    buffer_size=25600,  # 1.6秒 * 16kHz
                    max_pool_size=50     # ~2.5MB
                )

    return _audio_pool
