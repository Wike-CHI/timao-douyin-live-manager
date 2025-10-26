"""
AI 模型控制网关

统一管理多个 AI 服务商（通义千问、OpenAI、DeepSeek等），支持：
- 一键切换服务商和模型
- 自动降级和容错
- 统一的调用接口
- 集成成本监控

使用示例：
    gateway = AIGateway.get_instance()
    
    # 方法1：使用当前默认配置
    response = gateway.chat_completion(messages=[...])
    
    # 方法2：临时指定服务商
    response = gateway.chat_completion(
        messages=[...],
        provider="openai",
        model="gpt-4"
    )
    
    # 方法3：切换全局默认配置
    gateway.switch_provider("deepseek", model="deepseek-chat")
"""

from __future__ import annotations

import os
import time
import logging
from typing import Any, Dict, List, Optional, Literal
from dataclasses import dataclass, field
from enum import Enum

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    """AI 服务商枚举"""
    QWEN = "qwen"           # 通义千问
    OPENAI = "openai"       # OpenAI
    DEEPSEEK = "deepseek"   # DeepSeek
    DOUBAO = "doubao"       # 字节豆包
    GLM = "glm"             # 智谱 ChatGLM


@dataclass
class ProviderConfig:
    """服务商配置"""
    provider: AIProvider
    api_key: str
    base_url: str
    default_model: str
    models: List[str] = field(default_factory=list)
    enabled: bool = True
    timeout: int = 30
    max_retries: int = 2
    
    def __post_init__(self):
        if not self.models:
            self.models = [self.default_model]


@dataclass
class AIResponse:
    """统一的 AI 响应格式"""
    content: str
    model: str
    provider: str
    usage: Dict[str, int]  # {prompt_tokens, completion_tokens, total_tokens}
    cost: float
    duration_ms: float
    success: bool = True
    error: Optional[str] = None


class AIGateway:
    """AI 模型控制网关（单例模式）"""
    
    _instance: Optional[AIGateway] = None
    
    # 内置服务商配置模板
    PROVIDER_TEMPLATES = {
        AIProvider.QWEN: {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_model": "qwen-plus",
            "models": ["qwen-plus", "qwen-turbo", "qwen-max", "qwen-max-longcontext"],
        },
        AIProvider.OPENAI: {
            "base_url": "https://api.openai.com/v1",
            "default_model": "gpt-3.5-turbo",
            "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"],
        },
        AIProvider.DEEPSEEK: {
            "base_url": "https://api.deepseek.com/v1",
            "default_model": "deepseek-chat",
            "models": ["deepseek-chat", "deepseek-coder"],
        },
        AIProvider.DOUBAO: {
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "default_model": "doubao-pro",
            "models": ["doubao-pro", "doubao-lite"],
        },
        AIProvider.GLM: {
            "base_url": "https://open.bigmodel.cn/api/paas/v4",
            "default_model": "glm-4",
            "models": ["glm-4", "glm-3-turbo"],
        },
    }
    
    def __init__(self):
        """初始化网关（私有，使用 get_instance() 获取单例）"""
        self.providers: Dict[str, ProviderConfig] = {}
        self.clients: Dict[str, OpenAI] = {}
        self.current_provider: Optional[str] = None
        self.current_model: Optional[str] = None
        self.fallback_chain: List[str] = []
        
        # 从环境变量加载配置
        self._load_from_env()
        
    @classmethod
    def get_instance(cls) -> AIGateway:
        """获取网关单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _load_from_env(self) -> None:
        """从环境变量加载配置"""
        # 主服务商配置（向后兼容）
        primary_provider = os.getenv("AI_SERVICE", "qwen").lower()
        primary_api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY", "")
        primary_base_url = os.getenv("AI_BASE_URL") or os.getenv("OPENAI_BASE_URL", "")
        primary_model = os.getenv("AI_MODEL") or os.getenv("OPENAI_MODEL", "qwen-plus")
        
        # 注册主服务商
        if primary_api_key:
            self.register_provider(
                provider=primary_provider,
                api_key=primary_api_key,
                base_url=primary_base_url,
                default_model=primary_model,
            )
            self.switch_provider(primary_provider, primary_model)
        
        # 加载其他服务商配置（可选）
        self._load_additional_providers()
        
    def _load_additional_providers(self) -> None:
        """加载额外的服务商配置"""
        # DeepSeek
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            self.register_provider(
                provider="deepseek",
                api_key=deepseek_key,
                base_url=os.getenv("DEEPSEEK_BASE_URL"),
            )
        
        # 豆包
        doubao_key = os.getenv("DOUBAO_API_KEY")
        if doubao_key:
            self.register_provider(
                provider="doubao",
                api_key=doubao_key,
                base_url=os.getenv("DOUBAO_BASE_URL"),
            )
        
        # ChatGLM
        glm_key = os.getenv("GLM_API_KEY")
        if glm_key:
            self.register_provider(
                provider="glm",
                api_key=glm_key,
                base_url=os.getenv("GLM_BASE_URL"),
            )
    
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
        
        Args:
            provider: 服务商名称 (qwen/openai/deepseek/doubao/glm)
            api_key: API密钥
            base_url: API基础URL（为空则使用默认值）
            default_model: 默认模型（为空则使用预设值）
            models: 支持的模型列表
            enabled: 是否启用
        """
        provider = provider.lower()
        
        # 获取模板配置
        template = self.PROVIDER_TEMPLATES.get(AIProvider(provider), {})
        
        config = ProviderConfig(
            provider=AIProvider(provider),
            api_key=api_key,
            base_url=base_url or template.get("base_url", ""),
            default_model=default_model or template.get("default_model", ""),
            models=models or template.get("models", []),
            enabled=enabled,
        )
        
        self.providers[provider] = config
        
        # 创建客户端
        if OpenAI and enabled:
            try:
                self.clients[provider] = OpenAI(
                    api_key=api_key,
                    base_url=config.base_url or None,
                    timeout=config.timeout,
                    max_retries=config.max_retries,
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
    
    def set_fallback_chain(self, providers: List[str]) -> None:
        """设置服务商降级链
        
        当主服务失败时，按顺序尝试备用服务商
        
        Args:
            providers: 服务商列表，按优先级排序
        """
        self.fallback_chain = [p.lower() for p in providers if p.lower() in self.providers]
        logger.info(f"降级链已设置: {' -> '.join(self.fallback_chain)}")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> AIResponse:
        """统一的对话补全接口
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            provider: 临时指定服务商（为空则使用当前默认）
            model: 临时指定模型（为空则使用当前默认）
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式（如 {"type": "json_object"}）
            **kwargs: 其他参数
            
        Returns:
            AIResponse: 统一响应对象
        """
        # 确定使用的服务商和模型
        target_provider = (provider or self.current_provider or "").lower()
        target_model = model or self.current_model
        
        if not target_provider or target_provider not in self.providers:
            raise ValueError(f"无效的服务商: {target_provider}")
        
        # 尝试主服务商
        try:
            return self._call_provider(
                provider=target_provider,
                model=target_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                **kwargs,
            )
        except Exception as e:
            logger.warning(f"{target_provider} 调用失败: {e}")
            
            # 尝试降级链
            if self.fallback_chain:
                for fallback_provider in self.fallback_chain:
                    if fallback_provider == target_provider:
                        continue
                    try:
                        logger.info(f"尝试降级到: {fallback_provider}")
                        fallback_config = self.providers[fallback_provider]
                        return self._call_provider(
                            provider=fallback_provider,
                            model=fallback_config.default_model,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            response_format=response_format,
                            **kwargs,
                        )
                    except Exception as fallback_error:
                        logger.warning(f"{fallback_provider} 降级失败: {fallback_error}")
                        continue
            
            # 所有服务都失败
            return AIResponse(
                content="",
                model=target_model or "",
                provider=target_provider,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                cost=0.0,
                duration_ms=0.0,
                success=False,
                error=str(e),
            )
    
    def _call_provider(
        self,
        provider: str,
        model: Optional[str],
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> AIResponse:
        """调用指定服务商"""
        start_time = time.time()
        
        config = self.providers[provider]
        client = self.clients.get(provider)
        
        if not client:
            raise RuntimeError(f"{provider} 客户端未初始化")
        
        actual_model = model or config.default_model
        
        # 调用 API
        response = client.chat.completions.create(
            model=actual_model,
            messages=messages,  # type: ignore
            **kwargs,
        )
        
        duration_ms = (time.time() - start_time) * 1000
        
        # 提取数据
        content = response.choices[0].message.content or ""
        usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        }
        
        # 计算成本
        cost = self._calculate_cost(provider, actual_model, usage)
        
        # 记录到监控（可选）
        self._record_usage(
            provider=provider,
            model=actual_model,
            usage=usage,
            cost=cost,
            duration_ms=duration_ms,
        )
        
        return AIResponse(
            content=content,
            model=actual_model,
            provider=provider,
            usage=usage,
            cost=cost,
            duration_ms=duration_ms,
            success=True,
        )
    
    def _calculate_cost(
        self,
        provider: str,
        model: str,
        usage: Dict[str, int],
    ) -> float:
        """计算调用成本"""
        # 导入定价模块
        try:
            from server.utils.ai_usage_monitor import ModelPricing
            pricing = ModelPricing.get_pricing(model)
            if pricing:
                input_cost = (usage["prompt_tokens"] / 1000) * pricing["input"]
                output_cost = (usage["completion_tokens"] / 1000) * pricing["output"]
                return input_cost + output_cost
        except Exception as e:
            logger.debug(f"成本计算失败: {e}")
        
        return 0.0
    
    def _record_usage(
        self,
        provider: str,
        model: str,
        usage: Dict[str, int],
        cost: float,
        duration_ms: float,
    ) -> None:
        """记录使用情况到监控系统"""
        try:
            from server.utils.ai_usage_monitor import record_ai_usage
            record_ai_usage(
                model=model,
                function=f"gateway_{provider}",
                input_tokens=usage["prompt_tokens"],
                output_tokens=usage["completion_tokens"],
                cost=cost,
                duration_ms=duration_ms,
                success=True,
            )
        except Exception as e:
            logger.debug(f"记录使用情况失败: {e}")
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前配置信息"""
        if not self.current_provider:
            return {"error": "未配置服务商"}
        
        config = self.providers[self.current_provider]
        return {
            "provider": self.current_provider,
            "model": self.current_model,
            "base_url": config.base_url,
            "available_models": config.models,
            "enabled": config.enabled,
            "fallback_chain": self.fallback_chain,
        }
    
    def list_providers(self) -> Dict[str, Dict[str, Any]]:
        """列出所有已注册的服务商"""
        return {
            name: {
                "provider": config.provider.value,
                "base_url": config.base_url,
                "default_model": config.default_model,
                "models": config.models,
                "enabled": config.enabled,
            }
            for name, config in self.providers.items()
        }


# 便捷函数
def get_gateway() -> AIGateway:
    """获取网关实例"""
    return AIGateway.get_instance()
