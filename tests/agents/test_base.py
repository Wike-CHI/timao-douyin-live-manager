"""测试Agent基础类"""
import pytest
from server.agents.base import BaseAgent, AgentResult


class TestAgent(BaseAgent):
    """测试用Agent"""

    def run(self, state: dict) -> AgentResult:
        return AgentResult(
            success=True,
            data={"test": "result"},
            metadata={"duration_ms": 100}
        )


class TestBaseAgent:
    """BaseAgent测试"""

    def test_agent_initialization(self):
        """测试Agent初始化"""
        agent = TestAgent(
            name="test_agent",
            provider="glm",
            model="glm-5"
        )
        assert agent.name == "test_agent"
        assert agent.provider == "glm"
        assert agent.model == "glm-5"

    def test_agent_run(self):
        """测试Agent执行"""
        agent = TestAgent(name="test")
        result = agent.run({})

        assert result.success is True
        assert result.data == {"test": "result"}
        assert result.metadata["duration_ms"] == 100

    def test_agent_result_to_dict(self):
        """测试结果转换为字典"""
        result = AgentResult(
            success=True,
            data={"key": "value"},
            metadata={"time": 50}
        )

        d = result.to_dict()
        assert d["success"] is True
        assert d["data"]["key"] == "value"
