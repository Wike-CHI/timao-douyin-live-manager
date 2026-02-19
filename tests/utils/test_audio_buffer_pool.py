# -*- coding: utf-8 -*-
"""
AudioBufferPool 单元测试

测试音频缓冲区内存池功能，用于复用 numpy 数组，减少内存分配和 GC 压力。

TDD 方法：先编写测试，再实现功能。
"""

import pytest
import numpy as np


class TestAudioBufferPool:
    """AudioBufferPool 测试套件"""

    def test_acquire_creates_new_buffer(self):
        """测试首次获取创建新缓冲区"""
        # 在测试内部导入，避免模块不存在时导入失败
        from server.utils.audio_buffer_pool import AudioBufferPool

        pool = AudioBufferPool(buffer_size=1024, max_pool_size=10)
        buffer = pool.acquire()

        assert buffer is not None
        assert isinstance(buffer, np.ndarray)
        assert buffer.shape == (1024,)
        assert buffer.dtype == np.float32

    def test_release_returns_buffer_to_pool(self):
        """测试归还缓冲区进入池"""
        from server.utils.audio_buffer_pool import AudioBufferPool

        pool = AudioBufferPool(buffer_size=1024, max_pool_size=10)
        buffer = pool.acquire()

        # 归还缓冲区
        pool.release(buffer)

        # 检查池中有可用缓冲区
        stats = pool.get_stats()
        assert stats['available_buffers'] == 1
        assert stats['total_created'] == 1

    def test_acquire_reuses_released_buffer(self):
        """测试获取复用已归还的缓冲区"""
        from server.utils.audio_buffer_pool import AudioBufferPool

        pool = AudioBufferPool(buffer_size=1024, max_pool_size=10)

        # 获取并归还
        buffer1 = pool.acquire()
        pool.release(buffer1)

        # 再次获取应该复用
        buffer2 = pool.acquire()

        # 应该是同一个缓冲区对象
        assert buffer2 is buffer1

        stats = pool.get_stats()
        assert stats['available_buffers'] == 0
        assert stats['total_created'] == 1  # 只创建了一个

    def test_pool_overflow_drops_excess_buffers(self):
        """测试池满后丢弃多余缓冲区"""
        from server.utils.audio_buffer_pool import AudioBufferPool

        max_size = 3
        pool = AudioBufferPool(buffer_size=1024, max_pool_size=max_size)

        # 创建超过池容量的缓冲区
        buffers = [pool.acquire() for _ in range(max_size + 2)]

        # 全部归还
        for buf in buffers:
            pool.release(buf)

        # 池中应该只保留 max_size 个缓冲区
        stats = pool.get_stats()
        assert stats['available_buffers'] == max_size

    def test_released_buffer_is_cleared(self):
        """测试归还的缓冲区被清空"""
        from server.utils.audio_buffer_pool import AudioBufferPool

        pool = AudioBufferPool(buffer_size=1024, max_pool_size=10)
        buffer = pool.acquire()

        # 填充数据
        buffer.fill(0.5)

        # 归并（应该清空）
        pool.release(buffer)

        # 再次获取同一个缓冲区
        buffer2 = pool.acquire()

        # 验证数据被清零
        assert np.all(buffer2 == 0.0)

    def test_get_stats_returns_correct_info(self):
        """测试统计信息正确"""
        from server.utils.audio_buffer_pool import AudioBufferPool

        pool = AudioBufferPool(buffer_size=2048, max_pool_size=5)

        # 初始状态
        stats = pool.get_stats()
        assert stats['buffer_size'] == 2048
        assert stats['max_pool_size'] == 5
        assert stats['available_buffers'] == 0
        assert stats['total_created'] == 0

        # 获取2个缓冲区
        buf1 = pool.acquire()
        buf2 = pool.acquire()

        stats = pool.get_stats()
        assert stats['available_buffers'] == 0
        assert stats['total_created'] == 2

        # 归还1个
        pool.release(buf1)

        stats = pool.get_stats()
        assert stats['available_buffers'] == 1
        assert stats['total_created'] == 2
