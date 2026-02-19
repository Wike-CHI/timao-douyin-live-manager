"""测试工作流V2"""
import pytest
from unittest.mock import MagicMock, patch

from server.agents.workflow_v2 import LiveAnalysisWorkflowV2, WorkflowState


class TestWorkflowV2:
    """LiveAnalysisWorkflowV2测试"""

    def _create_mock_gateway(self):
        """创建模拟网关"""
        mock_gateway = MagicMock()
        mock_gateway.switch_provider.return_value = None
        return mock_gateway

    def test_workflow_initialization(self):
        """测试工作流初始化"""
        mock_gateway = self._create_mock_gateway()

        with patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway):

            workflow = LiveAnalysisWorkflowV2()
            assert workflow.graph is not None
            assert workflow.workflow is not None
            assert workflow.memory_agent is not None
            assert workflow.analyzer_agent is not None
            assert workflow.decision_agent is not None
            assert workflow.reflection_agent is not None

    def test_workflow_max_retries(self):
        """测试最大重试次数"""
        mock_gateway = self._create_mock_gateway()

        with patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway):

            workflow = LiveAnalysisWorkflowV2()
            assert workflow.MAX_RETRIES == 2

    def test_workflow_invoke_basic(self):
        """测试基本工作流执行"""
        mock_gateway = self._create_mock_gateway()

        with patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway):

            workflow = LiveAnalysisWorkflowV2()

            state = {
                "anchor_id": "test_anchor",
                "transcript_snippet": "大家好，欢迎来到直播间",
                "chat_signals": [
                    {"text": "主播好", "weight": 0.5, "category": "support"}
                ],
                "vibe": {"level": "neutral", "score": 50},
            }

            # Mock所有Agent
            with patch.object(workflow.memory_agent, 'run') as mock_memory:
                mock_memory.return_value = MagicMock(
                    success=True,
                    data={"memories": [{"content": "历史记忆"}]}
                )

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

    def test_workflow_should_reflect(self):
        """测试是否需要反思判断"""
        mock_gateway = self._create_mock_gateway()

        with patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway):

            workflow = LiveAnalysisWorkflowV2()

            # 总是返回True（每次都反思）
            assert workflow._should_reflect({}) is True

    def test_workflow_should_retry(self):
        """测试是否需要重试判断"""
        mock_gateway = self._create_mock_gateway()

        with patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway):

            workflow = LiveAnalysisWorkflowV2()

            # 需要重试且未超过次数
            state = {
                "reflection_result": {"needs_retry": True},
                "retry_count": 0,
                "max_retries": 2,
            }
            assert workflow._should_retry(state) is True

            # 需要重试但已超过次数
            state = {
                "reflection_result": {"needs_retry": True},
                "retry_count": 2,
                "max_retries": 2,
            }
            assert workflow._should_retry(state) is False

            # 不需要重试
            state = {
                "reflection_result": {"needs_retry": False},
                "retry_count": 0,
                "max_retries": 2,
            }
            assert workflow._should_retry(state) is False

    def test_workflow_memory_updater_node(self):
        """测试记忆更新节点"""
        mock_gateway = self._create_mock_gateway()

        with patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway):

            workflow = LiveAnalysisWorkflowV2()

            state = {
                "anchor_id": "test",
                "decision_result": {"decision": "测试决策"},
            }

            with patch.object(workflow.memory_agent, 'run') as mock_memory:
                mock_memory.return_value = MagicMock(
                    success=True,
                    data={"saved": True}
                )

                result = workflow._memory_updater_node(state)
                assert "memory_result" in result
                assert result["memory_result"]["saved"] is True

    def test_workflow_agent_failure(self):
        """测试Agent失败场景"""
        mock_gateway = self._create_mock_gateway()

        with patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway):

            workflow = LiveAnalysisWorkflowV2()

            state = {
                "anchor_id": "test",
                "transcript_snippet": "测试",
                "chat_signals": [],
                "vibe": {},
            }

            with patch.object(workflow.memory_agent, 'run') as mock_memory:
                mock_memory.return_value = MagicMock(
                    success=True,
                    data={"memories": []}
                )

                with patch.object(workflow.analyzer_agent, 'run') as mock_analyzer:
                    mock_analyzer.return_value = MagicMock(
                        success=False,
                        error="API Error",
                        data={}
                    )

                    with patch.object(workflow.decision_agent, 'run') as mock_decision:
                        mock_decision.return_value = MagicMock(
                            success=True,
                            data={"decision": "默认决策"}
                        )

                        with patch.object(workflow.reflection_agent, 'run') as mock_reflect:
                            mock_reflect.return_value = MagicMock(
                                success=True,
                                data={"quality_score": 0.5, "needs_retry": False}
                            )

                            result = workflow.invoke(state)
                            # 工作流应该完成，即使有失败
                            assert result is not None
                            # 分析结果应该包含错误
                            assert "error" in result.get("analysis_result", {})

    def test_workflow_retry_loop(self):
        """测试重试循环"""
        mock_gateway = self._create_mock_gateway()

        with patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway):

            workflow = LiveAnalysisWorkflowV2()

            state = {
                "anchor_id": "test",
                "transcript_snippet": "测试",
                "chat_signals": [],
                "vibe": {},
            }

            call_count = {"count": 0}

            def mock_reflection_run(*args, **kwargs):
                call_count["count"] += 1
                # 第一次需要重试，第二次不需要
                needs_retry = call_count["count"] < 2
                return MagicMock(
                    success=True,
                    data={"quality_score": 0.5, "needs_retry": needs_retry}
                )

            with patch.object(workflow.memory_agent, 'run') as mock_memory:
                mock_memory.return_value = MagicMock(
                    success=True,
                    data={"memories": []}
                )

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

                        with patch.object(workflow.reflection_agent, 'run', side_effect=mock_reflection_run):
                            result = workflow.invoke(state)
                            # 应该触发一次重试
                            assert call_count["count"] >= 1
                            assert result is not None

    def test_invoke_does_not_mutate_input_state(self):
        """测试invoke不会修改输入的state"""
        mock_gateway = self._create_mock_gateway()

        with patch('server.agents.memory.get_gateway', return_value=mock_gateway), \
             patch('server.agents.analyzer.get_gateway', return_value=mock_gateway), \
             patch('server.agents.decision.get_gateway', return_value=mock_gateway), \
             patch('server.agents.reflection.get_gateway', return_value=mock_gateway):

            workflow = LiveAnalysisWorkflowV2()

            original_state = {
                "anchor_id": "test",
                "transcript_snippet": "测试",
                "chat_signals": [],
                "vibe": {},
            }

            # 保存原始状态的副本用于比较
            import copy
            state_copy = copy.deepcopy(original_state)

            with patch.object(workflow.memory_agent, 'run') as mock_memory:
                mock_memory.return_value = MagicMock(
                    success=True,
                    data={"memories": []}
                )

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

                            workflow.invoke(original_state)
                            # 原始状态不应该被修改
                            assert original_state == state_copy
                            assert "retry_count" not in original_state
