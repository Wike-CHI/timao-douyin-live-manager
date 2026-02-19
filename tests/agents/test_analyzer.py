"""测试Analyzer Agent"""
import pytest
from unittest.mock import MagicMock, patch
from server.agents.analyzer import AnalyzerAgent


class TestAnalyzerAgent:
    """AnalyzerAgent测试"""

    def test_analyzer_initialization(self):
        """测试分析器初始化"""
        with patch('server.agents.analyzer.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_get_gateway.return_value = mock_gateway

            agent = AnalyzerAgent()
            assert agent.name == "analyzer"
            assert agent.provider == "minimax"
            assert agent.model == "MiniMax-M2.5-highspeed"
            assert agent.enable_thinking is False
            # 验证初始化时切换了provider
            mock_gateway.switch_provider.assert_called_once_with("minimax", "MiniMax-M2.5-highspeed")

    def test_analyzer_run_with_signals(self):
        """测试分析器处理信号"""
        with patch('server.agents.analyzer.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.chat_completion.return_value = {
                "content": "主播正在与观众互动",
                "reasoning": ""
            }
            mock_get_gateway.return_value = mock_gateway

            agent = AnalyzerAgent()

            state = {
                "transcript_snippet": "大家好，欢迎来到直播间",
                "chat_signals": [
                    {"text": "主播好", "weight": 0.5, "category": "support"}
                ],
                "vibe": {"level": "neutral", "score": 50},
            }

            result = agent.run(state)
            assert result.success is True
            assert "analysis" in result.data
            # 验证run中不再调用switch_provider（只在初始化时调用一次）
            assert mock_gateway.switch_provider.call_count == 1  # 仅初始化时调用

    def test_analyzer_run_empty_state(self):
        """测试分析器处理空状态"""
        with patch('server.agents.analyzer.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.chat_completion.return_value = {"content": "等待数据", "reasoning": ""}
            mock_get_gateway.return_value = mock_gateway

            agent = AnalyzerAgent()

            result = agent.run({})
            assert result.success is True

    def test_analyzer_build_prompt(self):
        """测试提示词构建"""
        with patch('server.agents.analyzer.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_get_gateway.return_value = mock_gateway

            agent = AnalyzerAgent()

            prompt = agent._build_prompt(
                transcript="测试口播",
                chat_signals=[{"text": "测试弹幕", "weight": 0.8}],
                vibe={"level": "positive", "score": 80}
            )

            assert "测试口播" in prompt
            assert "测试弹幕" in prompt
            assert "positive" in prompt

    def test_analyzer_run_handles_exception(self):
        """测试分析器异常处理"""
        with patch('server.agents.analyzer.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_gateway.chat_completion.side_effect = Exception("API错误")
            mock_get_gateway.return_value = mock_gateway

            agent = AnalyzerAgent()

            result = agent.run({})
            assert result.success is False
            assert "API错误" in result.error
