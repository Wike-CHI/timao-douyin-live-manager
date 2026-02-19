"""测试chat_completion方法"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from server.ai.ai_gateway_v2 import AIGatewayV2


@pytest.fixture
def gateway_with_mocked_client():
    """创建带有模拟客户端的网关实例"""
    AIGatewayV2._reset_instance()

    # Create mock client before any provider registration
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test response content"
    mock_response.choices[0].message.reasoning_content = "Test reasoning"
    mock_client.chat.completions.create.return_value = mock_response

    with patch.dict('os.environ', {}, clear=True):
        with patch('server.ai.ai_gateway_v2.OpenAI', return_value=mock_client):
            g = AIGatewayV2()

            g.register_provider("glm", "test-key", "https://test.api", "glm-5")
            g.register_provider("minimax", "test-key", "https://test.api", "MiniMax-M2.5")

            yield g

    AIGatewayV2._reset_instance()


def test_chat_completion_basic_call(gateway_with_mocked_client):
    """测试基本chat_completion调用"""
    gateway = gateway_with_mocked_client
    gateway.switch_provider("glm")

    messages = [{"role": "user", "content": "Hello"}]
    result = gateway.chat_completion(messages=messages)

    assert "content" in result
    assert result["content"] == "Test response content"


def test_chat_completion_with_thinking_enabled(gateway_with_mocked_client):
    """测试启用思考模式的chat_completion"""
    gateway = gateway_with_mocked_client
    gateway.switch_provider("glm")

    messages = [{"role": "user", "content": "Hello"}]
    result = gateway.chat_completion(messages=messages, enable_thinking=True)

    assert "content" in result
    assert "reasoning" in result
    assert result["reasoning"] == "Test reasoning"


def test_chat_completion_switches_provider(gateway_with_mocked_client):
    """测试chat_completion可以切换服务商"""
    gateway = gateway_with_mocked_client

    messages = [{"role": "user", "content": "Hello"}]

    # Test with GLM
    gateway.switch_provider("glm")
    result = gateway.chat_completion(messages=messages)
    assert "content" in result

    # Test with MiniMax
    gateway.switch_provider("minimax")
    result = gateway.chat_completion(messages=messages)
    assert "content" in result


def test_chat_completion_raises_error_no_provider(gateway_with_mocked_client):
    """测试未切换服务商时抛出错误"""
    gateway = gateway_with_mocked_client
    # Don't switch provider

    messages = [{"role": "user", "content": "Hello"}]

    with pytest.raises(ValueError, match="未选择服务商"):
        gateway.chat_completion(messages=messages)


def test_chat_completion_passes_model_override(gateway_with_mocked_client):
    """测试model参数覆盖"""
    gateway = gateway_with_mocked_client
    gateway.switch_provider("glm")

    messages = [{"role": "user", "content": "Hello"}]
    result = gateway.chat_completion(messages=messages, model="glm-5-custom")

    # Verify the mock was called with the correct model
    call_args = gateway.clients["glm"].chat.completions.create.call_args
    assert call_args.kwargs["model"] == "glm-5-custom"


def test_chat_completion_with_custom_temperature(gateway_with_mocked_client):
    """测试自定义temperature参数"""
    gateway = gateway_with_mocked_client
    gateway.switch_provider("glm")

    messages = [{"role": "user", "content": "Hello"}]
    result = gateway.chat_completion(messages=messages, temperature=0.5)

    call_args = gateway.clients["glm"].chat.completions.create.call_args
    assert call_args.kwargs["temperature"] == 0.5


def test_chat_completion_with_custom_max_tokens(gateway_with_mocked_client):
    """测试自定义max_tokens参数"""
    gateway = gateway_with_mocked_client
    gateway.switch_provider("glm")

    messages = [{"role": "user", "content": "Hello"}]
    result = gateway.chat_completion(messages=messages, max_tokens=2048)

    call_args = gateway.clients["glm"].chat.completions.create.call_args
    assert call_args.kwargs["max_tokens"] == 2048


def test_chat_completion_raises_error_client_unavailable(gateway_with_mocked_client):
    """测试客户端不可用时抛出错误"""
    gateway = gateway_with_mocked_client

    # Remove the client for glm
    del gateway.clients["glm"]
    gateway.switch_provider("glm")

    messages = [{"role": "user", "content": "Hello"}]

    with pytest.raises(ValueError, match="客户端不可用"):
        gateway.chat_completion(messages=messages)


def test_chat_completion_with_minimax_thinking(gateway_with_mocked_client):
    """测试MiniMax的思考模式"""
    gateway = gateway_with_mocked_client
    gateway.switch_provider("minimax")

    # Setup mock for MiniMax reasoning format
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Response content"
    mock_response.choices[0].message.reasoning_details = [{"text": "MiniMax reasoning"}]

    # Create a new mock client for minimax with the custom response
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    gateway.clients["minimax"] = mock_client

    messages = [{"role": "user", "content": "Hello"}]
    result = gateway.chat_completion(messages=messages, enable_thinking=True)

    assert "content" in result
    assert "reasoning" in result
    assert result["reasoning"] == "MiniMax reasoning"


def test_chat_completion_handles_api_error(gateway_with_mocked_client):
    """测试API调用失败时的错误处理"""
    gateway = gateway_with_mocked_client
    gateway.switch_provider("glm")
    gateway.clients["glm"].chat.completions.create.side_effect = Exception("Network Error")

    with pytest.raises(RuntimeError, match="AI服务调用失败"):
        gateway.chat_completion(messages=[{"role": "user", "content": "Hello"}])


def test_chat_completion_handles_empty_response(gateway_with_mocked_client):
    """测试空响应处理"""
    gateway = gateway_with_mocked_client
    gateway.switch_provider("glm")

    # Mock empty response
    gateway.clients["glm"].chat.completions.create.return_value.choices = []

    with pytest.raises(ValueError, match="API返回空响应"):
        gateway.chat_completion(messages=[{"role": "user", "content": "Hello"}])
