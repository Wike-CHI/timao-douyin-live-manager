"""测试AI Gateway 2.0"""
import pytest
from unittest.mock import Mock, patch
from server.ai.ai_gateway_v2 import AIGatewayV2


def test_gateway_initializes_without_providers():
    """测试网关初始化时无服务商"""
    gateway = AIGatewayV2()

    assert gateway.providers == {}
    assert gateway.clients == {}


@patch.dict('os.environ', {
    'GLM_API_KEY': 'test-glm-key',
    'MINIMAX_API_KEY': 'test-minimax-key'
})
def test_gateway_loads_glm_and_minimax_from_env():
    """测试从环境变量加载GLM和MiniMax配置"""
    gateway = AIGatewayV2()

    assert "glm" in gateway.providers
    assert "minimax" in gateway.providers
    assert gateway.providers["glm"].api_key == "test-glm-key"
    assert gateway.providers["minimax"].api_key == "test-minimax-key"


def test_register_glm5_provider():
    """测试注册GLM-5服务商"""
    gateway = AIGatewayV2()

    gateway.register_provider(
        provider="glm",
        api_key="test-key",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        default_model="glm-5"
    )

    assert "glm" in gateway.providers
    assert gateway.providers["glm"].default_model == "glm-5"


def test_register_minimax_provider():
    """测试注册MiniMax服务商"""
    gateway = AIGatewayV2()

    gateway.register_provider(
        provider="minimax",
        api_key="test-key",
        base_url="https://api.minimaxi.com/v1",
        default_model="MiniMax-M2.5-highspeed",
        models=["MiniMax-M2.5", "MiniMax-M2.5-highspeed"]
    )

    assert "minimax" in gateway.providers
    assert "MiniMax-M2.5" in gateway.providers["minimax"].models


def test_switch_provider():
    """测试切换服务商"""
    gateway = AIGatewayV2()
    gateway.register_provider("glm", "key1", "url1", "glm-5")
    gateway.register_provider("minimax", "key2", "url2", "MiniMax-M2.5")

    gateway.switch_provider("minimax", "MiniMax-M2.5-highspeed")

    assert gateway.current_provider == "minimax"
    assert gateway.current_model == "MiniMax-M2.5-highspeed"


def test_switch_to_unknown_provider_raises_error():
    """测试切换到未注册的服务商抛出错误"""
    gateway = AIGatewayV2()

    with pytest.raises(ValueError, match="未注册的服务商"):
        gateway.switch_provider("unknown", "model")
