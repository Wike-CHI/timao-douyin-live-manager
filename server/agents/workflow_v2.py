"""Agent工作流V2

集成AI Gateway V2，使用GLM-5和MiniMax实现多Agent协作
"""
from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from server.agents.analyzer import AnalyzerAgent
from server.agents.decision import DecisionAgent
from server.agents.reflection import ReflectionAgent
from server.agents.memory import MemoryAgent


class WorkflowState(TypedDict, total=False):
    """工作流状态"""
    anchor_id: Optional[str]
    transcript_snippet: str
    chat_signals: list
    vibe: dict
    persona: dict

    # Agent输出
    memory_result: dict
    analysis_result: dict
    decision_result: dict
    reflection_result: dict

    # 控制
    retry_count: int
    max_retries: int


class LiveAnalysisWorkflowV2:
    """直播分析工作流V2"""

    MAX_RETRIES = 2

    def __init__(self):
        """初始化工作流"""
        # 初始化Agents
        self.memory_agent = MemoryAgent()
        self.analyzer_agent = AnalyzerAgent()
        self.decision_agent = DecisionAgent()
        self.reflection_agent = ReflectionAgent()

        # 构建图
        self.graph = self._build_graph()
        self.workflow = self.graph.compile(checkpointer=MemorySaver())

    def _build_graph(self) -> StateGraph:
        """构建Agent协作图"""
        graph = StateGraph(WorkflowState)

        # 添加节点
        graph.add_node("memory_loader", self._memory_loader_node)
        graph.add_node("analyzer", self._analyzer_node)
        graph.add_node("decision_maker", self._decision_node)
        graph.add_node("reflection", self._reflection_node)
        graph.add_node("memory_updater", self._memory_updater_node)

        # 定义流程
        graph.set_entry_point("memory_loader")
        graph.add_edge("memory_loader", "analyzer")
        graph.add_edge("analyzer", "decision_maker")

        # 反思循环
        graph.add_conditional_edges(
            "decision_maker",
            self._should_reflect,
            {
                True: "reflection",
                False: "memory_updater"
            }
        )

        graph.add_conditional_edges(
            "reflection",
            self._should_retry,
            {
                True: "analyzer",
                False: "memory_updater"
            }
        )

        graph.add_edge("memory_updater", END)

        return graph

    def invoke(self, state: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行工作流

        Args:
            state: 工作流状态
            config: LangGraph配置，可包含thread_id等
        """
        state.setdefault("retry_count", 0)
        state.setdefault("max_retries", self.MAX_RETRIES)

        # 提供默认的thread_id配置
        if config is None:
            config = {"configurable": {"thread_id": "default"}}

        return self.workflow.invoke(state, config)

    # 节点实现
    def _memory_loader_node(self, state: WorkflowState) -> dict:
        """加载记忆节点"""
        load_state = dict(state)
        load_state["memory_action"] = "load"
        result = self.memory_agent.run(load_state)
        memories = result.data.get("memories", [])
        persona = memories[0] if memories else {}
        return {"memory_result": result.data, "persona": persona}

    def _analyzer_node(self, state: WorkflowState) -> dict:
        """分析节点"""
        result = self.analyzer_agent.run(state)
        return {"analysis_result": result.data}

    def _decision_node(self, state: WorkflowState) -> dict:
        """决策节点"""
        result = self.decision_agent.run(state)
        return {"decision_result": result.data}

    def _reflection_node(self, state: WorkflowState) -> dict:
        """反思节点"""
        result = self.reflection_agent.run(state)
        return {
            "reflection_result": result.data,
            "retry_count": state.get("retry_count", 0) + 1,
        }

    def _memory_updater_node(self, state: WorkflowState) -> dict:
        """更新记忆节点"""
        save_state = dict(state)
        save_state["memory_action"] = "save"
        save_state["memory_content"] = state.get("decision_result", {}).get("decision", "")
        save_state["memory_type"] = "feedback"

        result = self.memory_agent.run(save_state)
        return {"memory_result": result.data}

    # 条件判断
    def _should_reflect(self, state: WorkflowState) -> bool:
        """是否需要反思"""
        # 每次都进行反思评估
        return True

    def _should_retry(self, state: WorkflowState) -> bool:
        """是否需要重试"""
        reflection = state.get("reflection_result", {})
        needs_retry = reflection.get("needs_retry", False)
        retry_count = state.get("retry_count", 0)
        max_retries = state.get("max_retries", self.MAX_RETRIES)

        return needs_retry and retry_count < max_retries
