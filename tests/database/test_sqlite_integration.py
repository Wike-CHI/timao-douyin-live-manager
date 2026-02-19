"""SQLite集成测试

测试完整的SQLite数据库工作流程
"""
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from sqlalchemy import text

from server.database import (
    SQLiteDatabaseManager,
    SQLiteConfig,
    get_sqlite_manager,
    close_sqlite,
    init_ai_tables,
)


class TestSQLiteIntegration:
    """SQLite集成测试"""

    def test_full_initialization_workflow(self):
        """测试完整初始化流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. 创建配置
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)

            # 2. 初始化
            manager.initialize()

            # 3. 验证目录结构
            assert Path(tmpdir).exists()
            assert (Path(tmpdir) / "timao.db").exists()
            assert (Path(tmpdir) / "ai").exists()
            assert (Path(tmpdir) / "sessions").exists()

            # 4. 关闭
            manager.close()

    def test_full_workflow_with_ai_tables(self):
        """测试包含AI表的完整流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()

            # 初始化AI表
            init_ai_tables(manager)

            # 验证AI数据库文件
            assert (Path(tmpdir) / "ai" / "memory_vectors.db").exists()
            assert (Path(tmpdir) / "ai" / "style_profiles.db").exists()
            assert (Path(tmpdir) / "ai" / "ai_usage_logs.db").exists()

            manager.close()

    def test_session_database_workflow(self):
        """测试直播会话数据库流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()

            # 获取当前月份的会话数据库
            session_db = manager.get_current_session_database()
            assert session_db is not None

            # 验证数据库文件已创建
            now = datetime.now()
            expected_path = Path(tmpdir) / "sessions" / f"live_{now.year:04d}-{now.month:02d}.db"
            assert expected_path.exists()

            manager.close()

    def test_crud_operations_workflow(self):
        """测试CRUD操作流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()
            init_ai_tables(manager)

            # 1. CREATE - 插入向量记忆
            memory_engine = manager.get_ai_database("memory_vectors")
            with memory_engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO memory_vectors (anchor_id, memory_type, content)
                    VALUES ('anchor_001', 'style', '主播风格很活泼')
                """))
                conn.commit()

            # 2. READ - 读取记忆
            with memory_engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM memory_vectors WHERE anchor_id = 'anchor_001'
                """)).fetchone()
                assert result is not None
                # 获取列名映射
                columns = result._fields if hasattr(result, '_fields') else []
                if columns:
                    # 找到memory_type列的索引
                    type_idx = columns.index('memory_type') if 'memory_type' in columns else 1
                    assert result[type_idx] == 'style'
                else:
                    # 回退到位置查找
                    assert 'style' in str(result)

            # 3. UPDATE - 更新访问计数
            with memory_engine.connect() as conn:
                conn.execute(text("""
                    UPDATE memory_vectors
                    SET access_count = access_count + 1
                    WHERE anchor_id = 'anchor_001'
                """))
                conn.commit()

            # 4. DELETE - 删除记忆
            with memory_engine.connect() as conn:
                conn.execute(text("""
                    DELETE FROM memory_vectors WHERE anchor_id = 'anchor_001'
                """))
                conn.commit()

            # 验证删除
            with memory_engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT * FROM memory_vectors WHERE anchor_id = 'anchor_001'
                """)).fetchone()
                assert result is None

            manager.close()

    def test_ai_usage_logging_workflow(self):
        """测试AI使用日志流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()
            init_ai_tables(manager)

            # 记录AI调用
            logs_engine = manager.get_ai_database("ai_usage_logs")
            with logs_engine.connect() as conn:
                # 插入多条日志
                for i in range(3):
                    conn.execute(text("""
                        INSERT INTO ai_usage_logs
                        (provider, model, function, prompt_tokens, completion_tokens, cost, duration_ms)
                        VALUES ('glm', 'glm-5', 'live_analysis', 100, 50, 0.01, 500)
                    """))
                conn.commit()

            # 查询日志
            with logs_engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM ai_usage_logs WHERE provider = 'glm'
                """)).fetchone()
                assert result[0] == 3

            manager.close()

    def test_style_profile_workflow(self):
        """测试风格画像流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()
            init_ai_tables(manager)

            # 创建风格画像
            style_engine = manager.get_ai_database("style_profiles")
            with style_engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO style_profiles (anchor_id, profile_data)
                    VALUES ('anchor_001', '{"style": "energetic", "topics": ["游戏", "聊天"]}')
                """))
                conn.commit()

            # 更新风格画像
            with style_engine.connect() as conn:
                conn.execute(text("""
                    UPDATE style_profiles
                    SET profile_data = '{"style": "calm", "topics": ["音乐", "聊天"]}',
                        version = version + 1
                    WHERE anchor_id = 'anchor_001'
                """))
                conn.commit()

            # 验证更新
            with style_engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT version, profile_data FROM style_profiles WHERE anchor_id = 'anchor_001'
                """)).fetchone()
                assert result[0] == 2  # version incremented
                assert 'calm' in result[1]

            manager.close()

    def test_global_singleton_workflow(self):
        """测试全局单例流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 重置全局实例
            close_sqlite()

            # 创建自定义配置的实例
            from server.database import sqlite_manager
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)

            # 手动设置全局实例
            import server.database.sqlite_manager as sm
            sm._db_manager = manager
            sm._db_manager.initialize()

            # 获取全局实例
            global_manager = get_sqlite_manager()
            assert global_manager is manager

            # 使用全局实例
            with global_manager.get_session() as session:
                session.execute(text("CREATE TABLE IF NOT EXISTS test (id INTEGER)"))
                session.execute(text("INSERT INTO test VALUES (1)"))

            # 验证
            with global_manager.get_session() as session:
                result = session.execute(text("SELECT * FROM test")).fetchone()
                assert result == (1,)

            # 清理
            close_sqlite()

    def test_multiple_ai_databases_workflow(self):
        """测试多个AI数据库协同工作流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()
            init_ai_tables(manager)

            # 在memory_vectors中记录记忆
            memory_engine = manager.get_ai_database("memory_vectors")
            with memory_engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO memory_vectors (anchor_id, memory_type, content, importance_score)
                    VALUES ('anchor_001', 'style', '主播很幽默', 0.8)
                """))
                conn.commit()

            # 在style_profiles中创建画像
            style_engine = manager.get_ai_database("style_profiles")
            with style_engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO style_profiles (anchor_id, profile_data)
                    VALUES ('anchor_001', '{"humor_level": "high"}')
                """))
                conn.commit()

            # 在ai_usage_logs中记录调用
            logs_engine = manager.get_ai_database("ai_usage_logs")
            with logs_engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO ai_usage_logs (provider, model, function, prompt_tokens)
                    VALUES ('qwen', 'qwen-plus', 'style_analysis', 200)
                """))
                conn.commit()

            # 验证所有数据
            with memory_engine.connect() as conn:
                mem_result = conn.execute(text(
                    "SELECT content FROM memory_vectors WHERE anchor_id = 'anchor_001'"
                )).fetchone()
                assert mem_result is not None

            with style_engine.connect() as conn:
                style_result = conn.execute(text(
                    "SELECT profile_data FROM style_profiles WHERE anchor_id = 'anchor_001'"
                )).fetchone()
                assert style_result is not None

            with logs_engine.connect() as conn:
                logs_result = conn.execute(text(
                    "SELECT model FROM ai_usage_logs WHERE function = 'style_analysis'"
                )).fetchone()
                assert logs_result is not None

            manager.close()

    def test_session_database_monthly_rotation(self):
        """测试直播会话数据库按月分库"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()

            # 获取不同月份的数据库
            db_2025_01 = manager.get_session_database(2025, 1)
            db_2025_02 = manager.get_session_database(2025, 2)

            # 验证是不同的引擎
            assert db_2025_01 is not db_2025_02

            # 验证数据库文件
            assert (Path(tmpdir) / "sessions" / "live_2025-01.db").exists()
            assert (Path(tmpdir) / "sessions" / "live_2025-02.db").exists()

            # 在不同数据库中插入数据
            with db_2025_01.connect() as conn:
                conn.execute(text("CREATE TABLE test (id INTEGER)"))
                conn.execute(text("INSERT INTO test VALUES (1)"))
                conn.commit()

            with db_2025_02.connect() as conn:
                conn.execute(text("CREATE TABLE test (id INTEGER)"))
                conn.execute(text("INSERT INTO test VALUES (2)"))
                conn.commit()

            # 验证数据隔离
            with db_2025_01.connect() as conn:
                result = conn.execute(text("SELECT * FROM test")).fetchone()
                assert result[0] == 1

            with db_2025_02.connect() as conn:
                result = conn.execute(text("SELECT * FROM test")).fetchone()
                assert result[0] == 2

            manager.close()

    def test_database_cleanup_and_reopen(self):
        """测试数据库关闭和重新打开"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 第一次初始化
            config = SQLiteConfig(data_dir=tmpdir)
            manager1 = SQLiteDatabaseManager(config)
            manager1.initialize()
            init_ai_tables(manager1)

            # 插入数据
            memory_engine = manager1.get_ai_database("memory_vectors")
            with memory_engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO memory_vectors (anchor_id, memory_type, content)
                    VALUES ('anchor_001', 'style', '测试数据')
                """))
                conn.commit()

            manager1.close()

            # 重新打开
            manager2 = SQLiteDatabaseManager(config)
            manager2.initialize()

            # 验证数据仍然存在
            memory_engine2 = manager2.get_ai_database("memory_vectors")
            with memory_engine2.connect() as conn:
                result = conn.execute(text(
                    "SELECT content FROM memory_vectors WHERE anchor_id = 'anchor_001'"
                )).fetchone()
                assert result is not None
                assert '测试数据' in result[0]

            manager2.close()

    def test_concurrent_access_to_different_databases(self):
        """测试并发访问不同数据库"""
        import threading

        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()
            init_ai_tables(manager)

            results = []

            def write_to_memory():
                try:
                    engine = manager.get_ai_database("memory_vectors")
                    with engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO memory_vectors (anchor_id, memory_type, content)
                            VALUES ('thread1', 'test', 'Thread 1 data')
                        """))
                        conn.commit()
                    results.append('memory_ok')
                except Exception as e:
                    results.append(f'memory_error: {e}')

            def write_to_style():
                try:
                    engine = manager.get_ai_database("style_profiles")
                    with engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO style_profiles (anchor_id, profile_data)
                            VALUES ('thread2', '{"test": true}')
                        """))
                        conn.commit()
                    results.append('style_ok')
                except Exception as e:
                    results.append(f'style_error: {e}')

            # 并发执行
            t1 = threading.Thread(target=write_to_memory)
            t2 = threading.Thread(target=write_to_style)

            t1.start()
            t2.start()
            t1.join()
            t2.join()

            # 验证两个操作都成功
            assert 'memory_ok' in results
            assert 'style_ok' in results

            manager.close()

    def test_error_handling_workflow(self):
        """测试错误处理流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()

            # 测试获取不存在的数据库时自动创建
            custom_engine = manager.get_ai_database("custom_db")
            assert custom_engine is not None
            assert (Path(tmpdir) / "ai" / "custom_db.db").exists()

            # 测试在关闭后访问
            manager.close()

            with pytest.raises(RuntimeError, match="Database not initialized"):
                with manager.get_session() as session:
                    pass

    def test_memory_summaries_workflow(self):
        """测试记忆摘要流程"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()
            init_ai_tables(manager)

            # 记忆摘要在memory_vectors数据库中
            memory_engine = manager.get_ai_database("memory_vectors")

            # 插入记忆摘要
            with memory_engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO memory_summaries (anchor_id, period_start, period_end, summary_text, key_insights)
                    VALUES (
                        'anchor_001',
                        '2025-01-01 00:00:00',
                        '2025-01-31 23:59:59',
                        '本月主播表现活跃，互动频繁',
                        '["高频互动", "游戏内容为主"]'
                    )
                """))
                conn.commit()

            # 查询摘要
            with memory_engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT summary_text, key_insights
                    FROM memory_summaries
                    WHERE anchor_id = 'anchor_001'
                """)).fetchone()
                assert result is not None
                assert '活跃' in result[0]

            manager.close()
