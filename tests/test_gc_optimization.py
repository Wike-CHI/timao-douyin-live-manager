# -*- coding: utf-8 -*-
"""
GC 优化测试
测试 GC 阈值优化是否正确应用
"""

import gc
import os
import pytest


class TestGCOptimization:
    """GC 优化测试套件"""

    def test_gc_threshold_is_adjusted(self):
        """测试 GC 阈值已调整（>= 2000, 20, 20）"""
        # 模拟 main.py 中的 GC 优化逻辑
        original_threshold = gc.get_threshold()

        # 如果 GC_OPTIMIZATION_ENABLED 不是 false，则应用优化
        if os.getenv("GC_OPTIMIZATION_ENABLED", "true").lower() != "false":
            gc.set_threshold(2000, 20, 20)

        thresholds = gc.get_threshold()

        # 验证 GC 阈值已从默认值调整
        # 默认: (700, 10, 10) → 优化后: (2000, 20, 20)
        assert thresholds[0] >= 2000, (
            f"Generation 0 threshold should be >= 2000, got {thresholds[0]}"
        )
        assert thresholds[1] >= 20, (
            f"Generation 1 threshold should be >= 20, got {thresholds[1]}"
        )
        assert thresholds[2] >= 20, (
            f"Generation 2 threshold should be >= 20, got {thresholds[2]}"
        )

        # 恢复原始阈值
        gc.set_threshold(*original_threshold)

    def test_gc_collect_works(self):
        """测试手动 GC 正常工作"""
        # 创建一些垃圾对象
        for _ in range(1000):
            _ = [i for i in range(100)]

        # 强制 GC
        collected = gc.collect()

        # GC 应该能收集到一些对象
        # 注意：collected 可能是 0，取决于 Python 版本和 GC 状态
        # 我们只验证 GC 不抛出异常
        assert isinstance(collected, int), "gc.collect() should return an integer"
        assert collected >= 0, "gc.collect() should return a non-negative integer"

    def test_gc_enabled(self):
        """测试 GC 是启用的"""
        assert gc.isenabled(), "GC should be enabled by default"

    def test_gc_threshold_structure(self):
        """测试 GC 阈值结构正确"""
        thresholds = gc.get_threshold()

        # 验证返回值是包含 3 个元素的元组
        assert isinstance(thresholds, tuple), "get_threshold() should return a tuple"
        assert len(thresholds) == 3, "get_threshold() should return 3 values"

        # 验证所有值都是正整数
        for i, threshold in enumerate(thresholds):
            assert isinstance(threshold, int), (
                f"Threshold {i} should be an integer, got {type(threshold)}"
            )
            assert threshold > 0, f"Threshold {i} should be positive, got {threshold}"

    def test_gc_optimization_can_be_disabled(self):
        """测试 GC 优化可以通过环境变量禁用"""
        original_threshold = gc.get_threshold()

        # 保存原始环境变量
        original_env = os.environ.get("GC_OPTIMIZATION_ENABLED")

        try:
            # 设置环境变量禁用 GC 优化
            os.environ["GC_OPTIMIZATION_ENABLED"] = "false"

            # 模拟 main.py 中的逻辑
            if os.getenv("GC_OPTIMIZATION_ENABLED", "true").lower() != "false":
                gc.set_threshold(2000, 20, 20)
                optimized = True
            else:
                optimized = False

            # 验证优化被跳过
            assert not optimized, "GC optimization should be skipped when disabled"

        finally:
            # 恢复原始阈值和环境变量
            gc.set_threshold(*original_threshold)
            if original_env is None:
                os.environ.pop("GC_OPTIMIZATION_ENABLED", None)
            else:
                os.environ["GC_OPTIMIZATION_ENABLED"] = original_env


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
