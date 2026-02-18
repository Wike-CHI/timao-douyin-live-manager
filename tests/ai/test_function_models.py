"""测试功能级模型配置"""
import pytest
from server.ai.function_models import (
    FUNCTION_MODELS,
    get_function_model,
    get_all_function_models
)


def test_function_models_structure():
    """测试功能模型配置结构"""
    assert "live_analysis" in FUNCTION_MODELS
    assert "style_profile" in FUNCTION_MODELS
    assert "script_generation" in FUNCTION_MODELS
    assert "live_review" in FUNCTION_MODELS


def test_live_analysis_uses_minimax_highspeed():
    """测试实时分析使用MiniMax highspeed"""
    config = get_function_model("live_analysis")

    assert config["provider"] == "minimax"
    assert config["model"] == "MiniMax-M2.5-highspeed"
    assert config["enable_thinking"] is False


def test_style_profile_uses_glm5():
    """测试风格画像使用GLM-5"""
    config = get_function_model("style_profile")

    assert config["provider"] == "glm"
    assert config["model"] == "glm-5"
    assert config["enable_thinking"] is True


def test_get_all_function_models_returns_copy():
    """测试获取所有配置返回副本"""
    all_models = get_all_function_models()

    # 修改返回的副本不应影响原始配置
    all_models["test"] = {"provider": "test"}
    assert "test" not in FUNCTION_MODELS


def test_get_function_model_unknown_returns_default():
    """测试未知功能返回默认配置"""
    config = get_function_model("unknown_function")

    assert config["provider"] == "minimax"
    assert config["model"] == "MiniMax-M2.5-highspeed"
