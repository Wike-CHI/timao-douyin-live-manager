"""测试Reflection Agent"""
import pytest
from unittest.mock import MagicMock, patch
from server.agents.reflection import ReflectionAgent


class TestReflectionAgent:
    """ReflectionAgent测试"""

    def test_reflection_initialization(self):
        """测试反思器初始化"""
        with patch('server.agents.reflection.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_get_gateway.return_value = mock_gateway

            agent = ReflectionAgent()
            assert agent.name == "reflection"
            assert agent.provider == "glm"
            assert agent.model == "glm-5"
            assert agent.enable_thinking is True
            assert agent.QUALITY_THRESHOLD == 0.7
            # 验证初始化时切换了provider
            mock_gateway.switch_provider.assert_called_once_with("glm", "glm-5")

    def test_reflection_run_high_quality(self):
        """测试高质量分析（不需要重试）"""
        with patch('server.agents.reflection.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.chat_completion.return_value = {
                "content": "质量评分: 0.85\n需要重试: 否\n问题说明: 无",
                "reasoning": "分析完整、建议具体",
            }
            mock_get_gateway.return_value = mock_gateway

            agent = ReflectionAgent()

            state = {
                "analysis_result": {"analysis": "主播正在与观众互动，氛围良好"},
                "decision_result": {"decision": "建议继续互动"},
            }

            result = agent.run(state)
            assert result.success is True
            assert result.data["quality_score"] >= 0.7
            assert result.data["needs_retry"] is False
            # 验证run中不再调用switch_provider（只在初始化时调用一次）
            assert mock_gateway.switch_provider.call_count == 1  # 仅初始化时调用

    def test_reflection_run_low_quality(self):
        """测试低质量分析（需要重试）"""
        with patch('server.agents.reflection.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.chat_completion.return_value = {
                "content": "质量评分: 0.4\n需要重试: 是\n问题说明: 分析不完整",
                "reasoning": "缺少具体建议",
            }
            mock_get_gateway.return_value = mock_gateway

            agent = ReflectionAgent()

            state = {
                "analysis_result": {"analysis": "等待数据"},
                "decision_result": {"decision": "无法判断"},
            }

            result = agent.run(state)
            assert result.success is True
            assert result.data["quality_score"] < 0.7
            assert result.data["needs_retry"] is True

    def test_reflection_extract_score(self):
        """测试评分提取"""
        with patch('server.agents.reflection.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_get_gateway.return_value = mock_gateway

            agent = ReflectionAgent()

            # 测试正常提取
            score = agent._extract_score("质量评分: 0.85")
            assert score == 0.85

            # 测试无法提取时返回默认值
            score = agent._extract_score("没有评分")
            assert score == 0.7

    def test_reflection_run_handles_exception(self):
        """测试异常处理"""
        with patch('server.agents.reflection.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.chat_completion.side_effect = Exception("API Error")
            mock_get_gateway.return_value = mock_gateway

            agent = ReflectionAgent()

            result = agent.run({})
            assert result.success is False
            assert result.data["quality_score"] == 0.5
            assert result.data["needs_retry"] is False
