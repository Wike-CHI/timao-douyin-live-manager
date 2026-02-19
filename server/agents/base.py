"""Agent基础类定义"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Agent执行结果"""
    success: bool = True
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }


class BaseAgent:
    """Agent基类"""

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

    def run(self, state: Dict[str, Any]) -> AgentResult:
        """执行Agent逻辑（子类实现）"""
        raise NotImplementedError("Subclasses must implement run()")

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
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
            logger.error(f"Agent {self.name} exception: {e}")
            return AgentResult(
                success=False,
                error=str(e),
                metadata={"agent_name": self.name}
            ).data
