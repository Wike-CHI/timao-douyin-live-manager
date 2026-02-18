"""测试智能路由引擎"""
import pytest
from server.ai.ai_gateway_v2 import AIGatewayV2


@pytest.fixture
def gateway():
    """创建配置好的网关实例"""
    AIGatewayV2._reset_instance()
    g = AIGatewayV2()
    g.register_provider("glm", "key", "url", "glm-5")
    g.register_provider("minimax", "key", "url", "MiniMax-M2.5-highspeed")
    yield g
    AIGatewayV2._reset_instance()


def test_route_live_analysis_to_minimax_highspeed(gateway):
    """测试实时分析路由到MiniMax highspeed"""
    model = gateway.smart_route("live_analysis", {"latency": "fast"})
    assert model == "minimax:MiniMax-M2.5-highspeed"


def test_route_style_profile_to_glm5(gateway):
    """测试风格画像路由到GLM-5"""
    model = gateway.smart_route("style_profile", {})
    assert model == "glm:glm-5"


def test_route_script_generation_to_glm5(gateway):
    """测试话术生成路由到GLM-5"""
    model = gateway.smart_route("script_generation", {})
    assert model == "glm:glm-5"


def test_route_live_review_to_minimax(gateway):
    """测试复盘总结路由到MiniMax标准版"""
    model = gateway.smart_route("live_review", {})
    assert model == "minimax:MiniMax-M2.5"


def test_route_reflection_to_glm5(gateway):
    """测试反思路由到GLM-5"""
    model = gateway.smart_route("reflection", {})
    assert model == "glm:glm-5"


def test_route_unknown_to_default(gateway):
    """测试未知任务路由到默认模型"""
    model = gateway.smart_route("unknown_task", {})
    assert model == "minimax:MiniMax-M2.5-highspeed"


def test_route_live_analysis_normal_latency(gateway):
    """测试实时分析普通延迟路由到MiniMax标准版"""
    model = gateway.smart_route("live_analysis", {"latency": "normal"})
    assert model == "minimax:MiniMax-M2.5"


def test_route_topic_generation_to_glm5(gateway):
    """测试话题生成路由到GLM-5"""
    model = gateway.smart_route("topic_generation", {})
    assert model == "glm:glm-5"


def test_route_chat_focus_to_minimax_highspeed(gateway):
    """测试聊天焦点路由到MiniMax highspeed"""
    model = gateway.smart_route("chat_focus", {})
    assert model == "minimax:MiniMax-M2.5-highspeed"


def test_route_live_analysis_no_latency_requirement(gateway):
    """测试实时分析无延迟需求时默认使用标准版"""
    model = gateway.smart_route("live_analysis", {})
    assert model == "minimax:MiniMax-M2.5"
