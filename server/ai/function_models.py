"""功能级模型配置

为不同功能指定最优的模型配置
"""
from typing import Any, Dict

# 功能级模型配置
# 只使用GLM-5和MiniMax系列
FUNCTION_MODELS: Dict[str, Dict[str, Any]] = {
    "live_analysis": {
        "provider": "minimax",
        "model": "MiniMax-M2.5-highspeed",  # 极速版，100 TPS
        "enable_thinking": False,           # 实时分析不需要思考过程
        "reason": "高速输出，降低延迟"
    },
    "style_profile": {
        "provider": "glm",
        "model": "glm-5",
        "enable_thinking": True,            # 启用深度思考
        "reason": "面向Agent优化，深度分析风格"
    },
    "script_generation": {
        "provider": "glm",
        "model": "glm-5",
        "enable_thinking": True,            # 启用深度思考
        "reason": "深度思考提升话术质量"
    },
    "live_review": {
        "provider": "minimax",
        "model": "MiniMax-M2.5",            # 复盘用标准版
        "enable_thinking": True,
        "reason": "204K大上下文，支持长复盘"
    },
    "reflection": {
        "provider": "glm",
        "model": "glm-5",
        "enable_thinking": True,
        "reason": "深度思考，评估分析质量"
    },
    "chat_focus": {
        "provider": "minimax",
        "model": "MiniMax-M2.5-highspeed",
        "enable_thinking": False,
        "reason": "快速摘要，降低延迟"
    },
    "topic_generation": {
        "provider": "glm",
        "model": "glm-5",
        "enable_thinking": True,
        "reason": "深度思考，生成智能话题"
    }
}

# 默认配置（MiniMax highspeed性价比最高）
DEFAULT_CONFIG = {
    "provider": "minimax",
    "model": "MiniMax-M2.5-highspeed",
    "enable_thinking": False,
    "reason": "默认配置，性价比最高"
}


def get_function_model(function_name: str) -> Dict[str, Any]:
    """获取指定功能的模型配置

    Args:
        function_name: 功能名称

    Returns:
        模型配置字典
    """
    return FUNCTION_MODELS.get(function_name, DEFAULT_CONFIG).copy()


def get_all_function_models() -> Dict[str, Dict[str, Any]]:
    """获取所有功能模型配置的副本

    Returns:
        所有功能配置的副本
    """
    return FUNCTION_MODELS.copy()
