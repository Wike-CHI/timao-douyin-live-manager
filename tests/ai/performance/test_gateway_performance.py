"""AI Gateway 2.0 性能测试

这些测试用于测量AI网关的延迟和吞吐量。
测试需要真实的API密钥才能运行。

运行方式:
    export GLM_API_KEY=your-key
    export MINIMAX_API_KEY=your-key
    pytest tests/ai/performance/test_gateway_performance.py -v -s
"""
import pytest
import os
import time
import statistics
from typing import List

from server.ai.ai_gateway_v2 import AIGatewayV2


def measure_latency(func, *args, iterations: int = 3, **kwargs) -> dict:
    """测量函数执行延迟

    Returns:
        dict with min, max, avg, median latency in milliseconds
    """
    latencies = []

    for _ in range(iterations):
        start = time.perf_counter()
        func(*args, **kwargs)
        end = time.perf_counter()
        latencies.append((end - start) * 1000)  # Convert to ms

    return {
        "min": min(latencies),
        "max": max(latencies),
        "avg": statistics.mean(latencies),
        "median": statistics.median(latencies),
        "iterations": iterations
    }


@pytest.fixture(autouse=True)
def reset_gateway():
    """每个测试前后重置网关实例"""
    AIGatewayV2._reset_instance()
    yield
    AIGatewayV2._reset_instance()


class TestGatewayPerformance:
    """AI Gateway 性能测试基类"""

    @pytest.fixture
    def gateway(self):
        """获取配置好的网关实例"""
        return AIGatewayV2()


@pytest.mark.skipif(not os.getenv("GLM_API_KEY"), reason="GLM_API_KEY not set")
class TestGLM5Performance(TestGatewayPerformance):
    """GLM-5 性能测试"""

    def test_glm5_basic_latency(self, gateway):
        """测试GLM-5基础调用延迟"""
        gateway.switch_provider("glm")

        messages = [{"role": "user", "content": "说'你好'两个字"}]

        stats = measure_latency(
            gateway.chat_completion,
            messages=messages,
            iterations=3
        )

        print(f"\nGLM-5 基础调用延迟:")
        print(f"  最小: {stats['min']:.0f}ms")
        print(f"  最大: {stats['max']:.0f}ms")
        print(f"  平均: {stats['avg']:.0f}ms")
        print(f"  中位数: {stats['median']:.0f}ms")

        # Basic assertions - should complete within reasonable time
        assert stats['avg'] < 10000, "GLM-5 平均延迟应小于10秒"

    def test_glm5_thinking_mode_latency(self, gateway):
        """测试GLM-5思考模式延迟"""
        gateway.switch_provider("glm")

        messages = [{"role": "user", "content": "1+1=?"}]

        # Without thinking
        stats_normal = measure_latency(
            gateway.chat_completion,
            messages=messages,
            enable_thinking=False,
            iterations=3
        )

        # With thinking
        stats_thinking = measure_latency(
            gateway.chat_completion,
            messages=messages,
            enable_thinking=True,
            iterations=3
        )

        print(f"\nGLM-5 思考模式对比:")
        print(f"  无思考: {stats_normal['avg']:.0f}ms")
        print(f"  有思考: {stats_thinking['avg']:.0f}ms")
        print(f"  开销: {stats_thinking['avg'] - stats_normal['avg']:.0f}ms")

        # Thinking mode should add some overhead but not too much
        overhead_ratio = stats_thinking['avg'] / stats_normal['avg']
        print(f"  倍率: {overhead_ratio:.2f}x")


@pytest.mark.skipif(not os.getenv("MINIMAX_API_KEY"), reason="MINIMAX_API_KEY not set")
class TestMiniMaxPerformance(TestGatewayPerformance):
    """MiniMax 性能测试"""

    def test_minimax_highspeed_latency(self, gateway):
        """测试MiniMax高速版延迟"""
        gateway.switch_provider("minimax", "MiniMax-M2.5-highspeed")

        messages = [{"role": "user", "content": "说'你好'两个字"}]

        stats = measure_latency(
            gateway.chat_completion,
            messages=messages,
            iterations=3
        )

        print(f"\nMiniMax-M2.5-highspeed 基础调用延迟:")
        print(f"  最小: {stats['min']:.0f}ms")
        print(f"  最大: {stats['max']:.0f}ms")
        print(f"  平均: {stats['avg']:.0f}ms")

        # MiniMax highspeed should be faster
        assert stats['avg'] < 8000, "MiniMax highspeed 平均延迟应小于8秒"

    def test_minimax_streaming_latency(self, gateway):
        """测试MiniMax流式输出首字延迟"""
        gateway.switch_provider("minimax", "MiniMax-M2.5-highspeed")

        messages = [{"role": "user", "content": "从1数到10"}]

        # Measure time to first chunk
        start = time.perf_counter()
        chunks = list(gateway.chat_completion_stream(messages=messages))
        first_chunk_time = None

        # Re-run to measure TTFB
        start = time.perf_counter()
        for chunk in gateway.chat_completion_stream(messages=messages):
            first_chunk_time = (time.perf_counter() - start) * 1000
            break

        print(f"\nMiniMax 流式输出:")
        print(f"  首字延迟: {first_chunk_time:.0f}ms")
        print(f"  总块数: {len(chunks)}")

        assert first_chunk_time < 3000, "首字延迟应小于3秒"


@pytest.mark.skipif(
    not (os.getenv("GLM_API_KEY") and os.getenv("MINIMAX_API_KEY")),
    reason="Both GLM_API_KEY and MINIMAX_API_KEY required"
)
class TestProviderComparison(TestGatewayPerformance):
    """服务商性能对比测试"""

    def test_compare_providers_latency(self, gateway):
        """对比GLM-5和MiniMax延迟"""
        messages = [{"role": "user", "content": "1+1=?"}]

        # Test GLM-5
        gateway.switch_provider("glm")
        stats_glm = measure_latency(
            gateway.chat_completion,
            messages=messages,
            iterations=3
        )

        # Test MiniMax highspeed
        gateway.switch_provider("minimax", "MiniMax-M2.5-highspeed")
        stats_minimax = measure_latency(
            gateway.chat_completion,
            messages=messages,
            iterations=3
        )

        print(f"\n服务商延迟对比:")
        print(f"  GLM-5: {stats_glm['avg']:.0f}ms")
        print(f"  MiniMax highspeed: {stats_minimax['avg']:.0f}ms")

        # Log comparison
        if stats_minimax['avg'] < stats_glm['avg']:
            speedup = stats_glm['avg'] / stats_minimax['avg']
            print(f"  MiniMax 快 {speedup:.2f}x")
        else:
            speedup = stats_minimax['avg'] / stats_glm['avg']
            print(f"  GLM-5 快 {speedup:.2f}x")
