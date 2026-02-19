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
        assert agent.enable_thinking is False

    def test_analyzer_run_with_signals(self):
        """测试分析器处理信号"""
        agent = AnalyzerAgent()

        state = {
            "transcript_snippet": "大家好，欢迎来到直播间",
            "chat_signals": [
                {"text": "主播好", "weight": 0.5, "category": "support"}
            ],
            "vibe": {"level": "neutral", "score": 50},
        }

        # Mock the gateway's chat_completion method
        with patch.object(agent.gateway, 'chat_completion') as mock_chat:
            mock_chat.return_value = {
                "content": "主播正在与观众互动",
                "reasoning": ""
            }

            # Also mock switch_provider to avoid provider registration issues
            with patch.object(agent.gateway, 'switch_provider'):
                result = agent.run(state)
                assert result.success is True
                assert "analysis" in result.data

    def test_analyzer_run_empty_state(self):
        """测试分析器处理空状态"""
        agent = AnalyzerAgent()

        with patch.object(agent.gateway, 'chat_completion') as mock_chat:
            mock_chat.return_value = {"content": "等待数据", "reasoning": ""}

            with patch.object(agent.gateway, 'switch_provider'):
                result = agent.run({})
                assert result.success is True

    def test_analyzer_build_prompt(self):
        """测试提示词构建"""
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
        agent = AnalyzerAgent()

        with patch.object(agent.gateway, 'switch_provider') as mock_switch:
            mock_switch.side_effect = Exception("API错误")

            result = agent.run({})
            assert result.success is False
            assert "API错误" in result.error
