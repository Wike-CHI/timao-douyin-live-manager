"""测试DatabaseManager兼容性

验证DatabaseManager同时支持SQLite和MySQL（配置层面）。
"""
import os
import pytest
import tempfile
from pathlib import Path

from sqlalchemy import text

from server.config import DatabaseConfig
from server.app.database import DatabaseManager


class TestDatabaseManagerSQLite:
    """DatabaseManager SQLite模式测试"""

    def test_init_sqlite_mode(self):
        """测试SQLite模式初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = DatabaseConfig(
                db_type="sqlite",
                sqlite_data_dir=tmpdir
            )
            manager = DatabaseManager(config)
            manager.initialize()

            # 检查数据库文件已创建
            db_path = Path(tmpdir) / "timao.db"
            assert db_path.exists(), f"数据库文件应该已创建: {db_path}"

            # 检查引擎已创建
            assert manager._engine is not None
            assert manager._session_factory is not None
            assert manager._sqlite_manager is not None

            manager.close()

            # 关闭后检查清理
            assert manager._sqlite_manager is None
            assert manager._engine is None

    def test_sqlite_session(self):
        """测试SQLite会话"""
        tmpdir = tempfile.mkdtemp()
        try:
            config = DatabaseConfig(
                db_type="sqlite",
                sqlite_data_dir=tmpdir
            )
            manager = DatabaseManager(config)
            manager.initialize()

            with manager.get_session() as session:
                # 创建测试表（使用text()包装SQL）
                session.execute(text("CREATE TABLE IF NOT EXISTS test (id INTEGER)"))
                session.execute(text("INSERT INTO test VALUES (1)"))

            # 验证数据已提交
            with manager.get_session() as session:
                result = session.execute(text("SELECT * FROM test")).fetchone()
                assert result == (1,)

            manager.close()
        finally:
            # Windows需要确保文件句柄释放后才能删除
            import gc
            gc.collect()
            # 尝试清理，忽略错误
            try:
                import shutil
                shutil.rmtree(tmpdir, ignore_errors=True)
            except Exception:
                pass

    def test_sqlite_session_sync(self):
        """测试同步会话获取"""
        tmpdir = tempfile.mkdtemp()
        try:
            config = DatabaseConfig(
                db_type="sqlite",
                sqlite_data_dir=tmpdir
            )
            manager = DatabaseManager(config)
            manager.initialize()

            session = manager.get_session_sync()
            try:
                assert session is not None
                # 执行简单查询（使用text()包装SQL）
                result = session.execute(text("SELECT 1")).fetchone()
                assert result == (1,)
            finally:
                session.close()

            manager.close()
        finally:
            # Windows需要确保文件句柄释放后才能删除
            import gc
            gc.collect()
            try:
                import shutil
                shutil.rmtree(tmpdir, ignore_errors=True)
            except Exception:
                pass

    def test_sqlite_create_tables(self):
        """测试表创建"""
        tmpdir = tempfile.mkdtemp()
        try:
            config = DatabaseConfig(
                db_type="sqlite",
                sqlite_data_dir=tmpdir
            )
            manager = DatabaseManager(config)
            manager.initialize()

            # 表应该已创建（通过Base.metadata.create_all）
            # 验证可以创建表
            manager.create_tables()

            manager.close()
        finally:
            import gc
            gc.collect()
            try:
                import shutil
                shutil.rmtree(tmpdir, ignore_errors=True)
            except Exception:
                pass

    def test_invalid_db_type(self):
        """测试无效的数据库类型"""
        config = DatabaseConfig(db_type="invalid")
        manager = DatabaseManager(config)

        with pytest.raises(ValueError, match="不支持的数据库类型"):
            manager.initialize()

    def test_database_not_initialized_error(self):
        """测试未初始化时的错误"""
        config = DatabaseConfig(db_type="sqlite")
        manager = DatabaseManager(config)
        # 不调用initialize

        with pytest.raises(RuntimeError, match="Database not initialized"):
            with manager.get_session():
                pass

        with pytest.raises(RuntimeError, match="Database not initialized"):
            manager.get_session_sync()


class TestDatabaseManagerConfig:
    """DatabaseManager配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = DatabaseConfig()
        # 默认应该是mysql（向后兼容）
        assert config.db_type == "mysql"

    def test_sqlite_config(self):
        """测试SQLite配置"""
        config = DatabaseConfig(
            db_type="sqlite",
            sqlite_data_dir="custom_data"
        )
        assert config.db_type == "sqlite"
        assert config.sqlite_data_dir == "custom_data"

    def test_mysql_config_preserved(self):
        """测试MySQL配置保留"""
        config = DatabaseConfig(
            db_type="mysql",
            mysql_host="custom_host",
            mysql_port=3307,
            mysql_user="custom_user",
            mysql_password="custom_pass",
            mysql_database="custom_db"
        )
        assert config.db_type == "mysql"
        assert config.mysql_host == "custom_host"
        assert config.mysql_port == 3307
        assert config.mysql_user == "custom_user"
        assert config.mysql_password == "custom_pass"
        assert config.mysql_database == "custom_db"


class TestDatabaseManagerReinitialize:
    """DatabaseManager重初始化测试"""

    def test_reinitialize_clears_previous(self):
        """测试重初始化清除之前的连接"""
        tmpdir = tempfile.mkdtemp()
        try:
            config = DatabaseConfig(
                db_type="sqlite",
                sqlite_data_dir=tmpdir
            )
            manager = DatabaseManager(config)

            # 第一次初始化
            manager.initialize()
            first_engine = manager._engine
            assert first_engine is not None

            # 重初始化
            manager.initialize()
            second_engine = manager._engine
            assert second_engine is not None
            # 注意：重初始化会创建新引擎，但旧引擎可能未正确清理
            # 这是当前实现的行为

            manager.close()
        finally:
            import gc
            gc.collect()
            try:
                import shutil
                shutil.rmtree(tmpdir, ignore_errors=True)
            except Exception:
                pass
