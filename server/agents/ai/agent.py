# -*- coding: utf-8 -*-
"""AI Agent - LLM Integration

Wraps AIGateway with Agent pattern for unified LLM access.
"""
from pydantic import BaseModel
from typing import Optional, Literal, List, Dict, Any

from server.agents.base import BaseAgent, AgentResult


class AIAgentConfig(BaseModel):
    """AI Agent 配置"""
    service: Literal["qwen", "openai", "deepseek", "doubao", "chatglm", "xunfei", "gemini"] = "qwen"
    model: str = "qwen-plus"
    temperature: float = 0.7
    max_tokens: int = 2000
    function: Optional[str] = None  # live_analysis, style_profile, script_generation, live_review, etc.


class AIAgentResult(AgentResult):
    """AI Agent 结果"""
    content: str = ""
    model: str = ""
    provider: str = ""
    usage: Dict[str, int] = {}
    cost: float = 0.0


class AIAgent(BaseAgent[AIAgentResult]):
    """AI Agent

    Wraps AIGateway for LLM completions with unified interface.

    Example:
        # Simple usage
        agent = AIAgent()
        result = await agent.chat([
            {"role": "user", "content": "Hello"}
        ])

        # With specific function
        agent = AIAgent(AIAgentConfig(function="live_analysis"))
        result = await agent.chat(messages)

        # With custom model
        agent = AIAgent(AIAgentConfig(service="openai", model="gpt-4"))
        result = await agent.chat(messages)
    """

    def __init__(self, config: Optional[AIAgentConfig] = None):
        super().__init__(name="ai")
        self.config = config or AIAgentConfig()
        self._gateway = None

    def _get_gateway(self):
        """Lazy load the gateway to avoid import issues"""
        if self._gateway is None:
            from server.ai.ai_gateway import get_gateway
            self._gateway = get_gateway()
        return self._gateway

    async def run(self, input_data: dict) -> AIAgentResult:
        """执行 AI 对话

        Args:
            input_data: {
                "messages": [{"role": "user", "content": "..."}],
                "function": "live_analysis"  # optional
            }

        Returns:
            AIAgentResult
        """
        messages = input_data.get("messages", [])
        function = input_data.get("function") or self.config.function

        return await self.chat(messages, function=function)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        function: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AIAgentResult:
        """执行对话补全

        Args:
            messages: 消息列表
            function: 功能标识 (用于选择专用模型)
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            AIAgentResult
        """
        try:
            gateway = self._get_gateway()

            # Build kwargs for gateway
            kwargs: Dict[str, Any] = {
                "messages": messages,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
            }

            # Add provider/model if specified in config
            if self.config.service:
                kwargs["provider"] = self.config.service
            if self.config.model:
                kwargs["model"] = self.config.model

            # Add function for model selection
            if function or self.config.function:
                kwargs["function"] = function or self.config.function

            response = gateway.chat_completion(**kwargs)

            return AIAgentResult(
                success=response.success,
                error=response.error,
                content=response.content,
                model=response.model,
                provider=response.provider,
                usage=response.usage,
                cost=response.cost,
                duration_ms=response.duration_ms
            )
        except Exception as e:
            return AIAgentResult(
                success=False,
                error=str(e)
            )

    async def health_check(self) -> bool:
        """健康检查

        Returns:
            True if gateway is available
        """
        try:
            gateway = self._get_gateway()
            return gateway is not None
        except Exception:
            return False

    def switch_provider(self, service: str, model: Optional[str] = None) -> None:
        """切换服务商

        Args:
            service: 服务商名称
            model: 模型名称 (可选)
        """
        gateway = self._get_gateway()
        gateway.switch_provider(service, model)
        self.config.service = service  # type: ignore
        if model:
            self.config.model = model

    def list_functions(self) -> Dict[str, Dict[str, str]]:
        """列出所有功能及其默认模型配置

        Returns:
            功能配置字典
        """
        gateway = self._get_gateway()
        return gateway.list_function_models()
