"""测试Memory Agent"""
import pytest
from unittest.mock import MagicMock, patch
from server.agents.memory import MemoryAgent


class TestMemoryAgent:
    """MemoryAgent测试"""

    def test_memory_initialization(self):
        """测试记忆Agent初始化"""
        with patch('server.agents.memory.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_get_gateway.return_value = mock_gateway

            agent = MemoryAgent()
            assert agent.name == "memory"
            assert agent.provider == "glm"
            assert agent.model == "glm-5"
            assert agent.enable_thinking is True
            # 验证初始化时切换了provider
            mock_gateway.switch_provider.assert_called_once_with("glm", "glm-5")

    def test_memory_load_action(self):
        """测试加载记忆"""
        with patch('server.agents.memory.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_get_gateway.return_value = mock_gateway

            agent = MemoryAgent()

            state = {
                "memory_action": "load",
                "anchor_id": "test_anchor",
            }

            # Mock数据库
            mock_db = MagicMock()
            mock_engine = MagicMock()
            mock_conn = MagicMock()
            mock_result = MagicMock()
            mock_result.fetchall.return_value = [
                ("记忆内容1", '{"type": "style"}', 0.8),
                ("记忆内容2", '{"type": "feedback"}', 0.6),
            ]
            mock_conn.execute.return_value = mock_result
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=False)
            mock_engine.connect.return_value = mock_conn
            mock_db.get_ai_database.return_value = mock_engine

            with patch.object(agent, '_get_db', return_value=mock_db):
                result = agent.run(state)

            assert result.success is True
            assert "memories" in result.data
            assert len(result.data["memories"]) == 2

    def test_memory_save_action(self):
        """测试保存记忆"""
        with patch('server.agents.memory.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_get_gateway.return_value = mock_gateway

            agent = MemoryAgent()

            state = {
                "memory_action": "save",
                "anchor_id": "test_anchor",
                "memory_content": "这是一条新记忆",
                "memory_type": "feedback",
            }

            # Mock数据库
            mock_db = MagicMock()
            mock_engine = MagicMock()
            mock_conn = MagicMock()
            mock_conn.execute.return_value = None
            mock_conn.commit.return_value = None
            mock_conn.__enter__ = MagicMock(return_value=mock_conn)
            mock_conn.__exit__ = MagicMock(return_value=False)
            mock_engine.connect.return_value = mock_conn
            mock_db.get_ai_database.return_value = mock_engine

            with patch.object(agent, '_get_db', return_value=mock_db):
                result = agent.run(state)

            assert result.success is True
            assert result.data["saved"] is True

    def test_memory_save_empty_content(self):
        """测试保存空内容"""
        with patch('server.agents.memory.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_get_gateway.return_value = mock_gateway

            agent = MemoryAgent()

            state = {
                "memory_action": "save",
                "anchor_id": "test_anchor",
                "memory_content": "",
            }

            result = agent.run(state)

            assert result.success is True
            assert result.data["saved"] is False
            assert "reason" in result.data

    def test_memory_unknown_action(self):
        """测试未知操作"""
        with patch('server.agents.memory.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_get_gateway.return_value = mock_gateway

            agent = MemoryAgent()

            state = {
                "memory_action": "unknown",
            }

            result = agent.run(state)

            assert result.success is False
            assert "未知" in result.error

    def test_memory_load_handles_exception(self):
        """测试加载异常处理"""
        with patch('server.agents.memory.get_gateway') as mock_get_gateway:
            mock_gateway = MagicMock()
            mock_get_gateway.return_value = mock_gateway

            agent = MemoryAgent()

            state = {
                "memory_action": "load",
                "anchor_id": "test_anchor",
            }

            with patch.object(agent, '_get_db', side_effect=Exception("DB Error")):
                result = agent.run(state)

            assert result.success is False
            assert result.data["memories"] == []
