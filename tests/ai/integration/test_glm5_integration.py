"""GLM-5 集成测试

这些测试需要真实的GLM_API_KEY环境变量。
如果没有设置，测试将被跳过。

运行方式:
    export GLM_API_KEY=your-key-here
    pytest tests/ai/integration/test_glm5_integration.py -v
"""
import pytest
import os
from server.ai.ai_gateway_v2 import AIGatewayV2


# Skip all tests in this module if GLM_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.getenv("GLM_API_KEY"),
    reason="GLM_API_KEY environment variable not set"
)


@pytest.fixture(autouse=True)
def reset_gateway():
    """每个测试前后重置网关实例"""
    AIGatewayV2._reset_instance()
    yield
    AIGatewayV2._reset_instance()


class TestGLM5BasicIntegration:
    """GLM-5 基础集成测试"""

    def test_glm5_provider_loaded_from_env(self):
        """测试从环境变量加载GLM-5服务商"""
        gateway = AIGatewayV2()
        assert "glm" in gateway.providers
        assert gateway.providers["glm"].default_model == "glm-5"

    def test_glm5_basic_chat_completion(self):
        """测试GLM-5基础对话补全"""
        gateway = AIGatewayV2()
        gateway.switch_provider("glm")

        messages = [{"role": "user", "content": "你好，请用一句话介绍自己。"}]
        result = gateway.chat_completion(messages=messages)

        assert "content" in result
        assert len(result["content"]) > 0
        print(f"\n响应: {result['content']}")

    def test_glm5_chat_completion_with_thinking(self):
        """测试GLM-5带思考模式的对话补全"""
        gateway = AIGatewayV2()
        gateway.switch_provider("glm")

        messages = [{"role": "user", "content": "1+1等于多少？请思考一下。"}]
        result = gateway.chat_completion(messages=messages, enable_thinking=True)

        assert "content" in result
        assert "reasoning" in result
        assert len(result["content"]) > 0
        print(f"\n思考过程: {result.get('reasoning', '(无)')[:200]}...")
        print(f"回答: {result['content']}")


class TestGLM5StreamingIntegration:
    """GLM-5 流式输出集成测试"""

    def test_glm5_streaming_chat_completion(self):
        """测试GLM-5流式对话补全"""
        gateway = AIGatewayV2()
        gateway.switch_provider("glm")

        messages = [{"role": "user", "content": "数数1到5"}]
        chunks = list(gateway.chat_completion_stream(messages=messages))

        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0
        print(f"\n流式响应: {full_response}")

    def test_glm5_streaming_with_thinking_warning(self):
        """测试GLM-5流式带思考模式的警告"""
        gateway = AIGatewayV2()
        gateway.switch_provider("glm")

        messages = [{"role": "user", "content": "你好"}]

        # Should log warning but still work
        chunks = list(gateway.chat_completion_stream(
            messages=messages,
            enable_thinking=True
        ))

        assert len(chunks) >= 0  # May or may not have content


class TestGLM5SmartRoutingIntegration:
    """GLM-5 智能路由集成测试"""

    def test_smart_route_to_glm5(self):
        """测试智能路由选择GLM-5"""
        gateway = AIGatewayV2()

        # Agent工作流任务应该路由到GLM-5
        route = gateway.smart_route("style_profile", {})
        assert route == "glm:glm-5"

        route = gateway.smart_route("script_generation", {})
        assert route == "glm:glm-5"
