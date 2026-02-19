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
