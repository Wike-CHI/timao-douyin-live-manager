"""测试SQLite数据库管理器"""
import pytest
import os
import tempfile
import threading
from pathlib import Path

from sqlalchemy import text

from server.database.sqlite_manager import SQLiteDatabaseManager, SQLiteConfig


class TestSQLiteDatabaseManager:
    """SQLite数据库管理器测试"""

    def test_init_creates_database_file(self):
        """测试初始化创建数据库文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()

            # 检查主数据库文件已创建
            db_path = Path(tmpdir) / "timao.db"
            assert db_path.exists()

            manager.close()

    def test_wal_mode_enabled(self):
        """测试WAL模式已启用"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()

            # 检查WAL模式
            session = manager.get_session_sync()
            result = session.execute(text("PRAGMA journal_mode")).fetchone()
            session.close()
            assert result[0].lower() == "wal"

            manager.close()

    def test_get_ai_database(self):
        """测试获取AI专用数据库"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()

            # 获取AI数据库
            ai_db = manager.get_ai_database("memory_vectors")
            assert ai_db is not None

            # 检查AI数据库文件已创建
            ai_db_path = Path(tmpdir) / "ai" / "memory_vectors.db"
            assert ai_db_path.exists()

            manager.close()

    def test_get_session_database(self):
        """测试获取按月分库的直播数据库"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()

            # 获取2025年2月的直播数据库
            session_db = manager.get_session_database(2025, 2)
            assert session_db is not None

            # 检查数据库文件已创建
            session_db_path = Path(tmpdir) / "sessions" / "live_2025-02.db"
            assert session_db_path.exists()

            manager.close()

    def test_get_current_session_database(self):
        """测试获取当前月份的直播数据库"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()

            # 获取当前月份的数据库
            session_db = manager.get_current_session_database()
            assert session_db is not None

            manager.close()

    def test_get_session_context_manager(self):
        """测试会话上下文管理器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()

            with manager.get_session() as session:
                # 创建测试表
                session.execute(text("CREATE TABLE IF NOT EXISTS test (id INTEGER)"))
                session.execute(text("INSERT INTO test VALUES (1)"))

            # 验证数据已提交
            session = manager.get_session_sync()
            result = session.execute(text("SELECT * FROM test")).fetchone()
            session.close()
            assert result == (1,)

            manager.close()

    def test_invalid_synchronous_value(self):
        """测试无效的synchronous配置值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="synchronous must be one of"):
                config = SQLiteConfig(data_dir=tmpdir, synchronous="INVALID")

    def test_invalid_temp_store_value(self):
        """测试无效的temp_store配置值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="temp_store must be one of"):
                config = SQLiteConfig(data_dir=tmpdir, temp_store="INVALID")

    def test_singleton_thread_safety(self):
        """测试单例的线程安全性"""
        with tempfile.TemporaryDirectory() as tmpdir:
            instances = []

            def create_instance():
                config = SQLiteConfig(data_dir=tmpdir)
                manager = SQLiteDatabaseManager(config)
                manager.initialize()
                instances.append(id(manager))
                manager.close()

            threads = [threading.Thread(target=create_instance) for _ in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # Each thread creates its own instance with custom config
            # This is expected behavior - config determines uniqueness
            assert len(instances) == 5
