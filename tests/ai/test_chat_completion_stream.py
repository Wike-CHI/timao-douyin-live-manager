"""测试流式chat_completion方法"""
import pytest
from unittest.mock import MagicMock, patch
from server.ai.ai_gateway_v2 import AIGatewayV2


@pytest.fixture
def gateway_with_mocked_stream():
    """创建带有模拟流式客户端的网关实例"""
    AIGatewayV2._reset_instance()

    # Mock the streaming response
    mock_chunks = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content=" World"))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content="!"))]),
    ]

    mock_stream = MagicMock()
    mock_stream.__iter__ = lambda self: iter(mock_chunks)

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_stream

    with patch.dict('os.environ', {}, clear=True):
        with patch('server.ai.ai_gateway_v2.OpenAI', return_value=mock_client):
            g = AIGatewayV2()

            g.register_provider("glm", "test-key", "https://test.api", "glm-5")
            g.register_provider("minimax", "test-key", "https://test.api", "MiniMax-M2.5")

            yield g

    AIGatewayV2._reset_instance()


def test_chat_completion_stream_yields_chunks(gateway_with_mocked_stream):
    """测试流式输出产生chunks"""
    gateway = gateway_with_mocked_stream
    gateway.switch_provider("glm")

    messages = [{"role": "user", "content": "Hello"}]
    chunks = list(gateway.chat_completion_stream(messages=messages))

    assert len(chunks) == 3
    assert chunks[0] == "Hello"
    assert chunks[1] == " World"
    assert chunks[2] == "!"


def test_chat_completion_stream_passes_stream_param(gateway_with_mocked_stream):
    """测试流式调用传递stream=True参数"""
    gateway = gateway_with_mocked_stream
    gateway.switch_provider("glm")

    messages = [{"role": "user", "content": "Hello"}]
    list(gateway.chat_completion_stream(messages=messages))

    call_args = gateway.clients["glm"].chat.completions.create.call_args
    assert call_args.kwargs.get("stream") == True


def test_chat_completion_stream_raises_error_no_provider(gateway_with_mocked_stream):
    """测试未选择服务商时抛出错误"""
    gateway = gateway_with_mocked_stream
    # Don't switch provider

    messages = [{"role": "user", "content": "Hello"}]

    with pytest.raises(ValueError, match="未选择服务商"):
        list(gateway.chat_completion_stream(messages=messages))


def test_chat_completion_stream_handles_empty_delta(gateway_with_mocked_stream):
    """测试处理空delta"""
    gateway = gateway_with_mocked_stream
    gateway.switch_provider("glm")

    # Mock response with empty delta
    mock_chunks = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content=None))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content="Valid"))]),
    ]

    mock_stream = MagicMock()
    mock_stream.__iter__ = lambda self: iter(mock_chunks)
    gateway.clients["glm"].chat.completions.create.return_value = mock_stream

    messages = [{"role": "user", "content": "Hello"}]
    chunks = list(gateway.chat_completion_stream(messages=messages))

    # Empty delta should be skipped
    assert chunks == ["Valid"]


def test_chat_completion_stream_passes_model_override(gateway_with_mocked_stream):
    """测试model参数覆盖"""
    gateway = gateway_with_mocked_stream
    gateway.switch_provider("glm")

    messages = [{"role": "user", "content": "Hello"}]
    list(gateway.chat_completion_stream(messages=messages, model="glm-5-custom"))

    call_args = gateway.clients["glm"].chat.completions.create.call_args
    assert call_args.kwargs["model"] == "glm-5-custom"


def test_chat_completion_stream_with_custom_temperature(gateway_with_mocked_stream):
    """测试自定义temperature参数"""
    gateway = gateway_with_mocked_stream
    gateway.switch_provider("glm")

    messages = [{"role": "user", "content": "Hello"}]
    list(gateway.chat_completion_stream(messages=messages, temperature=0.5))

    call_args = gateway.clients["glm"].chat.completions.create.call_args
    assert call_args.kwargs["temperature"] == 0.5


def test_chat_completion_stream_with_custom_max_tokens(gateway_with_mocked_stream):
    """测试自定义max_tokens参数"""
    gateway = gateway_with_mocked_stream
    gateway.switch_provider("glm")

    messages = [{"role": "user", "content": "Hello"}]
    list(gateway.chat_completion_stream(messages=messages, max_tokens=2048))

    call_args = gateway.clients["glm"].chat.completions.create.call_args
    assert call_args.kwargs["max_tokens"] == 2048


def test_chat_completion_stream_raises_error_client_unavailable(gateway_with_mocked_stream):
    """测试客户端不可用时抛出错误"""
    gateway = gateway_with_mocked_stream

    # Remove the client for glm
    del gateway.clients["glm"]
    gateway.switch_provider("glm")

    messages = [{"role": "user", "content": "Hello"}]

    with pytest.raises(ValueError, match="客户端不可用"):
        list(gateway.chat_completion_stream(messages=messages))


def test_chat_completion_stream_handles_api_error(gateway_with_mocked_stream):
    """测试API调用失败时的错误处理"""
    gateway = gateway_with_mocked_stream
    gateway.switch_provider("glm")
    gateway.clients["glm"].chat.completions.create.side_effect = Exception("Network Error")

    with pytest.raises(RuntimeError, match="AI流式服务调用失败"):
        list(gateway.chat_completion_stream(messages=[{"role": "user", "content": "Hello"}]))


def test_chat_completion_stream_switches_provider(gateway_with_mocked_stream):
    """测试流式chat_completion可以切换服务商"""
    gateway = gateway_with_mocked_stream

    messages = [{"role": "user", "content": "Hello"}]

    # Test with GLM
    gateway.switch_provider("glm")
    chunks = list(gateway.chat_completion_stream(messages=messages))
    assert len(chunks) == 3

    # Test with MiniMax
    gateway.switch_provider("minimax")
    chunks = list(gateway.chat_completion_stream(messages=messages))
    assert len(chunks) == 3


def test_chat_completion_stream_handles_empty_choices(gateway_with_mocked_stream):
    """测试处理空choices"""
    gateway = gateway_with_mocked_stream
    gateway.switch_provider("glm")

    # Mock response with empty choices
    mock_chunks = [
        MagicMock(choices=[]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content="Valid"))]),
    ]

    mock_stream = MagicMock()
    mock_stream.__iter__ = lambda self: iter(mock_chunks)
    gateway.clients["glm"].chat.completions.create.return_value = mock_stream

    messages = [{"role": "user", "content": "Hello"}]
    chunks = list(gateway.chat_completion_stream(messages=messages))

    # Empty choices should be skipped
    assert chunks == ["Valid"]
