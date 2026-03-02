"""Agent模块 - Pydantic AI 兼容"""
# 新版 Pydantic AI 风格
from server.agents.base import BaseAgent, AgentResult, LegacyBaseAgent, LegacyAgentResult

# 现有 Agent (向后兼容)
from server.agents.analyzer import AnalyzerAgent
from server.agents.decision import DecisionAgent
from server.agents.reflection import ReflectionAgent
from server.agents.memory import MemoryAgent
from server.agents.workflow_v2 import LiveAnalysisWorkflowV2, WorkflowState

# Voice Agent (新增)
from server.agents.voice import VoiceAgent, VoiceAgentConfig, VoiceAgentResult

__all__ = [
    # 新版基类
    "BaseAgent", "AgentResult",
    # 旧版兼容
    "LegacyBaseAgent", "LegacyAgentResult",
    # 现有 Agents
    "AnalyzerAgent", "DecisionAgent", "ReflectionAgent", "MemoryAgent",
    "LiveAnalysisWorkflowV2", "WorkflowState",
    # Voice Agent
    "VoiceAgent", "VoiceAgentConfig", "VoiceAgentResult",
]
