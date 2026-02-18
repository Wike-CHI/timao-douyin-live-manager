"""AI Gateway 兼容层

提供旧版AIGateway接口的兼容性支持，内部使用AIGatewayV2实现。
这是一个临时迁移方案，新代码应直接使用AIGatewayV2。

Migration Guide (迁移指南):
===========================

旧代码 (Old Code):
    from server.ai.ai_gateway import get_gateway, AIResponse
    gateway = get_gateway()
    response = gateway.chat_completion(messages=[...], function="live_analysis")
    if response.success:
        content = response.content

新代码 (New Code):
    from server.ai.ai_gateway_v2 import get_gateway
    gateway = get_gateway()
    gateway.switch_provider("glm", "glm-5")  # 或使用 smart_route
    result = gateway.chat_completion(messages=[...], enable_thinking=True)
    content = result["content"]
    reasoning = result["reasoning"]

兼容层用法 (Compatibility Layer Usage):
    # 保持旧代码不变，只需更改导入
    from server.ai.ai_gateway_compat import get_gateway, AIResponse
    # 其余代码无需修改

Version History:
- v1.0: 初始版本，支持基本的 chat_completion 兼容
"""
from __future__ import annotations

import time
import logging
from typing import Any, Dict, List, Optional, Literal
from dataclasses import dataclass

# 从 V2 导入核心功能
from server.ai.ai_gateway_v2 import AIGatewayV2, get_gateway as get_gateway_v2

logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """统一的 AI 响应格式 (兼容旧版)

    这是一个兼容性数据类，用于保持与旧代码的兼容性。
    新代码应直接使用 AIGatewayV2 返回的字典格式。
    """
    content: str
    model: str
    provider: str
    usage: Dict[str, int]  # {prompt_tokens, completion_tokens, total_tokens}
    cost: float
    duration_ms: float
    success: bool = True
    error: Optional[str] = None


class AIProvider:
    """AI 服务商枚举 (兼容旧版)

    注意: V2 仅支持 GLM 和 MiniMax，旧代码使用的其他服务商
    需要通过环境变量配置到 V1 网关。
    """
    GLM = "glm"
    MINIMAX = "minimax"

    # 向后兼容的别名
    QWEN = "qwen"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    DOUBAO = "doubao"
    GEMINI = "gemini"
    XUNFEI = "xunfei"


class AIGatewayCompat:
    """AI Gateway 兼容层

    将旧的 AIResponse 接口包装到新的 AIGatewayV2 上。
    这个类只在内部使用，外部代码应使用 get_gateway() 函数。
    """

    def __init__(self):
        self._v2 = get_gateway_v2()
        self._v1 = None  # 延迟加载 V1 网关用于兼容旧服务商
        self._initialized = True

    @property
    def v2(self) -> AIGatewayV2:
        """获取 V2 网关实例"""
        return self._v2

    @property
    def v1(self):
        """获取 V1 网关实例 (延迟加载，用于兼容旧服务商)"""
        if self._v1 is None:
            try:
                from server.ai.ai_gateway import AIGateway
                self._v1 = AIGateway.get_instance()
            except Exception as e:
                logger.warning(f"无法加载 V1 网关: {e}")
                self._v1 = None
        return self._v1

    @property
    def current_provider(self) -> Optional[str]:
        """当前服务商"""
        return self._v2.current_provider

    @property
    def current_model(self) -> Optional[str]:
        """当前模型"""
        return self._v2.current_model

    @property
    def providers(self) -> Dict[str, Any]:
        """已注册的服务商列表"""
        # 合并 V2 和 V1 的服务商信息
        result = {}

        # V2 服务商
        for name, config in self._v2.providers.items():
            result[name] = {
                "provider": config.provider.value,
                "base_url": config.base_url,
                "default_model": config.default_model,
                "models": config.models,
                "enabled": config.enabled,
            }

        # V1 服务商 (如果有)
        if self.v1:
            for name, config in self.v1.providers.items():
                if name not in result:
                    result[name] = {
                        "provider": config.provider.value,
                        "base_url": config.base_url,
                        "default_model": config.default_model,
                        "models": config.models,
                        "enabled": config.enabled,
                    }

        return result

    # 功能级别的默认模型配置 (委托给 V1)
    FUNCTION_MODELS = {
        "live_analysis": {"provider": "minimax", "model": "MiniMax-M2.5-highspeed"},
        "style_profile": {"provider": "glm", "model": "glm-5"},
        "script_generation": {"provider": "glm", "model": "glm-5"},
        "live_review": {"provider": "minimax", "model": "MiniMax-M2.5"},
        "chat_focus": {"provider": "minimax", "model": "MiniMax-M2.5-highspeed"},
        "topic_generation": {"provider": "glm", "model": "glm-5"},
    }

    def get_function_config(self, function: str) -> Optional[Dict[str, str]]:
        """获取指定功能的默认配置

        优先使用 V2 的智能路由，否则使用 FUNCTION_MODELS
        """
        # 检查 V1 的配置
        if self.v1 and hasattr(self.v1, 'get_function_config'):
            v1_config = self.v1.get_function_config(function)
            if v1_config:
                return v1_config

        # 使用 V2 兼容配置
        return self.FUNCTION_MODELS.get(function)

    def list_function_configs(self) -> Dict[str, Dict[str, str]]:
        """列出所有功能的默认配置"""
        # 合并 V1 和 V2 的配置
        result = self.FUNCTION_MODELS.copy()

        if self.v1 and hasattr(self.v1, 'list_function_configs'):
            v1_configs = self.v1.list_function_configs()
            result.update(v1_configs)

        return result

    def switch_provider(self, provider: str, model: Optional[str] = None) -> None:
        """切换当前服务商和模型

        优先尝试 V2，如果服务商不支持则委托给 V1
        """
        provider_lower = provider.lower()

        # V2 支持的服务商
        if provider_lower in {"glm", "minimax"}:
            self._v2.switch_provider(provider_lower, model)
            logger.info(f"✅ 使用 AIGatewayV2: {provider_lower}/{model or 'default'}")
        elif self.v1:
            # 委托给 V1
            self.v1.switch_provider(provider, model)
            logger.info(f"✅ 使用 AIGatewayV1 (兼容模式): {provider}/{model or 'default'}")
        else:
            raise ValueError(f"不支持的服务商: {provider}")

    def register_provider(
        self,
        provider: str,
        api_key: str,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
        models: Optional[List[str]] = None,
        enabled: bool = True,
    ) -> None:
        """注册一个服务商

        V2 服务商直接注册到 V2，其他委托给 V1
        """
        provider_lower = provider.lower()

        if provider_lower in {"glm", "minimax"}:
            self._v2.register_provider(
                provider=provider_lower,
                api_key=api_key,
                base_url=base_url or "",
                default_model=default_model or "",
                models=models or [],
                enabled=enabled,
            )
        elif self.v1:
            self.v1.register_provider(
                provider=provider,
                api_key=api_key,
                base_url=base_url,
                default_model=default_model,
                models=models,
                enabled=enabled,
            )
        else:
            logger.warning(f"无法注册服务商 {provider}: V1 网关不可用")

    def unregister_provider(self, provider: str) -> None:
        """删除一个服务商"""
        provider_lower = provider.lower()

        if provider_lower in self._v2.providers:
            if provider_lower in self._v2.providers:
                del self._v2.providers[provider_lower]
            if provider_lower in self._v2.clients:
                del self._v2.clients[provider_lower]
        elif self.v1:
            self.v1.unregister_provider(provider)

    def update_provider_api_key(self, provider: str, api_key: str) -> None:
        """更新服务商的 API Key"""
        provider_lower = provider.lower()

        if provider_lower in self._v2.providers:
            config = self._v2.providers[provider_lower]
            config.api_key = api_key
            # 重新创建客户端
            try:
                from openai import OpenAI
                self._v2.clients[provider_lower] = OpenAI(
                    api_key=api_key,
                    base_url=config.base_url
                )
            except Exception as e:
                logger.error(f"更新 {provider} API Key 失败: {e}")
                config.enabled = False
        elif self.v1:
            self.v1.update_provider_api_key(provider, api_key)

    def list_providers(self) -> Dict[str, Dict[str, Any]]:
        """列出所有已注册的服务商"""
        return self.providers

    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置信息"""
        if self._v2.current_provider:
            return {
                "provider": self._v2.current_provider,
                "model": self._v2.current_model,
                "base_url": self._v2.providers[self._v2.current_provider].base_url if self._v2.current_provider in self._v2.providers else "",
                "available_models": self._v2.providers[self._v2.current_provider].models if self._v2.current_provider in self._v2.providers else [],
                "enabled": self._v2.providers[self._v2.current_provider].enabled if self._v2.current_provider in self._v2.providers else False,
            }
        elif self.v1:
            return self.v1.get_current_config()
        else:
            return {"error": "未配置服务商"}

    def update_function_config(
        self,
        function: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        """更新指定功能的默认配置"""
        if function in self.FUNCTION_MODELS:
            if provider:
                self.FUNCTION_MODELS[function]["provider"] = provider.lower()
            if model:
                self.FUNCTION_MODELS[function]["model"] = model

        # 同时更新 V1 的配置
        if self.v1 and hasattr(self.v1, 'update_function_config'):
            try:
                self.v1.update_function_config(function, provider, model)
            except Exception as e:
                logger.warning(f"更新 V1 功能配置失败: {e}")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        function: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> AIResponse:
        """统一的对话补全接口 (兼容旧版)

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            provider: 临时指定服务商（为空则使用功能默认或当前默认）
            model: 临时指定模型（为空则使用功能默认或当前默认）
            function: 功能标识（live_analysis/style_profile/script_generation/live_review）
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式（如 {"type": "json_object"}）
            **kwargs: 其他参数

        Returns:
            AIResponse: 统一响应对象 (兼容旧版)
        """
        start_time = time.time()

        # 确定使用哪个服务商
        target_provider = provider
        target_model = model

        # 如果指定了功能但没有指定provider和model，则使用功能级别的默认配置
        if function and not provider and not model:
            func_config = self.get_function_config(function)
            if func_config:
                target_provider = func_config.get("provider", "")
                target_model = func_config.get("model")

        # 如果还是没有指定，使用当前配置
        if not target_provider:
            target_provider = self._v2.current_provider or ""
        if not target_model:
            target_model = self._v2.current_model

        provider_lower = (target_provider or "").lower()

        # 判断是否应该使用 V2
        use_v2 = provider_lower in {"glm", "minimax"}

        if use_v2:
            # 使用 V2 网关
            return self._chat_completion_v2(
                messages=messages,
                provider=provider_lower,
                model=target_model,
                temperature=temperature,
                max_tokens=max_tokens or 4096,
                response_format=response_format,
                start_time=start_time,
                **kwargs,
            )
        elif self.v1:
            # 委托给 V1 网关
            return self.v1.chat_completion(
                messages=messages,
                provider=provider,
                model=model,
                function=function,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                **kwargs,
            )
        else:
            # 无可用网关
            return AIResponse(
                content="",
                model=target_model or "",
                provider=target_provider or "",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                cost=0.0,
                duration_ms=(time.time() - start_time) * 1000,
                success=False,
                error=f"不支持的服务商: {target_provider}",
            )

    def _chat_completion_v2(
        self,
        messages: List[Dict[str, str]],
        provider: str,
        model: Optional[str],
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, str]],
        start_time: float,
        **kwargs,
    ) -> AIResponse:
        """使用 V2 网关进行 chat_completion 并转换为旧版响应格式"""
        try:
            # 确保服务商已切换
            if self._v2.current_provider != provider:
                self._v2.switch_provider(provider, model)

            # 调用 V2
            result = self._v2.chat_completion(
                messages=messages,
                model=model,
                enable_thinking=kwargs.get("enable_thinking", False),
                temperature=temperature,
                max_tokens=max_tokens,
            )

            duration_ms = (time.time() - start_time) * 1000

            # 构建兼容响应
            content = result.get("content", "")

            # 估算 token (V2 不返回 usage，需要估算)
            # 粗略估算: 中文约 0.5 token/字符，英文约 0.25 token/字符
            prompt_chars = sum(len(m.get("content", "")) for m in messages)
            completion_chars = len(content)

            # 简单估算
            prompt_tokens = int(prompt_chars * 0.4)
            completion_tokens = int(completion_chars * 0.4)
            total_tokens = prompt_tokens + completion_tokens

            usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            }

            # 记录日志
            logger.info(
                f"🚀 AI网关V2调用: provider={provider}, model={model or self._v2.current_model}, "
                f"tokens={total_tokens}, duration={duration_ms:.1f}ms"
            )

            return AIResponse(
                content=content,
                model=model or self._v2.current_model or "unknown",
                provider=provider,
                usage=usage,
                cost=0.0,  # V2 暂不支持成本计算
                duration_ms=duration_ms,
                success=True,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"V2 网关调用失败: {e}")

            return AIResponse(
                content="",
                model=model or "",
                provider=provider,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                cost=0.0,
                duration_ms=duration_ms,
                success=False,
                error=str(e),
            )


# 全局单例
_instance: Optional[AIGatewayCompat] = None


def get_gateway() -> AIGatewayCompat:
    """获取网关实例 (兼容旧版)

    这个函数保持与旧代码的完全兼容性。
    """
    global _instance
    if _instance is None:
        _instance = AIGatewayCompat()
    return _instance


# 向后兼容的别名
AIGateway = AIGatewayCompat

# 导出的符号
__all__ = [
    'AIGateway',
    'AIGatewayCompat',
    'AIGatewayV2',
    'AIProvider',
    'AIResponse',
    'get_gateway',
    'get_gateway_v2',
]
