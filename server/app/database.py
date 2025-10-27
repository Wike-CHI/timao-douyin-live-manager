import logging
import os
from contextlib import contextmanager
from typing import Generator, Optional
from urllib.parse import quote_plus

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from server.app.models import Base
from server.config import DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    def initialize(self) -> None:
        """初始化数据库连接并建表"""
        self._engine = None
        self._session_factory = None

        if self.config.db_type == "mysql":
            try:
                self._init_mysql_engine()
                backend_name = "MYSQL"
                logger.info(
                    "✅ 使用 MySQL 数据库：%s@%s:%s/%s",
                    self.config.mysql_user,
                    self.config.mysql_host,
                    self.config.mysql_port,
                    self.config.mysql_database,
                )
            except OperationalError as exc:
                self._log_mysql_error(exc)
                raise
            except Exception as exc:
                logger.error("❌ 初始化 MySQL 失败：%s", exc)
                raise
        else:
            self._init_sqlite_engine()
            backend_name = "SQLITE"

        # 创建会话工厂
        self._session_factory = sessionmaker(
            bind=self._engine, autocommit=False, autoflush=False
        )

        # 创建所有表
        self.create_tables()
        logger.info("✅ 数据库初始化完成，当前后端：%s", backend_name)

    def _init_mysql_engine(self) -> None:
        """初始化 MySQL 数据库引擎"""
        # 构建 MySQL 连接字符串
        user = quote_plus(self.config.mysql_user)
        password = quote_plus(self.config.mysql_password or "")
        host = self.config.mysql_host
        port = self.config.mysql_port
        database = self.config.mysql_database
        charset = self.config.mysql_charset

        # 先尝试创建数据库（若用户具备权限）
        if self.config.mysql_auto_create_db:
            try:
                self._ensure_mysql_database(
                    user, password, host, port, database, charset
                )
            except OperationalError as exc:
                # 仅记录，部分线上环境会禁用创建权限
                logger.debug("跳过 MySQL 数据库自动创建：%s", exc)
            except Exception as exc:  # pragma: no cover - 防御性日志
                logger.warning("尝试自动创建 MySQL 数据库时出错（可忽略）：%s", exc)

        connection_url = (
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
            f"?charset={charset}"
        )

        # 创建数据库引擎
        self._engine = create_engine(
            connection_url,
            pool_size=self.config.pool_size,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=self.config.pool_pre_ping,
            max_overflow=self.config.max_overflow,
            echo=False  # 生产环境关闭SQL日志
        )

    def _ensure_mysql_database(
        self,
        user: str,
        password: str,
        host: str,
        port: int,
        database: str,
        charset: str,
    ) -> None:
        """确保目标数据库存在"""
        server_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/"
        tmp_engine = create_engine(
            server_url,
            pool_pre_ping=True,
            echo=False,
            isolation_level="AUTOCOMMIT",
        )

        db_identifier = database.replace("`", "``")
        try:
            with tmp_engine.connect() as conn:
                conn.execute(
                    text(f"CREATE DATABASE IF NOT EXISTS `{db_identifier}` "
                         "CHARACTER SET :charset"),
                    {"charset": charset},
                )
                conn.execute(
                    text(f"ALTER DATABASE `{db_identifier}` CHARACTER SET :charset"),
                    {"charset": charset},
                )
        finally:
            tmp_engine.dispose()

    def _log_mysql_error(self, exc: OperationalError) -> None:
        """记录更友好的 MySQL 连接错误信息"""
        masked_pwd = "******" if self.config.mysql_password else "(空密码)"
        logger.error(
            "❌ 无法连接到 MySQL：%s@%s:%s/%s（密码：%s）",
            self.config.mysql_user,
            self.config.mysql_host,
            self.config.mysql_port,
            self.config.mysql_database,
            masked_pwd,
        )
        logger.error("   详细错误：%s", exc)
        logger.error(
            "   请检查：1) 用户名/密码是否正确；2) 用户是否允许从 localhost 登录；"
            "3) 若使用 MySQL 8，确认用户插件为 mysql_native_password 或正确配置；"
            "4) 数据库 %s 是否存在（或开启 mysql_auto_create_db 自动建库）；"
            "5) 本地 MySQL 服务是否启动",
            self.config.mysql_database,
        )
    
    def _init_sqlite_engine(self) -> None:
        """初始化 SQLite 数据库引擎"""
        # 创建数据库目录
        db_path = self.config.sqlite_path
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # 创建数据库引擎（SQLite 不支持 pool_size 等参数）
        self._engine = create_engine(
            f"sqlite:///{db_path}",
            poolclass=StaticPool,
            connect_args={
                "check_same_thread": False,
                "timeout": self.config.sqlite_timeout
            },
            echo=False  # 生产环境关闭SQL日志
        )
        
        # 启用SQLite外键约束
        @event.listens_for(self._engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")  # 启用WAL模式提高并发性能
            cursor.execute("PRAGMA synchronous=NORMAL")  # 平衡性能和安全性
            cursor.close()
    
    def create_tables(self) -> None:
        """创建所有数据库表"""
        if self._engine:
            Base.metadata.create_all(bind=self._engine)
    
    def drop_tables(self) -> None:
        """删除所有数据库表（谨慎使用）"""
        if self._engine:
            Base.metadata.drop_all(bind=self._engine)
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话上下文管理器"""
        if not self._session_factory:
            raise RuntimeError("Database not initialized")
        
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """获取同步数据库会话（需要手动管理）"""
        if not self._session_factory:
            raise RuntimeError("Database not initialized")
        return self._session_factory()
    
    def close(self) -> None:
        """关闭数据库连接"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None


# 全局数据库管理器实例
db_manager: Optional[DatabaseManager] = None


def init_database(config: DatabaseConfig) -> None:
    """初始化数据库"""
    global db_manager
    db_manager = DatabaseManager(config)
    db_manager.initialize()


def get_db_session() -> Generator[Session, None, None]:
    """获取数据库会话（FastAPI依赖注入用）"""
    if not db_manager:
        raise RuntimeError("Database not initialized")
    
    session = db_manager.get_session_sync()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Session:
    """获取数据库会话（同步使用）"""
    if not db_manager:
        raise RuntimeError("Database not initialized")
    return db_manager.get_session_sync()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """数据库会话上下文管理器"""
    if not db_manager:
        raise RuntimeError("Database not initialized")
    
    with db_manager.get_session() as session:
        yield session


def close_database() -> None:
    """关闭数据库连接"""
    global db_manager
    if db_manager:
        db_manager.close()
        db_manager = None
