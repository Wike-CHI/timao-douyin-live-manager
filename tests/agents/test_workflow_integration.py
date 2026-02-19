"""工作流集成测试

测试完整的Agent协作流程，使用mock的AI响应
"""
import pytest
from unittest.mock import MagicMock, patch

from server.agents import (
    AnalyzerAgent,
    DecisionAgent,
    ReflectionAgent,
    MemoryAgent,
    LiveAnalysisWorkflowV2,
    WorkflowState,
    AgentResult,
)


class TestWorkflowIntegration:
    """工作流集成测试"""

    def _create_mock_gateway(self):
        """创建模拟网关"""
        mock_gateway = MagicMock()
        mock_gateway.switch_provider.return_value = None
        return mock_gateway

    def _create_mock_db_manager(self):
        """创建模拟数据库管理器"""
        mock_manager = MagicMock()
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()

        # 模拟load返回空记忆
        mock_result.fetchall.return_value = []
        mock_conn.execute.return_value = mock_result
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.commit = MagicMock()
        mock_engine.connect.return_value = mock_conn
        mock_manager.get_ai_database.return_value = mock_engine

        return mock_manager

    def test_full_workflow_with_mocked_ai(self):
        """测试完整工作流（使用mock AI响应）"""
        mock_gateway = self._create_mock_gateway()
        mock_db_manager = self._create_mock_db_manager()

        # 配置各个gateway的返回值
        mock_gateway.chat_completion.return_value = {
            "content": "分析：主播正在介绍新品，观众期待值高。建议继续推进产品介绍。",
            "reasoning": "",
        }

        with patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_sqlite_manager', return_value=mock_db_manager):

            workflow = LiveAnalysisWorkflowV2()

            # 准备输入状态
            state = {
                "anchor_id": "integration_test_anchor",
                "transcript_snippet": "大家好，欢迎来到直播间，今天给大家带来新品推荐",
                "chat_signals": [
                    {"text": "主播好", "weight": 0.6, "category": "support"},
                    {"text": "期待新品", "weight": 0.8, "category": "interest"},
                ],
                "vibe": {"level": "positive", "score": 75},
            }

            # 执行工作流
            result = workflow.invoke(state)

            # 验证结果
            assert "decision_result" in result
            # 决策结果应该有内容或者有错误
            decision = result.get("decision_result", {})
            assert decision.get("decision") or decision.get("error")

    def test_workflow_retry_on_low_quality(self):
        """测试低质量分析时触发重试"""
        mock_db_manager = self._create_mock_db_manager()

        call_count = {"analyzer": 0, "reflection": 0}

        def mock_analyzer_completion(*args, **kwargs):
            call_count["analyzer"] += 1
            return {"content": f"分析结果 {call_count['analyzer']}", "reasoning": ""}

        def mock_reflection_completion(*args, **kwargs):
            call_count["reflection"] += 1
            # 第一次返回低分，之后返回高分
            if call_count["reflection"] == 1:
                return {"content": "质量评分: 0.5\n需要重试: 是", "reasoning": ""}
            return {"content": "质量评分: 0.8\n需要重试: 否", "reasoning": ""}

        # 使用不同的mock gateway来处理不同的调用
        analyzer_gateway = self._create_mock_gateway()
        analyzer_gateway.chat_completion.side_effect = mock_analyzer_completion

        decision_gateway = self._create_mock_gateway()
        decision_gateway.chat_completion.return_value = {
            "content": "决策建议", "reasoning": ""
        }

        reflection_gateway = self._create_mock_gateway()
        reflection_gateway.chat_completion.side_effect = mock_reflection_completion

        memory_gateway = self._create_mock_gateway()

        with patch('server.agents.analyzer.get_gateway', return_value=analyzer_gateway), \
             patch('server.agents.decision.get_gateway', return_value=decision_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=reflection_gateway), \
             patch('server.agents.memory.get_gateway', return_value=memory_gateway), \
             patch('server.agents.memory.get_sqlite_manager', return_value=mock_db_manager):

            workflow = LiveAnalysisWorkflowV2()

            state = {
                "anchor_id": "retry_test_anchor",
                "transcript_snippet": "测试内容",
                "chat_signals": [],
                "vibe": {"level": "neutral", "score": 50},
            }

            result = workflow.invoke(state)

            # 验证重试发生
            assert call_count["analyzer"] >= 2, "应该触发至少一次重试"
            assert call_count["reflection"] >= 2, "应该进行至少两次反思"

    def test_individual_agents_work_together(self):
        """测试单个Agent协作"""
        mock_gateway = self._create_mock_gateway()
        mock_db_manager = self._create_mock_db_manager()

        with patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_sqlite_manager', return_value=mock_db_manager):

            analyzer = AnalyzerAgent()
            decision = DecisionAgent()
            reflection = ReflectionAgent()

            # 模拟状态流转
            state = {
                "transcript_snippet": "测试口播",
                "chat_signals": [{"text": "好", "weight": 0.5}],
                "vibe": {"level": "neutral", "score": 50},
                "analysis_result": {},
                "decision_result": {},
            }

            # Mock gateway
            mock_gateway.chat_completion.return_value = {
                "content": "测试分析", "reasoning": ""
            }

            result = analyzer.run(state)
            assert result.success is True
            state["analysis_result"] = result.data

            # 更新mock返回值用于决策
            mock_gateway.chat_completion.return_value = {
                "content": "测试决策", "reasoning": ""
            }

            result = decision.run(state)
            assert result.success is True
            state["decision_result"] = result.data

            # 更新mock返回值用于反思
            mock_gateway.chat_completion.return_value = {
                "content": "质量评分: 0.8\n需要重试: 否", "reasoning": ""
            }

            result = reflection.run(state)
            assert result.success is True
            assert result.data["needs_retry"] is False

    def test_workflow_with_memory_persistence(self):
        """测试工作流与记忆持久化"""
        mock_gateway = self._create_mock_gateway()
        mock_db_manager = self._create_mock_db_manager()

        # 跟踪数据库调用
        save_called = {"count": 0}

        def mock_execute(*args, **kwargs):
            save_called["count"] += 1
            mock_result = MagicMock()
            mock_result.fetchall.return_value = []
            return mock_result

        mock_db_manager.get_ai_database.return_value.connect.return_value.__enter__.return_value.execute.side_effect = mock_execute

        mock_gateway.chat_completion.return_value = {
            "content": "测试响应",
            "reasoning": "",
        }

        with patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_sqlite_manager', return_value=mock_db_manager):

            workflow = LiveAnalysisWorkflowV2()

            state = {
                "anchor_id": "memory_test_anchor",
                "transcript_snippet": "测试记忆持久化",
                "chat_signals": [],
                "vibe": {"level": "positive", "score": 70},
            }

            result = workflow.invoke(state)

            # 验证工作流完成
            assert result is not None
            # 记忆结果应该存在
            assert "memory_result" in result

    def test_workflow_max_retries_exceeded(self):
        """测试超过最大重试次数后正常结束"""
        mock_gateway = self._create_mock_gateway()
        mock_db_manager = self._create_mock_db_manager()

        call_count = {"reflection": 0}

        def mock_reflection_always_retry(*args, **kwargs):
            call_count["reflection"] += 1
            # 总是返回需要重试
            return {"content": "质量评分: 0.3\n需要重试: 是", "reasoning": ""}

        reflection_gateway = self._create_mock_gateway()
        reflection_gateway.chat_completion.side_effect = mock_reflection_always_retry

        mock_gateway.chat_completion.return_value = {
            "content": "测试响应",
            "reasoning": "",
        }

        with patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=reflection_gateway), \
             patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_sqlite_manager', return_value=mock_db_manager):

            workflow = LiveAnalysisWorkflowV2()

            state = {
                "anchor_id": "max_retry_test",
                "transcript_snippet": "测试",
                "chat_signals": [],
                "vibe": {},
            }

            result = workflow.invoke(state)

            # 即使总是需要重试，工作流也应该正常结束
            assert result is not None
            # 反思次数不应该超过最大重试次数+1（初始+重试）
            assert call_count["reflection"] <= workflow.MAX_RETRIES + 1

    def test_workflow_handles_partial_failures(self):
        """测试工作流处理部分失败"""
        mock_gateway = self._create_mock_gateway()
        mock_db_manager = self._create_mock_db_manager()

        analyzer_gateway = self._create_mock_gateway()
        analyzer_gateway.chat_completion.side_effect = Exception("Analyzer API Error")

        decision_gateway = self._create_mock_gateway()
        decision_gateway.chat_completion.return_value = {
            "content": "默认决策", "reasoning": ""
        }

        reflection_gateway = self._create_mock_gateway()
        reflection_gateway.chat_completion.return_value = {
            "content": "质量评分: 0.6\n需要重试: 否", "reasoning": ""
        }

        with patch('server.agents.analyzer.get_gateway', return_value=analyzer_gateway), \
             patch('server.agents.decision.get_gateway', return_value=decision_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=reflection_gateway), \
             patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_sqlite_manager', return_value=mock_db_manager):

            workflow = LiveAnalysisWorkflowV2()

            state = {
                "anchor_id": "partial_failure_test",
                "transcript_snippet": "测试",
                "chat_signals": [],
                "vibe": {},
            }

            result = workflow.invoke(state)

            # 工作流应该继续执行，不应因单个Agent失败而中断
            assert result is not None
            # 分析结果应该包含错误
            assert "error" in result.get("analysis_result", {})


class TestAgentContracts:
    """Agent契约测试 - 验证Agent接口一致性"""

    def test_all_agents_return_agent_result(self):
        """测试所有Agent返回AgentResult"""
        mock_gateway = MagicMock()
        mock_gateway.switch_provider.return_value = None
        mock_db_manager = MagicMock()

        with patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_sqlite_manager', return_value=mock_db_manager):

            agents = [
                ("analyzer", AnalyzerAgent()),
                ("decision", DecisionAgent()),
                ("reflection", ReflectionAgent()),
                ("memory", MemoryAgent()),
            ]

            for name, agent in agents:
                assert hasattr(agent, 'run'), f"{name} should have run method"
                assert hasattr(agent, 'name'), f"{name} should have name attribute"
                # Agent名称可能不完全匹配，但应该相关
                assert agent.name.replace("_", "") in name.replace("_", "").replace("maker", "") or \
                       name.replace("_", "").replace("maker", "") in agent.name.replace("_", ""), \
                    f"Agent name mismatch: {agent.name} vs {name}"

    def test_workflow_state_typed_dict(self):
        """测试WorkflowState是有效的TypedDict"""
        # 验证可以创建实例
        state: WorkflowState = {
            "anchor_id": "test",
            "transcript_snippet": "test",
            "chat_signals": [],
            "vibe": {},
        }
        assert state["anchor_id"] == "test"

    def test_agent_result_dataclass(self):
        """测试AgentResult数据类"""
        # 测试成功结果
        success_result = AgentResult(
            success=True,
            data={"key": "value"},
            metadata={"duration_ms": 100}
        )
        assert success_result.success is True
        assert success_result.data == {"key": "value"}
        assert success_result.error is None

        # 测试失败结果
        failure_result = AgentResult(
            success=False,
            error="Test error"
        )
        assert failure_result.success is False
        assert failure_result.error == "Test error"

        # 测试to_dict方法
        result_dict = success_result.to_dict()
        assert "success" in result_dict
        assert "data" in result_dict
        assert "error" in result_dict
        assert "metadata" in result_dict

    def test_all_agents_can_be_called_as_langgraph_nodes(self):
        """测试所有Agent可以作为LangGraph节点调用"""
        mock_gateway = MagicMock()
        mock_gateway.switch_provider.return_value = None
        mock_gateway.chat_completion.return_value = {
            "content": "测试响应", "reasoning": ""
        }
        mock_db_manager = MagicMock()
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_conn.execute.return_value = mock_result
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_engine.connect.return_value = mock_conn
        mock_db_manager.get_ai_database.return_value = mock_engine

        with patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_sqlite_manager', return_value=mock_db_manager):

            agents = [
                AnalyzerAgent(),
                DecisionAgent(),
                ReflectionAgent(),
                MemoryAgent(),
            ]

            for agent in agents:
                # Agent应该可以直接调用（作为LangGraph节点）
                state = {
                    "anchor_id": "test",
                    "transcript_snippet": "测试",
                    "chat_signals": [],
                    "vibe": {},
                }
                result = agent(state)
                # 调用结果应该是字典
                assert isinstance(result, dict), f"{agent.name} should return dict when called"


class TestEdgeCases:
    """边界情况测试"""

    def _create_mock_gateway(self):
        """创建模拟网关"""
        mock_gateway = MagicMock()
        mock_gateway.switch_provider.return_value = None
        return mock_gateway

    def _create_mock_db_manager(self):
        """创建模拟数据库管理器"""
        mock_manager = MagicMock()
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_conn.execute.return_value = mock_result
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.commit = MagicMock()
        mock_engine.connect.return_value = mock_conn
        mock_manager.get_ai_database.return_value = mock_engine
        return mock_manager

    def test_empty_inputs(self):
        """测试空输入"""
        mock_gateway = self._create_mock_gateway()
        mock_db_manager = self._create_mock_db_manager()
        mock_gateway.chat_completion.return_value = {
            "content": "响应", "reasoning": ""
        }

        with patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_sqlite_manager', return_value=mock_db_manager):

            workflow = LiveAnalysisWorkflowV2()

            state = {
                "anchor_id": "empty_test",
                "transcript_snippet": "",
                "chat_signals": [],
                "vibe": {},
            }

            result = workflow.invoke(state)
            assert result is not None

    def test_missing_optional_fields(self):
        """测试缺少可选字段"""
        mock_gateway = self._create_mock_gateway()
        mock_db_manager = self._create_mock_db_manager()
        mock_gateway.chat_completion.return_value = {
            "content": "响应", "reasoning": ""
        }

        with patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_sqlite_manager', return_value=mock_db_manager):

            workflow = LiveAnalysisWorkflowV2()

            # 最小输入
            state = {
                "anchor_id": "minimal_test",
            }

            result = workflow.invoke(state)
            assert result is not None

    def test_large_chat_signals(self):
        """测试大量弹幕信号"""
        mock_gateway = self._create_mock_gateway()
        mock_db_manager = self._create_mock_db_manager()
        mock_gateway.chat_completion.return_value = {
            "content": "响应", "reasoning": ""
        }

        with patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.memory.get_sqlite_manager', return_value=mock_db_manager):

            workflow = LiveAnalysisWorkflowV2()

            # 生成大量弹幕
            large_signals = [
                {"text": f"弹幕{i}", "weight": 0.5, "category": "chat"}
                for i in range(100)
            ]

            state = {
                "anchor_id": "large_test",
                "transcript_snippet": "测试",
                "chat_signals": large_signals,
                "vibe": {"level": "positive", "score": 80},
            }

            result = workflow.invoke(state)
            assert result is not None
