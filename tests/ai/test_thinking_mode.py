"""测试思考模式管理器"""
import pytest
from server.ai.thinking_mode import ThinkingMode


def test_enable_for_glm5_adds_thinking_parameter():
    """测试为GLM-5启用思考模式"""
    kwargs = {"temperature": 0.7}
    result = ThinkingMode.enable_for_glm5(kwargs)

    assert "thinking" in result
    assert result["thinking"]["type"] == "enabled"
    assert result["temperature"] == 0.7  # 保留原有参数


def test_enable_for_minimax_adds_reasoning_split():
    """测试为MiniMax启用思考分离"""
    kwargs = {"temperature": 0.5}
    result = ThinkingMode.enable_for_minimax(kwargs)

    assert "extra_body" in result
    assert result["extra_body"]["reasoning_split"] is True
    assert result["temperature"] == 0.5


def test_parse_glm5_thinking_response():
    """测试解析GLM-5的思考响应"""
    # 模拟GLM-5响应对象
    class MockMessage:
        reasoning_content = "思考过程内容"
        content = "最终输出内容"

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    response = MockResponse()
    result = ThinkingMode.parse_thinking_response(response, "glm")

    assert result["reasoning"] == "思考过程内容"
    assert result["content"] == "最终输出内容"


def test_parse_minimax_thinking_response():
    """测试解析MiniMax的思考响应"""
    # 模拟MiniMax响应对象
    class MockMessage:
        reasoning_details = [{"text": "推理步骤1"}, {"text": "推理步骤2"}]
        content = "最终答案"

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    response = MockResponse()
    result = ThinkingMode.parse_thinking_response(response, "minimax")

    assert result["reasoning"] == "推理步骤1推理步骤2"
    assert result["content"] == "最终答案"


def test_parse_response_without_thinking():
    """测试解析不包含思考过程的响应"""
    class MockMessage:
        content = "普通响应"

    class MockChoice:
        message = MockMessage()

    class MockResponse:
        choices = [MockChoice()]

    response = MockResponse()
    result = ThinkingMode.parse_thinking_response(response, "unknown_provider")

    assert result["reasoning"] == ""
    assert result["content"] == "普通响应"
