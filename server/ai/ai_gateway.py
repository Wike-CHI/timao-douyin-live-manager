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
    from openai import OpenAI  # pyright: ignore[reportMissingImports]
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
    GEMINI = "gemini"       # Google Gemini (通过 AiHubMix)
    XUNFEI = "xunfei"       # 科大讯飞星火


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
    
    # 功能级别的默认模型配置
    # 这些配置可以通过环境变量覆盖：
    # AI_FUNCTION_LIVE_ANALYSIS_PROVIDER, AI_FUNCTION_LIVE_ANALYSIS_MODEL
    # AI_FUNCTION_STYLE_PROFILE_PROVIDER, AI_FUNCTION_STYLE_PROFILE_MODEL
    # AI_FUNCTION_SCRIPT_GENERATION_PROVIDER, AI_FUNCTION_SCRIPT_GENERATION_MODEL
    # AI_FUNCTION_LIVE_REVIEW_PROVIDER, AI_FUNCTION_LIVE_REVIEW_MODEL
    FUNCTION_MODELS = {
        "live_analysis": {
            "provider": os.getenv("AI_FUNCTION_LIVE_ANALYSIS_PROVIDER", "qwen"), # 已修正为 xunfei
            "model": os.getenv("AI_FUNCTION_LIVE_ANALYSIS_MODEL", "qwen3-max")      # 已修正为 lite
        },
        "style_profile": {
            "provider": os.getenv("AI_FUNCTION_STYLE_PROFILE_PROVIDER", "qwen"),
            "model": os.getenv("AI_FUNCTION_STYLE_PROFILE_MODEL", "qwen3-max")  # 直播间氛围与情绪识别：使用 qwen3-max
        },
        "script_generation": {
            "provider": os.getenv("AI_FUNCTION_SCRIPT_GENERATION_PROVIDER", "qwen"),
            "model": os.getenv("AI_FUNCTION_SCRIPT_GENERATION_MODEL", "qwen3-max")  # 话术生成：使用 qwen3-max
        },
        "live_review": {
            "provider": os.getenv("AI_FUNCTION_LIVE_REVIEW_PROVIDER", "gemini"),
            "model": os.getenv("AI_FUNCTION_LIVE_REVIEW_MODEL", "gemini-2.5-flash-preview-09-2025")  # 复盘：使用 Gemini 2.5 Flash Preview
        },
        "chat_focus": {
            "provider": os.getenv("AI_FUNCTION_CHAT_FOCUS_PROVIDER", "qwen"),
            "model": os.getenv("AI_FUNCTION_CHAT_FOCUS_MODEL", "qwen3-max")  # 聊天焦点摘要：使用 qwen3-max
        },
        "topic_generation": {
            "provider": os.getenv("AI_FUNCTION_TOPIC_GENERATION_PROVIDER", "qwen"),
            "model": os.getenv("AI_FUNCTION_TOPIC_GENERATION_MODEL", "qwen3-max")  # 智能话题生成：使用 qwen3-max
        },
    }
    
    # 内置服务商配置模板
    PROVIDER_TEMPLATES = {
        AIProvider.XUNFEI: {
            "base_url": "https://spark-api-open.xf-yun.com/v1",
            "default_model": "lite",
            "models": ["lite", "generalv3", "generalv3.5", "4.0Ultra"],
        },
        AIProvider.QWEN: {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "default_model": "qwen-plus",
            "models": ["qwen-plus", "qwen-turbo", "qwen-max", "qwen-max-longcontext", "qwen3-max"],
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
        AIProvider.GEMINI: {
            "base_url": "https://aihubmix.com/v1",
            "default_model": "gemini-2.5-flash-preview-09-2025",
            "models": ["gemini-2.5-flash-preview-09-2025"],
        },
    }
    
    def __init__(self):
        """初始化网关（私有，使用 get_instance() 获取单例）"""
        self.providers: Dict[str, ProviderConfig] = {}
        self.clients: Dict[str, OpenAI] = {}
        self.current_provider: Optional[str] = None
        self.current_model: Optional[str] = None
        
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
        # 主服务商配置（向后兼容）- 默认使用讯飞 lite
        primary_provider = os.getenv("AI_SERVICE", "xunfei").lower()
        primary_api_key = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY", "")
        primary_base_url = os.getenv("AI_BASE_URL") or os.getenv("OPENAI_BASE_URL", "")
        primary_model = os.getenv("AI_MODEL") or os.getenv("OPENAI_MODEL", "lite")
        
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
        # 科大讯飞（优先加载）
        xunfei_key = os.getenv("XUNFEI_API_KEY")
        if xunfei_key:
            self.register_provider(
                provider="xunfei",
                api_key=xunfei_key,
                base_url=os.getenv("XUNFEI_BASE_URL"),
                default_model=os.getenv("XUNFEI_MODEL", "lite"),
            )
            cfg = self.providers.get("xunfei")
            if cfg:
                logger.info(f"✅ 已注册讯飞(Xunfei)提供商: base_url={cfg.base_url} 默认模型={cfg.default_model}")
            else:  # pragma: no cover
                logger.warning("⚠️ 讯飞提供商注册后未找到配置对象，可能初始化失败")
        
        # 通义千问
        qwen_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
        if qwen_key:
            self.register_provider(
                provider="qwen",
                api_key=qwen_key,
                base_url=os.getenv("QWEN_BASE_URL"),
                default_model=os.getenv("QWEN_MODEL", "qwen-plus"),
            )
        
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
        
        # Gemini (通过 AiHubMix)
        gemini_key = os.getenv("AIHUBMIX_API_KEY") or os.getenv("GEMINI_API_KEY")
        if gemini_key:
            self.register_provider(
                provider="gemini",
                api_key=gemini_key,
                base_url=os.getenv("AIHUBMIX_BASE_URL"),
                default_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-09-2025"),
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
                # 使用最小化参数配置，避免兼容性问题
                # OpenAI 1.52.2+ 不支持某些旧参数
                client_kwargs = {
                    "api_key": api_key,
                }
                
                # 只在有值时添加 base_url
                if config.base_url:
                    client_kwargs["base_url"] = config.base_url
                
                # 创建客户端（不传递 timeout 和 max_retries，使用默认值）
                self.clients[provider] = OpenAI(**client_kwargs)
                logger.info(f"AI服务商已注册: {provider} (模型: {config.default_model})")
            except Exception as e:
                logger.error(f"创建 {provider} 客户端失败: {e}")
                logger.debug(f"客户端参数: {client_kwargs}")
                import traceback
                logger.debug(f"详细错误: {traceback.format_exc()}")
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
    
    def unregister_provider(self, provider: str) -> None:
        """删除一个服务商
        
        Args:
            provider: 服务商名称
        """
        provider = provider.lower()
        
        if provider not in self.providers:
            raise ValueError(f"服务商不存在: {provider}")
        
        # 如果是当前使用的服务商，不允许删除
        if provider == self.current_provider:
            raise ValueError(f"无法删除当前正在使用的服务商: {provider}")
        
        # 删除配置和客户端
        del self.providers[provider]
        if provider in self.clients:
            del self.clients[provider]
        
        logger.info(f"服务商已删除: {provider}")
    
    def update_provider_api_key(
        self,
        provider: str,
        api_key: str,
    ) -> None:
        """更新服务商的 API Key
        
        Args:
            provider: 服务商名称
            api_key: 新的 API 密钥
        """
        provider = provider.lower()
        
        if provider not in self.providers:
            raise ValueError(f"服务商不存在: {provider}")
        
        config = self.providers[provider]
        config.api_key = api_key
        
        # 重新创建客户端
        if OpenAI and config.enabled:
            try:
                # 使用最小化参数配置，避免兼容性问题
                client_kwargs = {
                    "api_key": api_key,
                }
                
                # 只在有值时添加 base_url
                if config.base_url:
                    client_kwargs["base_url"] = config.base_url
                
                # 创建客户端（不传递 timeout 和 max_retries，使用默认值）
                self.clients[provider] = OpenAI(**client_kwargs)
                logger.info(f"服务商 {provider} 的 API Key 已更新")
            except Exception as e:
                logger.error(f"更新 {provider} API Key 失败: {e}")
                config.enabled = False
                raise
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        function: Optional[str] = None,  # 功能标识：live_analysis, style_profile, script_generation, live_review
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> AIResponse:
        """统一的对话补全接口
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            provider: 临时指定服务商（为空则使用功能默认或当前默认）
            model: 临时指定模型（为空则使用功能默认或当前默认）
            function: 功能标识（live_analysis/style_profile/script_generation/live_review），用于自动选择默认模型
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式（如 {"type": "json_object"}）
            **kwargs: 其他参数
            
        Returns:
            AIResponse: 统一响应对象
        """
        # 如果指定了功能，但没有指定provider和model，则使用功能级别的默认配置
        if function and function in self.FUNCTION_MODELS and not provider and not model:
            func_config = self.FUNCTION_MODELS[function]
            target_provider = func_config["provider"].lower()
            target_model = func_config["model"]
        else:
            # 确定使用的服务商和模型
            target_provider = (provider or self.current_provider or "").lower()
            target_model = model or self.current_model

        # 调试日志（仅在 xunfei 或显式开启 AI_DEBUG 时输出）
        if os.getenv("AI_DEBUG") == "1" or target_provider == "xunfei":
            logger.debug(
                "[GatewayDebug] function=%s provider=%s model=%s has_response_format=%s messages_len=%d",
                function,
                target_provider,
                target_model,
                bool(response_format),
                len(messages),
            )
        
        if not target_provider or target_provider not in self.providers:
            return AIResponse(
                content="",
                model=target_model or "",
                provider=target_provider,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                cost=0.0,
                duration_ms=0.0,
                success=False,
                error=f"无效的服务商: {target_provider}",
            )

        # 校验模型是否存在于当前服务商支持列表，若不存在则自动降级为默认模型
        provider_cfg = self.providers[target_provider]
        if target_model and target_model not in provider_cfg.models:
            logger.warning(
                f"模型 {target_model} 不在服务商 {target_provider} 支持列表 {provider_cfg.models} 中，自动降级为 {provider_cfg.default_model}"
            )
            target_model = provider_cfg.default_model

        # 对 xunfei 的消息长度/字符数做基本统计，便于定位 404 来源（可能与超长提示相关）
        if target_provider == "xunfei":
            try:
                total_chars = sum(len(m.get("content", "")) for m in messages)
                if total_chars > 8000:
                    logger.info(f"讯飞提示总字数较长: {total_chars} chars (可能需要截断避免兼容层异常)")
            except Exception:
                pass
        
        # 直接调用，不做降级；对讯飞进行 response_format 兼容性回退（部分模型不支持该参数会触发 404）
        if target_provider == "xunfei" and response_format:
            try:
                return self._call_provider(
                    provider=target_provider,
                    model=target_model,
                    function=function,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                    **kwargs,
                )
            except Exception as e:
                # 捕获 NotFound/兼容失败错误后去掉 response_format 重试
                err_name = type(e).__name__
                if "NotFound" in err_name or "404" in str(e):
                    logger.warning(f"讯飞调用含 response_format 发生 {err_name}: {e} -> 自动回退去除 response_format 重试")
                    try:
                        return self._call_provider(
                            provider=target_provider,
                            model=target_model,
                            function=function,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            **kwargs,
                        )
                    except Exception as e2:
                        logger.error(f"讯飞回退重试仍失败: {type(e2).__name__}: {e2}")
                        return AIResponse(
                            content="",
                            model=target_model or "",
                            provider=target_provider,
                            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                            cost=0.0,
                            duration_ms=0.0,
                            success=False,
                            error=f"Xunfei call failed after fallback: {e2}",
                        )
                else:
                    logger.error(f"讯飞调用发生非404错误: {err_name}: {e}")
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
        # 普通路径
        return self._call_provider(
            provider=target_provider,
            model=target_model,
            function=function,  # 传递功能标识
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            **kwargs,
        )
    
    def _call_provider(
        self,
        provider: str,
        model: Optional[str],
        messages: List[Dict[str, str]],
        function: Optional[str] = None,  # 功能标识
        **kwargs: Any,
    ) -> AIResponse:
        """调用指定服务商"""
        start_time = time.time()
        
        config = self.providers[provider]
        client = self.clients.get(provider)
        
        if not client:
            raise RuntimeError(f"{provider} 客户端未初始化")
        
        actual_model = model or config.default_model
        # 预日志：便于 404 / NotFound 定位
        if os.getenv("AI_DEBUG") == "1" or provider == "xunfei":
            try:
                logger.debug(
                    "[GatewayRequest] provider=%s base_url=%s model=%s messages=%d keys=%s kwargs=%s",
                    provider,
                    config.base_url,
                    actual_model,
                    len(messages),
                    list(messages[0].keys()) if messages else [],
                    list(kwargs.keys()),
                )
            except Exception:  # pragma: no cover
                pass
        
        # 调用 API，增强异常捕获，统一返回 AIResponse 而不是直接抛出导致上层中断
        try:
            oc = client
            try:
                oc = client.with_options(timeout=config.timeout)
            except Exception:
                oc = client
            retries = 0
            while True:
                try:
                    response = oc.chat.completions.create(
                        model=actual_model,
                        messages=messages,  # type: ignore
                        **kwargs,
                    )
                    break
                except Exception as e_inner:
                    err_type_inner = type(e_inner).__name__
                    err_text_inner = str(e_inner)
                    transient = (
                        "timeout" in err_text_inner.lower()
                        or "ServiceUnavailable" in err_type_inner
                        or "RateLimit" in err_type_inner
                        or "429" in err_text_inner
                        or "500" in err_text_inner
                        or "503" in err_text_inner
                    )
                    if not transient or retries >= config.max_retries:
                        raise e_inner
                    wait = min(2 ** retries, 8)
                    time.sleep(wait)
                    retries += 1
        except Exception as e:  # 捕获 openai / 兼容层异常
            err_type = type(e).__name__
            err_text = str(e)
            # 部分 NotFoundError 不带 response，需要主动提示可疑点
            suspected = []
            if "NotFound" in err_type or "404" in err_text:
                # 基于常见错误添加诊断提示
                if config.base_url.endswith("/chat/completions"):
                    suspected.append("base_url 不应包含 /chat/completions，只保留到 /v1")
                if not config.base_url.rstrip("/").endswith("/v1"):
                    suspected.append("base_url 末尾通常需要包含 /v1 (OpenAI 兼容模式)")
                if actual_model not in config.models:
                    suspected.append(f"模型 {actual_model} 不在注册列表 {config.models}")
                if provider == "xunfei" and "response_format" in kwargs:
                    suspected.append("讯飞兼容层可能不支持 response_format，可移除后再试")
            # 输出扩展日志
            logger.error(
                "[GatewayError] provider=%s model=%s base_url=%s type=%s error=%s suspected=%s",
                provider,
                actual_model,
                config.base_url,
                err_type,
                err_text,
                "; ".join(suspected) if suspected else "",
            )
            # 尝试从异常对象提取底层 response 信息（openai 1.x 风格）
            resp = getattr(e, "response", None)
            if resp is not None:
                try:
                    status_code = getattr(resp, "status_code", None)
                    text_body = getattr(resp, "text", None)
                    logger.error("[GatewayErrorHTTP] status=%s body=%s", status_code, text_body[:500] if text_body else None)
                except Exception:  # pragma: no cover
                    pass
            # 返回失败响应，避免直接抛出让上层功能整体失败
            return AIResponse(
                content="",
                model=actual_model,
                provider=provider,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                cost=0.0,
                duration_ms=(time.time() - start_time) * 1000,
                success=False,
                error=f"{err_type}: {err_text}",
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
        
        # 在控制台显示调用信息（网关层）
        function_name = self._get_function_display_name(function, provider)
        duration_sec = duration_ms / 1000.0
        tokens_per_sec = usage["total_tokens"] / duration_sec if duration_sec > 0 else 0
        
        logger.info(
            f"🚀 AI网关调用: {function_name:20s} | "
            f"模型: {actual_model:25s} | "
            f"Provider: {provider:10s}\n"
            f"   └─ Token: {usage['prompt_tokens']:6d}+{usage['completion_tokens']:6d}={usage['total_tokens']:8d} | "
            f"成本: ¥{cost:.6f} | "
            f"耗时: {duration_ms:.1f}ms ({tokens_per_sec:.1f} tokens/s)"
        )
        
        # 记录到监控（可选）
        self._record_usage(
            provider=provider,
            model=actual_model,
            function=function,  # 传递功能标识
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
        """计算调用成本
        
        支持 Gemini 的缓存和搜索定价
        """
        # 导入定价模块
        try:
            from server.utils.ai_usage_monitor import ModelPricing
            pricing = ModelPricing.get_pricing(model)
            if pricing:
                input_cost = (usage["prompt_tokens"] / 1000) * pricing["input"]
                output_cost = (usage["completion_tokens"] / 1000) * pricing["output"]
                total_cost = input_cost + output_cost
                
                # Gemini 模型支持缓存和搜索定价（如果API响应中包含这些信息）
                if "cache_read" in pricing and "cache_read_tokens" in usage:
                    cache_cost = (usage["cache_read_tokens"] / 1000) * pricing["cache_read"]
                    total_cost += cache_cost
                
                if "web_search" in pricing and "web_search_tokens" in usage:
                    search_cost = (usage["web_search_tokens"] / 1000) * pricing["web_search"]
                    total_cost += search_cost
                
                return total_cost
        except Exception as e:
            logger.debug(f"成本计算失败: {e}")
        
        return 0.0
    
    def _get_function_display_name(self, function: Optional[str], provider: str, model: Optional[str] = None) -> str:
        """获取功能显示名称（包含模型信息）"""
        if function:
            function_map = {
                "live_analysis": "实时分析",
                "style_profile": "风格画像与氛围分析",
                "script_generation": "话术生成",
                "live_review": "复盘总结",
            }
            base_name = function_map.get(function, function)
        else:
            # 降级：根据provider推断功能
            if provider == "gemini":
                base_name = "复盘总结"
            elif provider == "xunfei":
                base_name = "实时分析"  # 默认推断
            else:
                base_name = f"AI调用({provider})"
        
        # 添加模型信息以区分不同模型
        if model:
            # 简化模型名称显示
            model_display = model
            if model == "lite":
                model_display = "讯飞lite"
            elif "qwen" in model.lower():
                # 提取qwen模型的简化名称
                if "max" in model.lower():
                    if "3" in model or "qwen3" in model.lower():
                        model_display = "qwen3-max"
                    else:
                        model_display = "qwen-max"
                elif "plus" in model.lower():
                    model_display = "qwen-plus"
                elif "turbo" in model.lower():
                    model_display = "qwen-turbo"
                else:
                    model_display = model
            elif "gemini" in model.lower():
                model_display = "gemini"
            
            return f"{base_name}({model_display})"
        
        return base_name
    
    def _record_usage(
        self,
        provider: str,
        model: str,
        function: Optional[str] = None,  # 功能标识
        usage: Dict[str, int] = None,
        cost: float = 0.0,
        duration_ms: float = 0.0,
    ) -> None:
        """记录使用情况到监控系统"""
        try:
            from server.utils.ai_usage_monitor import record_ai_usage
            
            # 根据功能标识确定功能名称（包含模型信息）
            function_name = self._get_function_display_name(function, provider, model)
            
            if not usage:
                usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            
            record_ai_usage(
                model=model,
                function=function_name,
                input_tokens=usage["prompt_tokens"],
                output_tokens=usage["completion_tokens"],
                total_tokens=usage.get("total_tokens") or (usage["prompt_tokens"] + usage["completion_tokens"]),
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
                "timeout": config.timeout,
                "max_retries": config.max_retries,
                "masked_api_key": (f"{config.api_key[:8]}..." if config.api_key else None),
            }
            for name, config in self.providers.items()
        }
    
    def get_function_config(self, function: str) -> Optional[Dict[str, str]]:
        """获取指定功能的默认配置
        
        Args:
            function: 功能标识（live_analysis/style_profile/script_generation/live_review）
            
        Returns:
            功能配置字典，包含provider和model，如果功能不存在则返回None
        """
        return self.FUNCTION_MODELS.get(function)
    
    def update_function_config(
        self,
        function: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        """更新指定功能的默认配置
        
        Args:
            function: 功能标识
            provider: 新的服务商（为空则不更新）
            model: 新的模型（为空则不更新）
        """
        if function not in self.FUNCTION_MODELS:
            raise ValueError(f"未知的功能标识: {function}")
        
        if provider:
            self.FUNCTION_MODELS[function]["provider"] = provider.lower()
        if model:
            self.FUNCTION_MODELS[function]["model"] = model
        
        logger.info(f"功能 {function} 的配置已更新: provider={provider or '未更改'}, model={model or '未更改'}")
    
    def list_function_configs(self) -> Dict[str, Dict[str, str]]:
        """列出所有功能的默认配置"""
        return self.FUNCTION_MODELS.copy()


# 便捷函数
def get_gateway() -> AIGateway:
    """获取网关实例"""
    return AIGateway.get_instance()
