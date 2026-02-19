"""测试Decision Agent"""
import pytest
from unittest.mock import MagicMock, patch
from server.agents.decision import DecisionAgent


class TestDecisionAgent:
    """DecisionAgent测试"""

    def test_decision_initialization(self):
        """测试决策器初始化"""
        with patch('server.agents.decision.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_get_gateway.return_value = mock_gateway

            agent = DecisionAgent()
            assert agent.name == "decision_maker"
            assert agent.provider == "glm"
            assert agent.model == "glm-5"
            assert agent.enable_thinking is True
            # 验证初始化时切换了provider
            mock_gateway.switch_provider.assert_called_once_with("glm", "glm-5")

    def test_decision_run_with_analysis(self):
        """测试决策器处理分析结果"""
        with patch('server.agents.decision.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.chat_completion.return_value = {
                "content": "建议继续互动",
                "reasoning": "分析显示互动效果良好",
            }
            mock_get_gateway.return_value = mock_gateway

            agent = DecisionAgent()

            state = {
                "analysis_result": {"analysis": "主播正在与观众互动"},
                "style_profile": {"tone": "专业陪伴"},
                "planner_notes": {"selected_topic": {"topic": "互动"}},
            }

            result = agent.run(state)
            assert result.success is True
            assert "decision" in result.data
            assert "reasoning" in result.data
            # 验证run中不再调用switch_provider（只在初始化时调用一次）
            assert mock_gateway.switch_provider.call_count == 1  # 仅初始化时调用

    def test_decision_run_empty_state(self):
        """测试决策器处理空状态"""
        with patch('server.agents.decision.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.chat_completion.return_value = {
                "content": "等待更多数据",
                "reasoning": "",
            }
            mock_get_gateway.return_value = mock_gateway

            agent = DecisionAgent()

            result = agent.run({})
            assert result.success is True

    def test_decision_build_prompt(self):
        """测试提示词构建"""
        with patch('server.agents.decision.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_get_gateway.return_value = mock_gateway

            agent = DecisionAgent()

            prompt = agent._build_prompt(
                analysis={"analysis": "测试分析"},
                style_profile={"tone": "专业"},
                planner_notes={"selected_topic": {"topic": "销售"}}
            )

            assert "测试分析" in prompt
            assert "专业" in prompt
            assert "销售" in prompt

    def test_decision_run_handles_exception(self):
        """测试决策器异常处理"""
        with patch('server.agents.decision.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.chat_completion.side_effect = Exception("API错误")
            mock_get_gateway.return_value = mock_gateway

            agent = DecisionAgent()

            result = agent.run({})
            assert result.success is False
            assert "API错误" in result.error
