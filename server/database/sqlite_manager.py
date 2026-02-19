"""SQLite数据库管理器

提供SQLite数据库的统一管理，支持：
- 主数据库（用户、配置）
- AI专用数据库（向量记忆、风格画像）
- 按月分库的直播记录
"""
import logging
import os
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional, Dict, Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

__all__ = [
    "SQLiteDatabaseManager",
    "SQLiteConfig",
    "get_sqlite_manager",
    "close_sqlite",
]

# PRAGMA允许的值
ALLOWED_SYNCHRONOUS = {"OFF", "NORMAL", "FULL"}
ALLOWED_TEMP_STORE = {"FILE", "MEMORY"}


@dataclass
class SQLiteConfig:
    """SQLite配置"""
    data_dir: str = "data"

    # 性能优化参数
    cache_size: int = -64000  # 64MB缓存（负数表示KB）
    mmap_size: int = 268435456  # 256MB内存映射
    synchronous: str = "NORMAL"
    temp_store: str = "MEMORY"

    # 连接池（SQLite单连接模式）
    pool_size: int = 1
    max_overflow: int = 0

    def __post_init__(self):
        """验证配置值"""
        if self.synchronous.upper() not in ALLOWED_SYNCHRONOUS:
            raise ValueError(f"synchronous must be one of {ALLOWED_SYNCHRONOUS}")
        if self.temp_store.upper() not in ALLOWED_TEMP_STORE:
            raise ValueError(f"temp_store must be one of {ALLOWED_TEMP_STORE}")


class SQLiteDatabaseManager:
    """SQLite数据库管理器"""

    def __init__(self, config: Optional[SQLiteConfig] = None):
        self.config = config or SQLiteConfig()
        self.data_dir = Path(self.config.data_dir)

        # 主数据库
        self._main_engine: Optional[Engine] = None
        self._main_session_factory: Optional[sessionmaker] = None

        # AI数据库缓存
        self._ai_engines: Dict[str, Engine] = {}

        # 直播会话数据库缓存
        self._session_engines: Dict[str, Engine] = {}

    def initialize(self) -> None:
        """初始化数据库管理器"""
        # 创建数据目录结构
        self._ensure_directories()

        # 初始化主数据库
        self._init_main_database()

        logger.info("✅ SQLite数据库管理器初始化完成")

    def _ensure_directories(self) -> None:
        """确保目录结构存在"""
        dirs = [
            self.data_dir,
            self.data_dir / "ai",
            self.data_dir / "sessions",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def _init_main_database(self) -> None:
        """初始化主数据库"""
        db_path = self.data_dir / "timao.db"
        db_url = f"sqlite:///{db_path}"

        self._main_engine = create_engine(
            db_url,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            echo=False,
        )

        # 应用SQLite优化
        self._apply_pragma(self._main_engine)

        self._main_session_factory = sessionmaker(
            bind=self._main_engine,
            autocommit=False,
            autoflush=False,
        )

        # 确保数据库文件创建（SQLite延迟创建）
        with self._main_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()

    def _apply_pragma(self, engine: Engine) -> None:
        """应用SQLite优化PRAGMA"""
        @event.listens_for(engine, "connect")
        def set_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute(f"PRAGMA synchronous={self.config.synchronous}")
            cursor.execute(f"PRAGMA cache_size={self.config.cache_size}")
            cursor.execute(f"PRAGMA temp_store={self.config.temp_store}")
            cursor.execute(f"PRAGMA mmap_size={self.config.mmap_size}")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    def get_ai_database(self, name: str) -> Engine:
        """获取AI专用数据库引擎

        Args:
            name: 数据库名称（如 memory_vectors, style_profiles）

        Returns:
            SQLAlchemy引擎
        """
        if name in self._ai_engines:
            return self._ai_engines[name]

        db_path = self.data_dir / "ai" / f"{name}.db"
        db_url = f"sqlite:///{db_path}"

        engine = create_engine(db_url, echo=False)
        self._apply_pragma(engine)

        # 确保数据库文件创建（SQLite延迟创建）
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()

        self._ai_engines[name] = engine
        logger.info(f"✅ AI数据库已打开: {name}")

        return engine

    def get_session_database(self, year: int, month: int) -> Engine:
        """获取按月分库的直播数据库

        Args:
            year: 年份
            month: 月份

        Returns:
            SQLAlchemy引擎
        """
        db_key = f"{year:04d}-{month:02d}"

        if db_key in self._session_engines:
            return self._session_engines[db_key]

        db_path = self.data_dir / "sessions" / f"live_{db_key}.db"
        db_url = f"sqlite:///{db_path}"

        engine = create_engine(db_url, echo=False)
        self._apply_pragma(engine)

        # 确保数据库文件创建（SQLite延迟创建）
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()

        self._session_engines[db_key] = engine
        logger.info(f"✅ 直播会话数据库已打开: live_{db_key}")

        return engine

    def get_current_session_database(self) -> Engine:
        """获取当前月份的直播数据库"""
        now = datetime.now()
        return self.get_session_database(now.year, now.month)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取主数据库会话"""
        if not self._main_session_factory:
            raise RuntimeError("Database not initialized")

        session = self._main_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session_sync(self) -> Session:
        """获取同步数据库会话"""
        if not self._main_session_factory:
            raise RuntimeError("Database not initialized")
        return self._main_session_factory()

    def close(self) -> None:
        """关闭所有数据库连接"""
        if self._main_engine:
            self._main_engine.dispose()

        for engine in self._ai_engines.values():
            engine.dispose()

        for engine in self._session_engines.values():
            engine.dispose()

        self._main_engine = None
        self._main_session_factory = None
        self._ai_engines.clear()
        self._session_engines.clear()

        logger.info("✅ SQLite数据库连接已关闭")


# 全局实例（线程安全）
_db_manager: Optional[SQLiteDatabaseManager] = None
_db_lock = threading.Lock()


def get_sqlite_manager() -> SQLiteDatabaseManager:
    """获取SQLite管理器实例（线程安全）"""
    global _db_manager
    if _db_manager is None:
        with _db_lock:
            if _db_manager is None:  # Double-check locking
                _db_manager = SQLiteDatabaseManager()
                _db_manager.initialize()
    return _db_manager


def close_sqlite() -> None:
    """关闭SQLite连接"""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None
