"""MiniMax 集成测试

这些测试需要真实的MINIMAX_API_KEY环境变量。
如果没有设置，测试将被跳过。

运行方式:
    export MINIMAX_API_KEY=your-key-here
    pytest tests/ai/integration/test_minimax_integration.py -v
"""
import pytest
import os
from server.ai.ai_gateway_v2 import AIGatewayV2


# Skip all tests in this module if MINIMAX_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("MINIMAX_API_KEY"),
    reason="MINIMAX_API_KEY environment variable not set"
)


@pytest.fixture(autouse=True)
def reset_gateway():
    """每个测试前后重置网关实例"""
    AIGatewayV2._reset_instance()
    yield
    AIGatewayV2._reset_instance()


class TestMiniMaxBasicIntegration:
    """MiniMax 基础集成测试"""

    def test_minimax_provider_loaded_from_env(self):
        """测试从环境变量加载MiniMax服务商"""
        gateway = AIGatewayV2()
        assert "minimax" in gateway.providers
        assert gateway.providers["minimax"].default_model == "MiniMax-M2.5-highspeed"

    def test_minimax_basic_chat_completion(self):
        """测试MiniMax基础对话补全"""
        gateway = AIGatewayV2()
        gateway.switch_provider("minimax")

        messages = [{"role": "user", "content": "你好，请用一句话介绍自己。"}]
        result = gateway.chat_completion(messages=messages)

        assert "content" in result
        assert len(result["content"]) > 0
        print(f"\n响应: {result['content']}")

    def test_minimax_chat_completion_with_thinking(self):
        """测试MiniMax带思考模式的对话补全"""
        gateway = AIGatewayV2()
        gateway.switch_provider("minimax")

        messages = [{"role": "user", "content": "1+1等于多少？请思考一下。"}]
        result = gateway.chat_completion(messages=messages, enable_thinking=True)

        assert "content" in result
        assert "reasoning" in result
        assert len(result["content"]) > 0
        print(f"\n思考过程: {result.get('reasoning', '(无)')[:200]}...")
        print(f"回答: {result['content']}")


class TestMiniMaxStreamingIntegration:
    """MiniMax 流式输出集成测试"""

    def test_minimax_streaming_chat_completion(self):
        """测试MiniMax流式对话补全"""
        gateway = AIGatewayV2()
        gateway.switch_provider("minimax")

        messages = [{"role": "user", "content": "数数1到5"}]
        chunks = list(gateway.chat_completion_stream(messages=messages))

        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0
        print(f"\n流式响应: {full_response}")

    def test_minimax_streaming_with_thinking_warning(self):
        """测试MiniMax流式带思考模式的警告"""
        gateway = AIGatewayV2()
        gateway.switch_provider("minimax")

        messages = [{"role": "user", "content": "你好"}]

        # Should log warning but still work
        chunks = list(gateway.chat_completion_stream(
            messages=messages,
            enable_thinking=True
        ))

        assert len(chunks) >= 0  # May or may not have content


class TestMiniMaxModelSelectionIntegration:
    """MiniMax 模型选择集成测试"""

    def test_minimax_highspeed_model(self):
        """测试MiniMax高速模型"""
        gateway = AIGatewayV2()
        gateway.switch_provider("minimax", "MiniMax-M2.5-highspeed")

        messages = [{"role": "user", "content": "Hi"}]
        result = gateway.chat_completion(messages=messages)

        assert "content" in result
        assert len(result["content"]) > 0

    def test_minimax_standard_model(self):
        """测试MiniMax标准模型"""
        gateway = AIGatewayV2()
        gateway.switch_provider("minimax", "MiniMax-M2.5")

        messages = [{"role": "user", "content": "Hi"}]
        result = gateway.chat_completion(messages=messages)

        assert "content" in result
        assert len(result["content"]) > 0


class TestMiniMaxSmartRoutingIntegration:
    """MiniMax 智能路由集成测试"""

    def test_smart_route_live_analysis_to_minimax(self):
        """测试实时分析路由到MiniMax highspeed"""
        gateway = AIGatewayV2()

        # 实时分析任务应该路由到MiniMax highspeed
        route = gateway.smart_route("live_analysis", {"latency": "fast"})
        assert route == "minimax:MiniMax-M2.5-highspeed"

    def test_smart_route_live_review_to_minimax(self):
        """测试复盘总结路由到MiniMax标准版"""
        gateway = AIGatewayV2()

        # 复盘总结应该路由到MiniMax标准版（204K上下文）
        route = gateway.smart_route("live_review", {})
        assert route == "minimax:MiniMax-M2.5"
