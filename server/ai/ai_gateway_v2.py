"""AI模型控制网关 2.0

统一管理GLM-5和MiniMax服务商，支持：
- 智能路由
- 思考模式
- 流式输出
"""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    """AI服务商枚举"""
    GLM = "glm"           # 智谱GLM-5
    MINIMAX = "minimax"   # MiniMax M2.5系列


@dataclass
class ProviderConfig:
    """服务商配置"""
    provider: AIProvider
    api_key: str
    base_url: str
    default_model: str
    models: List[str] = field(default_factory=list)
    enabled: bool = True

    def __post_init__(self):
        if not self.models:
            self.models = [self.default_model]


class AIGatewayV2:
    """AI模型控制网关 2.0（单例模式）"""

    _instance: Optional[AIGatewayV2] = None

    def __new__(cls):
        """确保单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化网关"""
        if self._initialized:
            return
        self._initialized = True

        self.providers: Dict[str, ProviderConfig] = {}
        self.clients: Dict[str, OpenAI] = {}
        self.current_provider: Optional[str] = None
        self.current_model: Optional[str] = None

        # 从环境变量加载配置
        self._load_from_env()

    @classmethod
    def get_instance(cls) -> AIGatewayV2:
        """获取网关单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def _reset_instance(cls) -> None:
        """重置单例实例（仅供测试使用）"""
        cls._instance = None

    def _load_from_env(self) -> None:
        """从环境变量加载配置"""
        # 加载GLM-5
        glm_key = os.getenv("GLM_API_KEY")
        if glm_key:
            self.register_provider(
                provider="glm",
                api_key=glm_key,
                base_url=os.getenv("GLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
                default_model="glm-5",
            )
            logger.info("✅ GLM-5已注册")

        # 加载MiniMax
        minimax_key = os.getenv("MINIMAX_API_KEY")
        if minimax_key:
            self.register_provider(
                provider="minimax",
                api_key=minimax_key,
                base_url=os.getenv("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1"),
                default_model="MiniMax-M2.5-highspeed",
                models=[
                    "MiniMax-M2.5",
                    "MiniMax-M2.5-highspeed",
                    "MiniMax-M2.1",
                    "MiniMax-M2.1-highspeed",
                    "MiniMax-M2",
                ]
            )
            logger.info("✅ MiniMax M2.5已注册")

    def register_provider(
        self,
        provider: str,
        api_key: str,
        base_url: str,
        default_model: str,
        models: Optional[List[str]] = None,
        enabled: bool = True,
    ) -> None:
        """注册一个服务商

        Args:
            provider: 服务商名称 (glm/minimax)
            api_key: API密钥
            base_url: API基础URL
            default_model: 默认模型
            models: 支持的模型列表
            enabled: 是否启用
        """
        provider = provider.lower()

        config = ProviderConfig(
            provider=AIProvider(provider),
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
            models=models or [],
            enabled=enabled,
        )

        self.providers[provider] = config

        # 创建OpenAI客户端
        if OpenAI and enabled:
            try:
                self.clients[provider] = OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )
                logger.info(f"AI服务商已注册: {provider} (模型: {config.default_model})")
            except Exception as e:
                logger.error(f"创建 {provider} 客户端失败: {e}")
                config.enabled = False

    def switch_provider(
        self,
        provider: str,
        model: Optional[str] = None,
    ) -> None:
        """切换当前服务商和模型

        Args:
            provider: 服务商名称
            model: 模型名称（为空则使用该服务商的默认模型）

        Raises:
            ValueError: 服务商未注册或已禁用
        """
        provider = provider.lower()

        if provider not in self.providers:
            raise ValueError(f"未注册的服务商: {provider}")

        config = self.providers[provider]
        if not config.enabled:
            raise ValueError(f"服务商已禁用: {provider}")

        self.current_provider = provider
        self.current_model = model or config.default_model

        logger.info(f"已切换至: {provider} / {self.current_model}")


# 便捷函数
def get_gateway() -> AIGatewayV2:
    """获取网关实例"""
    return AIGatewayV2.get_instance()
