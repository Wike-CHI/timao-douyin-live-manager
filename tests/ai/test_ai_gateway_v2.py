"""测试AI Gateway 2.0"""
import os
import pytest
from unittest.mock import Mock, patch
from server.ai.ai_gateway_v2 import AIGatewayV2


def test_singleton_pattern():
    """Test that AIGatewayV2 uses singleton pattern"""
    # Reset singleton for clean test
    AIGatewayV2._reset_instance()

    gateway1 = AIGatewayV2()
    gateway2 = AIGatewayV2()
    assert gateway1 is gateway2

    gateway3 = AIGatewayV2.get_instance()
    assert gateway1 is gateway3

    # Cleanup
    AIGatewayV2._reset_instance()


def test_gateway_initializes_without_providers():
    """Test initialization without environment variables"""
    # Reset singleton for clean test
    AIGatewayV2._reset_instance()

    with patch.dict(os.environ, {}, clear=True):
        gateway = AIGatewayV2()
        assert gateway.providers == {}
        assert gateway.clients == {}
        assert gateway.current_provider is None
        assert gateway.current_model is None

    # Cleanup
    AIGatewayV2._reset_instance()


def test_gateway_loads_glm_and_minimax_from_env():
    """测试从环境变量加载GLM和MiniMax配置"""
    # Reset singleton for clean test
    AIGatewayV2._reset_instance()

    with patch.dict(os.environ, {
        'GLM_API_KEY': 'test-glm-key',
        'MINIMAX_API_KEY': 'test-minimax-key'
    }):
        gateway = AIGatewayV2()

        assert "glm" in gateway.providers
        assert "minimax" in gateway.providers
        assert gateway.providers["glm"].api_key == "test-glm-key"
        assert gateway.providers["minimax"].api_key == "test-minimax-key"

    # Cleanup
    AIGatewayV2._reset_instance()


def test_register_glm5_provider():
    """测试注册GLM-5服务商"""
    # Reset singleton for clean test
    AIGatewayV2._reset_instance()

    with patch.dict(os.environ, {}, clear=True):
        gateway = AIGatewayV2()

        gateway.register_provider(
            provider="glm",
            api_key="test-key",
            base_url="https://open.bigmodel.cn/api/paas/v4",
            default_model="glm-5"
        )

        assert "glm" in gateway.providers
        assert gateway.providers["glm"].default_model == "glm-5"

    # Cleanup
    AIGatewayV2._reset_instance()


def test_register_minimax_provider():
    """测试注册MiniMax服务商"""
    # Reset singleton for clean test
    AIGatewayV2._reset_instance()

    with patch.dict(os.environ, {}, clear=True):
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

    # Cleanup
    AIGatewayV2._reset_instance()


def test_switch_provider():
    """测试切换服务商"""
    # Reset singleton for clean test
    AIGatewayV2._reset_instance()

    with patch.dict(os.environ, {}, clear=True):
        gateway = AIGatewayV2()
        gateway.register_provider("glm", "key1", "url1", "glm-5")
        gateway.register_provider("minimax", "key2", "url2", "MiniMax-M2.5")

        gateway.switch_provider("minimax", "MiniMax-M2.5-highspeed")

        assert gateway.current_provider == "minimax"
        assert gateway.current_model == "MiniMax-M2.5-highspeed"

    # Cleanup
    AIGatewayV2._reset_instance()


def test_switch_to_unknown_provider_raises_error():
    """测试切换到未注册的服务商抛出错误"""
    # Reset singleton for clean test
    AIGatewayV2._reset_instance()

    with patch.dict(os.environ, {}, clear=True):
        gateway = AIGatewayV2()

        with pytest.raises(ValueError, match="未注册的服务商"):
            gateway.switch_provider("unknown", "model")

    # Cleanup
    AIGatewayV2._reset_instance()


def test_register_provider_with_empty_api_key_raises_error():
    """测试注册时使用空API密钥抛出错误"""
    AIGatewayV2._reset_instance()

    gateway = AIGatewayV2()

    # Test with empty string
    with pytest.raises(ValueError, match="API key cannot be empty"):
        gateway.register_provider(
            provider="glm",
            api_key="",
            base_url="https://test.api",
            default_model="glm-5"
        )

    # Test with whitespace-only string
    with pytest.raises(ValueError, match="API key cannot be empty"):
        gateway.register_provider(
            provider="minimax",
            api_key="   ",
            base_url="https://test.api",
            default_model="MiniMax-M2.5"
        )

    # Verify no providers were registered
    assert "glm" not in gateway.providers
    assert "minimax" not in gateway.providers

    AIGatewayV2._reset_instance()


def test_switch_to_disabled_provider_raises_error():
    """测试切换到已禁用的服务商时抛出错误"""
    AIGatewayV2._reset_instance()

    gateway = AIGatewayV2()
    gateway.register_provider(
        provider="glm",
        api_key="test-key",
        base_url="https://test.api",
        default_model="glm-5",
        enabled=False  # Disabled
    )

    with pytest.raises(ValueError, match="服务商已禁用"):
        gateway.switch_provider("glm")

    AIGatewayV2._reset_instance()


def test_register_provider_handles_client_creation_failure():
    """测试处理客户端创建失败的情况"""
    AIGatewayV2._reset_instance()

    gateway = AIGatewayV2()

    with patch('server.ai.ai_gateway_v2.OpenAI', side_effect=Exception("Invalid API key")):
        gateway.register_provider(
            provider="glm",
            api_key="invalid-key",
            base_url="https://test.api",
            default_model="glm-5"
        )

        # Provider should be registered but disabled
        assert "glm" in gateway.providers
        assert gateway.providers["glm"].enabled is False
        assert "glm" not in gateway.clients

    AIGatewayV2._reset_instance()

