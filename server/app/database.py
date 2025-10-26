# -*- coding: utf-8 -*-
"""
数据库连接和会话管理
"""

import os
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from server.config import DatabaseConfig
from server.app.models import Base


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        
    def initialize(self) -> None:
        """初始化数据库连接"""
        # 根据数据库类型创建引擎
        if self.config.db_type == "mysql":
            self._init_mysql_engine()
        else:
            self._init_sqlite_engine()
        
        # 创建会话工厂
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False
        )
        
        # 创建所有表
        self.create_tables()
    
    def _init_mysql_engine(self) -> None:
        """初始化 MySQL 数据库引擎"""
        # 构建 MySQL 连接字符串
        connection_url = (
            f"mysql+pymysql://{self.config.mysql_user}:{self.config.mysql_password}"
            f"@{self.config.mysql_host}:{self.config.mysql_port}"
            f"/{self.config.mysql_database}?charset={self.config.mysql_charset}"
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
    
    with db_manager.get_session() as session:
        yield session


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