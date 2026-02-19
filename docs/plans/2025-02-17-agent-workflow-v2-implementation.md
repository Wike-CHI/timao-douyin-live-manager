# Agent工作流重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 升级LangGraph工作流，集成AI Gateway V2，实现多Agent协作

**Architecture:** 使用GLM-5进行深度分析和决策，MiniMax进行实时分析，添加反思机制和工具调用

**Tech Stack:** Python, LangGraph, AI Gateway V2, GLM-5, MiniMax

---

## 现有实现分析

当前 `langgraph_live_workflow.py` 已有以下节点:
- memory_loader - 加载记忆
- signal_collector - 收集信号
- topic_detector - 话题检测
- mood_estimator - 情绪估计
- planner - 规划器
- knowledge_loader - 知识库加载
- style_profile_builder - 风格画像
- analysis_generator - 分析生成
- question_responder - 问题响应
- summary - 总结

## 需要改进的点

1. **集成AI Gateway V2** - 替换旧的AI Gateway调用
2. **添加反思机制** - 使用GLM-5进行质量评估
3. **添加记忆更新器** - 将分析结果写入SQLite
4. **优化并行分析** - 使用MiniMax高速模型
5. **添加工具调用** - 支持Function Calling

---

## Task 1: 创建Agent基础类

**Files:**
- Create: `server/agents/__init__.py`
- Create: `server/agents/base.py`
- Create: `tests/agents/test_base.py`

**Step 1: 编写测试**

创建 `tests/agents/test_base.py`:

```python
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
```

**Step 2: 实现BaseAgent**

创建 `server/agents/__init__.py`:
```python
"""Agent模块"""
from server.agents.base import BaseAgent, AgentResult

__all__ = ["BaseAgent", "AgentResult"]
```

创建 `server/agents/base.py`:
```python
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
```

**Step 3: 运行测试**

```bash
pytest tests/agents/test_base.py -v
```

**Step 4: 提交**

```bash
git add server/agents/ tests/agents/
git commit -m "feat: add Agent base class"
```

---

## Task 2: 创建Analyzer Agent (MiniMax)

**Files:**
- Create: `server/agents/analyzer.py`
- Create: `tests/agents/test_analyzer.py`

**Step 1: 编写测试**

```python
"""测试Analyzer Agent"""
import pytest
from unittest.mock import MagicMock, patch
from server.agents.analyzer import AnalyzerAgent


class TestAnalyzerAgent:
    """AnalyzerAgent测试"""

    def test_analyzer_initialization(self):
        """测试分析器初始化"""
        agent = AnalyzerAgent()
        assert agent.name == "analyzer"
        assert agent.provider == "minimax"
        assert agent.model == "MiniMax-M2.5-highspeed"

    def test_analyzer_run_with_signals(self):
        """测试分析器处理信号"""
        agent = AnalyzerAgent()

        state = {
            "transcript_snippet": "大家好",
            "chat_signals": [
                {"text": "主播好", "weight": 0.5, "category": "support"}
            ],
            "vibe": {"level": "neutral", "score": 50},
        }

        with patch.object(agent, '_call_ai') as mock_call:
            mock_call.return_value = {
                "analysis": "主播正在与观众互动",
                "suggestions": ["继续互动"]
            }

            result = agent.run(state)
            assert result.success is True
            assert "analysis" in result.data
```

**Step 2: 实现AnalyzerAgent**

```python
"""实时分析Agent

使用MiniMax-M2.5-highspeed进行高速实时分析
"""
from typing import Any, Dict
from server.agents.base import BaseAgent, AgentResult
from server.ai.ai_gateway_v2 import get_gateway


class AnalyzerAgent(BaseAgent):
    """实时分析Agent (MiniMax高速模型)"""

    def __init__(self):
        super().__init__(
            name="analyzer",
            provider="minimax",
            model="MiniMax-M2.5-highspeed",
            enable_thinking=False,  # 实时分析不需要思考过程
        )
        self.gateway = get_gateway()

    def run(self, state: Dict[str, Any]) -> AgentResult:
        """执行实时分析"""
        transcript = state.get("transcript_snippet", "")
        chat_signals = state.get("chat_signals", [])
        vibe = state.get("vibe", {})

        # 构建分析提示
        prompt = self._build_prompt(transcript, chat_signals, vibe)

        try:
            # 切换到MiniMax高速模型
            self.gateway.switch_provider("minimax", "MiniMax-M2.5-highspeed")

            result = self.gateway.chat_completion(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                enable_thinking=False,
                temperature=0.7,
                max_tokens=1024,
            )

            return AgentResult(
                success=True,
                data={
                    "analysis": result.get("content", ""),
                    "reasoning": result.get("reasoning", ""),
                }
            )
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                data={"analysis": f"分析失败: {e}"}
            )

    def _get_system_prompt(self) -> str:
        return """你是直播间实时分析助手。
分析主播的口播内容和观众弹幕，提供简洁的实时分析。
输出格式：
1. 当前状态（一句话）
2. 主要关注点
3. 建议行动"""

    def _build_prompt(
        self,
        transcript: str,
        chat_signals: list,
        vibe: dict
    ) -> str:
        chat_summary = "\n".join([
            f"- {sig.get('text', '')} (权重:{sig.get('weight', 0):.1f})"
            for sig in chat_signals[-10:]
        ])

        return f"""请分析当前直播状态：

主播口播：
{transcript or "（暂无）"}

最近弹幕：
{chat_summary or "（暂无）"}

氛围状态：{vibe.get('level', 'neutral')} ({vibe.get('score', 0)}分)

请提供分析。"""
```

---

## Task 3: 创建Decision Agent (GLM-5)

**Files:**
- Create: `server/agents/decision.py`
- Create: `tests/agents/test_decision.py`

**Step 4: 实现DecisionAgent**

```python
"""决策Agent

使用GLM-5进行深度决策分析，支持思考模式
"""
from typing import Any, Dict
from server.agents.base import BaseAgent, AgentResult
from server.ai.ai_gateway_v2 import get_gateway


class DecisionAgent(BaseAgent):
    """决策Agent (GLM-5深度思考)"""

    def __init__(self):
        super().__init__(
            name="decision_maker",
            provider="glm",
            model="glm-5",
            enable_thinking=True,  # 启用深度思考
        )
        self.gateway = get_gateway()

    def run(self, state: Dict[str, Any]) -> AgentResult:
        """执行决策分析"""
        analysis = state.get("analysis_result", {})
        style_profile = state.get("style_profile", {})
        planner_notes = state.get("planner_notes", {})

        prompt = self._build_prompt(analysis, style_profile, planner_notes)

        try:
            # 切换到GLM-5
            self.gateway.switch_provider("glm", "glm-5")

            result = self.gateway.chat_completion(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                enable_thinking=True,  # 启用思考模式
                temperature=0.7,
                max_tokens=2048,
            )

            return AgentResult(
                success=True,
                data={
                    "decision": result.get("content", ""),
                    "reasoning": result.get("reasoning", ""),
                }
            )
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                data={"decision": f"决策失败: {e}"}
            )

    def _get_system_prompt(self) -> str:
        return """你是直播间决策助手，帮助主播做出最佳决策。

你需要：
1. 综合分析结果和风格画像
2. 考虑当前直播氛围
3. 给出具体可执行的建议

请先思考（在reasoning中），然后给出决策建议。"""

    def _build_prompt(
        self,
        analysis: dict,
        style_profile: dict,
        planner_notes: dict
    ) -> str:
        return f"""基于以下信息做出决策：

分析结果：
{analysis.get('analysis', '无')}

风格画像：
{style_profile.get('tone', '专业陪伴')}

规划笔记：
{planner_notes.get('selected_topic', {}).get('topic', '互动')}

请给出决策建议。"""
```

---

## Task 4: 创建Reflection Agent (GLM-5)

**Files:**
- Create: `server/agents/reflection.py`
- Create: `tests/agents/test_reflection.py`

**实现ReflectionAgent**

```python
"""反思Agent

使用GLM-5评估分析质量，触发重新分析
"""
from typing import Any, Dict
from server.agents.base import BaseAgent, AgentResult
from server.ai.ai_gateway_v2 import get_gateway


class ReflectionAgent(BaseAgent):
    """反思Agent (GLM-5评估质量)"""

    QUALITY_THRESHOLD = 0.7  # 质量阈值

    def __init__(self):
        super().__init__(
            name="reflection",
            provider="glm",
            model="glm-5",
            enable_thinking=True,
        )
        self.gateway = get_gateway()

    def run(self, state: Dict[str, Any]) -> AgentResult:
        """评估分析质量"""
        analysis = state.get("analysis_result", {})
        decision = state.get("decision_result", {})

        try:
            self.gateway.switch_provider("glm", "glm-5")

            result = self.gateway.chat_completion(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": self._build_prompt(analysis, decision)},
                ],
                enable_thinking=True,
                temperature=0.3,
                max_tokens=512,
            )

            content = result.get("content", "")
            quality_score = self._extract_score(content)
            needs_retry = quality_score < self.QUALITY_THRESHOLD

            return AgentResult(
                success=True,
                data={
                    "quality_score": quality_score,
                    "needs_retry": needs_retry,
                    "reflection": content,
                    "reasoning": result.get("reasoning", ""),
                }
            )
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                data={"quality_score": 0.5, "needs_retry": False}
            )

    def _get_system_prompt(self) -> str:
        return """你是分析质量评估专家。

评估分析结果的：
1. 相关性 - 是否与直播内容相关
2. 完整性 - 是否覆盖关键点
3. 可操作性 - 建议是否具体可行

输出格式：
质量评分: [0.0-1.0]
需要重试: [是/否]
问题说明: [如有]"""

    def _build_prompt(self, analysis: dict, decision: dict) -> str:
        return f"""请评估以下分析质量：

分析内容：
{analysis.get('analysis', '无')[:500]}

决策建议：
{decision.get('decision', '无')[:500]}

请给出质量评分。"""

    def _extract_score(self, content: str) -> float:
        """从内容中提取评分"""
        import re
        match = re.search(r"质量评分[：:]\s*([\d.]+)", content)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return 0.7  # 默认评分
```

---

## Task 5: 创建Memory Agent (GLM-5)

**Files:**
- Create: `server/agents/memory.py`
- Create: `tests/agents/test_memory.py`

**实现MemoryAgent**

```python
"""记忆管理Agent

使用GLM-5管理记忆存储和检索，与SQLite数据库交互
"""
from typing import Any, Dict, List, Optional
from server.agents.base import BaseAgent, AgentResult
from server.ai.ai_gateway_v2 import get_gateway
from server.database import get_sqlite_manager


class MemoryAgent(BaseAgent):
    """记忆管理Agent (GLM-5)"""

    def __init__(self):
        super().__init__(
            name="memory",
            provider="glm",
            model="glm-5",
            enable_thinking=True,
        )
        self.gateway = get_gateway()
        self.db_manager = None

    def _get_db(self):
        if self.db_manager is None:
            self.db_manager = get_sqlite_manager()
        return self.db_manager

    def run(self, state: Dict[str, Any]) -> AgentResult:
        """执行记忆操作"""
        action = state.get("memory_action", "load")
        anchor_id = state.get("anchor_id", "default")

        if action == "load":
            return self._load_memory(anchor_id)
        elif action == "save":
            return self._save_memory(anchor_id, state)
        else:
            return AgentResult(
                success=False,
                error=f"未知记忆操作: {action}"
            )

    def _load_memory(self, anchor_id: str) -> AgentResult:
        """加载记忆"""
        try:
            db = self._get_db()
            engine = db.get_ai_database("memory_vectors")

            with engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("""
                    SELECT content, metadata, importance_score
                    FROM memory_vectors
                    WHERE anchor_id = :anchor_id
                    ORDER BY importance_score DESC
                    LIMIT 10
                """), {"anchor_id": anchor_id})

                memories = [
                    {
                        "content": row[0],
                        "metadata": row[1],
                        "importance": row[2],
                    }
                    for row in result.fetchall()
                ]

            return AgentResult(
                success=True,
                data={"memories": memories}
            )
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                data={"memories": []}
            )

    def _save_memory(self, anchor_id: str, state: Dict[str, Any]) -> AgentResult:
        """保存记忆"""
        content = state.get("memory_content", "")
        memory_type = state.get("memory_type", "context")

        if not content:
            return AgentResult(
                success=True,
                data={"saved": False, "reason": "无内容"}
            )

        try:
            db = self._get_db()
            engine = db.get_ai_database("memory_vectors")

            with engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("""
                    INSERT INTO memory_vectors
                    (anchor_id, memory_type, content, importance_score)
                    VALUES (:anchor_id, :memory_type, :content, 0.5)
                """), {
                    "anchor_id": anchor_id,
                    "memory_type": memory_type,
                    "content": content,
                })
                conn.commit()

            return AgentResult(
                success=True,
                data={"saved": True}
            )
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                data={"saved": False}
            )
```

---

## Task 6: 创建工作流V2

**Files:**
- Create: `server/agents/workflow_v2.py`
- Create: `tests/agents/test_workflow_v2.py`

**实现新版工作流**

```python
"""Agent工作流V2

集成AI Gateway V2，使用GLM-5和MiniMax实现多Agent协作
"""
from typing import Any, Dict, Optional
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
        # 初始化Agents
        self.memory_agent = MemoryAgent()
        self.analyzer_agent = AnalyzerAgent()
        self.decision_agent = DecisionAgent()
        self.reflection_agent = ReflectionAgent()

        # 构建图
        self.graph = self._build_graph()
        self.workflow = self.graph.compile(checkpointer=MemorySaver())

    def _build_graph(self) -> StateGraph:
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

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流"""
        state.setdefault("retry_count", 0)
        state.setdefault("max_retries", self.MAX_RETRIES)
        return self.workflow.invoke(state)

    # 节点实现
    def _memory_loader_node(self, state: WorkflowState) -> dict:
        state["memory_action"] = "load"
        result = self.memory_agent.run(state)
        return {"memory_result": result.data, "persona": result.data.get("memories", [{}])[0] if result.data.get("memories") else {}}

    def _analyzer_node(self, state: WorkflowState) -> dict:
        result = self.analyzer_agent.run(state)
        return {"analysis_result": result.data}

    def _decision_node(self, state: WorkflowState) -> dict:
        result = self.decision_agent.run(state)
        return {"decision_result": result.data}

    def _reflection_node(self, state: WorkflowState) -> dict:
        result = self.reflection_agent.run(state)
        return {
            "reflection_result": result.data,
            "retry_count": state.get("retry_count", 0) + 1,
        }

    def _memory_updater_node(self, state: WorkflowState) -> dict:
        state["memory_action"] = "save"
        state["memory_content"] = state.get("decision_result", {}).get("decision", "")
        state["memory_type"] = "feedback"

        result = self.memory_agent.run(state)
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
```

---

## Task 7: 集成测试

**Files:**
- Create: `tests/agents/test_workflow_integration.py`

**Step 1: 创建集成测试**

```python
"""工作流集成测试"""
import pytest
from unittest.mock import patch, MagicMock
from server.agents.workflow_v2 import LiveAnalysisWorkflowV2


class TestWorkflowIntegration:
    """工作流集成测试"""

    def test_workflow_initialization(self):
        """测试工作流初始化"""
        workflow = LiveAnalysisWorkflowV2()
        assert workflow.graph is not None
        assert workflow.workflow is not None

    def test_workflow_invoke_basic(self):
        """测试基本工作流执行"""
        workflow = LiveAnalysisWorkflowV2()

        state = {
            "anchor_id": "test_anchor",
            "transcript_snippet": "大家好，欢迎来到直播间",
            "chat_signals": [
                {"text": "主播好", "weight": 0.5, "category": "support"}
            ],
            "vibe": {"level": "neutral", "score": 50},
        }

        with patch.object(workflow.analyzer_agent, 'run') as mock_analyzer:
            mock_analyzer.return_value = MagicMock(
                success=True,
                data={"analysis": "测试分析"}
            )

            with patch.object(workflow.decision_agent, 'run') as mock_decision:
                mock_decision.return_value = MagicMock(
                    success=True,
                    data={"decision": "测试决策"}
                )

                with patch.object(workflow.reflection_agent, 'run') as mock_reflect:
                    mock_reflect.return_value = MagicMock(
                        success=True,
                        data={"quality_score": 0.8, "needs_retry": False}
                    )

                    result = workflow.invoke(state)
                    assert "decision_result" in result
```

---

## Task 8: 更新文档

**Files:**
- Create: `docs/agents/Agent-Workflow-V2-Guide.md`

---

## 执行说明

1. **严格TDD流程**: 每个任务遵循"写测试→失败→写代码→通过→提交"
2. **使用AI Gateway V2**: 所有Agent通过V2调用GLM-5或MiniMax
3. **保持向后兼容**: 旧工作流继续可用
4. **增量迁移**: 先完成新工作流，再逐步替换

**下一步：**

选择执行方式后，将逐步执行每个Task。
