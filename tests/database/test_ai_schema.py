"""测试AI数据库Schema"""
import pytest
import tempfile
from pathlib import Path
from sqlalchemy import text

from server.database.sqlite_manager import SQLiteDatabaseManager, SQLiteConfig
from server.database.ai_schema import init_ai_tables


class TestAISchema:
    """AI数据库Schema测试"""

    def test_init_memory_vectors_table(self):
        """测试初始化向量记忆表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            try:
                manager.initialize()

                # 初始化AI表
                init_ai_tables(manager)

                # 检查表已创建
                engine = manager.get_ai_database("memory_vectors")
                with engine.connect() as conn:
                    result = conn.execute(
                        text("SELECT name FROM sqlite_master WHERE type='table' AND name='memory_vectors'")
                    ).fetchone()
                    assert result is not None
            finally:
                manager.close()

    def test_init_style_profiles_table(self):
        """测试初始化风格画像表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            try:
                manager.initialize()

                init_ai_tables(manager)

                engine = manager.get_ai_database("style_profiles")
                with engine.connect() as conn:
                    result = conn.execute(
                        text("SELECT name FROM sqlite_master WHERE type='table' AND name='style_profiles'")
                    ).fetchone()
                    assert result is not None
            finally:
                manager.close()

    def test_init_ai_usage_logs_table(self):
        """测试初始化AI使用日志表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            try:
                manager.initialize()

                init_ai_tables(manager)

                engine = manager.get_ai_database("ai_usage_logs")
                with engine.connect() as conn:
                    result = conn.execute(
                        text("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_usage_logs'")
                    ).fetchone()
                    assert result is not None
            finally:
                manager.close()

    def test_memory_vectors_indexes(self):
        """测试向量记忆表索引"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            try:
                manager.initialize()
                init_ai_tables(manager)

                engine = manager.get_ai_database("memory_vectors")
                with engine.connect() as conn:
                    result = conn.execute(
                        text("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_memory%'")
                    ).fetchall()
                    index_names = [r[0] for r in result]
                    assert "idx_memory_anchor" in index_names
                    assert "idx_memory_type" in index_names
            finally:
                manager.close()

    def test_insert_memory_vector(self):
        """测试插入向量记忆"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            try:
                manager.initialize()
                init_ai_tables(manager)

                engine = manager.get_ai_database("memory_vectors")
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO memory_vectors (anchor_id, memory_type, content)
                        VALUES ('test_anchor', 'style', 'Test content')
                    """))
                    conn.commit()

                    result = conn.execute(
                        text("SELECT * FROM memory_vectors WHERE anchor_id = 'test_anchor'")
                    ).fetchone()
                    assert result is not None
            finally:
                manager.close()

    def test_insert_style_profile(self):
        """测试插入风格画像"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            try:
                manager.initialize()
                init_ai_tables(manager)

                engine = manager.get_ai_database("style_profiles")
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO style_profiles (anchor_id, profile_data)
                        VALUES ('test_anchor', '{"style": "energetic"}')
                    """))
                    conn.commit()

                    result = conn.execute(
                        text("SELECT * FROM style_profiles WHERE anchor_id = 'test_anchor'")
                    ).fetchone()
                    assert result is not None
            finally:
                manager.close()

    def test_insert_ai_usage_log(self):
        """测试插入AI使用日志"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            try:
                manager.initialize()
                init_ai_tables(manager)

                engine = manager.get_ai_database("ai_usage_logs")
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO ai_usage_logs (provider, model, function, prompt_tokens, completion_tokens)
                        VALUES ('glm', 'glm-5', 'live_analysis', 100, 50)
                    """))
                    conn.commit()

                    result = conn.execute(
                        text("SELECT * FROM ai_usage_logs WHERE provider = 'glm'")
                    ).fetchone()
                    assert result is not None
            finally:
                manager.close()
