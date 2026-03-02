"""Agent基础类定义 - Pydantic AI 兼容"""
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from typing import TypeVar, Generic, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class AgentResult(BaseModel):
    """Agent执行结果基类 (Pydantic)

    Attributes:
        success: 执行是否成功
        error: 错误信息，成功时为None
        duration_ms: 执行耗时(毫秒)
    """
    success: bool = True
    error: Optional[str] = None
    duration_ms: float = 0.0

    class Config:
        extra = "allow"


class BaseAgent(ABC, Generic[T]):
    """Agent基类 - 支持异步和Pydantic类型

    Args:
        name: Agent名称，用于日志和标识
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def run(self, input_data: dict) -> T:
        """执行Agent逻辑（子类实现）- 异步版本"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass

    async def __call__(self, input_data: dict) -> T:
        """调用接口 - 自动计时"""
        start_time = time.perf_counter()
        try:
            result = await self.run(input_data)
            duration_ms = (time.perf_counter() - start_time) * 1000

            # 如果结果是AgentResult子类，设置duration
            if isinstance(result, AgentResult):
                result.duration_ms = round(duration_ms, 2)

            return result
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(f"Agent {self.name} exception: {e}")
            raise


# === 向后兼容的旧版 BaseAgent ===

class LegacyAgentResult:
    """旧版AgentResult (dataclass) - 向后兼容"""
    def __init__(
        self,
        success: bool = True,
        data: dict = None,
        error: Optional[str] = None,
        metadata: dict = None
    ):
        self.success = success
        self.data = data or {}
        self.error = error
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }


class LegacyBaseAgent:
    """旧版Agent基类 - 向后兼容 LangGraph 节点"""

    def __init__(
        self,
        name: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        enable_thinking: bool = False,
    ):
        self.name = name
        self.provider = provider
        self.model = model
        self.enable_thinking = enable_thinking

    def run(self, state: dict) -> LegacyAgentResult:
        """执行Agent逻辑（子类实现）"""
        raise NotImplementedError("Subclasses must implement run()")

    def __call__(self, state: dict) -> dict:
        """LangGraph节点调用接口"""
        start_time = time.perf_counter()
        try:
            result = self.run(state)
            duration_ms = (time.perf_counter() - start_time) * 1000
            result.metadata["agent_name"] = self.name
            result.metadata["duration_ms"] = round(duration_ms, 2)

            if not result.success:
                logger.warning(f"Agent {self.name} failed: {result.error}")

            return result.data
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(f"Agent {self.name} exception: {e}")
            return LegacyAgentResult(
                success=False,
                error=str(e),
                metadata={
                    "agent_name": self.name,
                    "duration_ms": round(duration_ms, 2)
                }
            ).data
