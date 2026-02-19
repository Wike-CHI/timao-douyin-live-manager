# SQLite迁移实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将数据库从MySQL迁移到SQLite，简化Electron桌面应用部署

**Architecture:** 保持SQLAlchemy ORM层，底层切换到SQLite。使用WAL模式优化性能，按月分库管理直播记录。

**Tech Stack:** Python, SQLite, SQLAlchemy, ChromaDB

---

## Task 1: 创建SQLite数据库管理器

**Files:**
- Create: `server/database/sqlite_manager.py`
- Create: `tests/database/test_sqlite_manager.py`

**Step 1: 编写SQLite管理器测试**

创建 `tests/database/test_sqlite_manager.py`：

```python
"""测试SQLite数据库管理器"""
import pytest
import os
import tempfile
from pathlib import Path

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
            with manager.get_session_sync() as session:
                result = session.execute("PRAGMA journal_mode").fetchone()
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
```

**Step 2: 运行测试确认失败**

Run: `pytest tests/database/test_sqlite_manager.py -v`
Expected: FAIL - ModuleNotFoundError

**Step 3: 实现SQLite数据库管理器**

创建 `server/database/sqlite_manager.py`：

```python
"""SQLite数据库管理器

提供SQLite数据库的统一管理，支持：
- 主数据库（用户、配置）
- AI专用数据库（向量记忆、风格画像）
- 按月分库的直播记录
"""
import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Generator, Optional, Dict, Any

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)


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


# 全局实例
_db_manager: Optional[SQLiteDatabaseManager] = None


def get_sqlite_manager() -> SQLiteDatabaseManager:
    """获取SQLite管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = SQLiteDatabaseManager()
        _db_manager.initialize()
    return _db_manager


def close_sqlite() -> None:
    """关闭SQLite连接"""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None
```

**Step 4: 运行测试确认通过**

Run: `pytest tests/database/test_sqlite_manager.py -v`
Expected: PASS

**Step 5: 提交**

```bash
git add server/database/sqlite_manager.py tests/database/test_sqlite_manager.py
git commit -m "feat: add SQLite database manager with WAL mode"
```

---

## Task 2: 创建AI专用数据库表

**Files:**
- Create: `server/database/ai_schema.py`
- Create: `tests/database/test_ai_schema.py`

**Step 1: 编写AI Schema测试**

创建 `tests/database/test_ai_schema.py`：

```python
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

            manager.close()

    def test_init_style_profiles_table(self):
        """测试初始化风格画像表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()

            init_ai_tables(manager)

            engine = manager.get_ai_database("style_profiles")
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='style_profiles'")
                ).fetchone()
                assert result is not None

            manager.close()

    def test_init_ai_usage_logs_table(self):
        """测试初始化AI使用日志表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SQLiteConfig(data_dir=tmpdir)
            manager = SQLiteDatabaseManager(config)
            manager.initialize()

            init_ai_tables(manager)

            engine = manager.get_ai_database("ai_usage_logs")
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_usage_logs'")
                ).fetchone()
                assert result is not None

            manager.close()
```

**Step 2: 实现AI Schema**

创建 `server/database/ai_schema.py`：

```python
"""AI数据库Schema定义

定义AI功能所需的数据库表结构：
- memory_vectors: 向量记忆存储
- style_profiles: 风格画像
- memory_summaries: 记忆摘要
- ai_usage_logs: AI调用日志
"""
import logging
from sqlalchemy import text

from server.database.sqlite_manager import SQLiteDatabaseManager

logger = logging.getLogger(__name__)


# 向量记忆表DDL
MEMORY_VECTORS_SCHEMA = """
CREATE TABLE IF NOT EXISTS memory_vectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anchor_id TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding BLOB,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    importance_score REAL DEFAULT 0.5
);

CREATE INDEX IF NOT EXISTS idx_memory_anchor ON memory_vectors(anchor_id);
CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_vectors(memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory_vectors(importance_score);
"""

# 风格画像表DDL
STYLE_PROFILES_SCHEMA = """
CREATE TABLE IF NOT EXISTS style_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anchor_id TEXT NOT NULL UNIQUE,
    profile_data TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_style_anchor ON style_profiles(anchor_id);
"""

# 记忆摘要表DDL
MEMORY_SUMMARIES_SCHEMA = """
CREATE TABLE IF NOT EXISTS memory_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anchor_id TEXT NOT NULL,
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    summary_text TEXT,
    key_insights TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_summary_anchor ON memory_summaries(anchor_id);
"""

# AI使用日志表DDL
AI_USAGE_LOGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS ai_usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    function TEXT NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    cost REAL,
    duration_ms REAL,
    success INTEGER DEFAULT 1,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_usage_provider ON ai_usage_logs(provider);
CREATE INDEX IF NOT EXISTS idx_usage_function ON ai_usage_logs(function);
CREATE INDEX IF NOT EXISTS idx_usage_created ON ai_usage_logs(created_at);
"""


def init_ai_tables(manager: SQLiteDatabaseManager) -> None:
    """初始化AI相关数据库表

    Args:
        manager: SQLite数据库管理器
    """
    # 初始化向量记忆表
    memory_engine = manager.get_ai_database("memory_vectors")
    with memory_engine.connect() as conn:
        conn.execute(text(MEMORY_VECTORS_SCHEMA))
        conn.execute(text(MEMORY_SUMMARIES_SCHEMA))
        conn.commit()
    logger.info("✅ 向量记忆表已初始化")

    # 初始化风格画像表
    style_engine = manager.get_ai_database("style_profiles")
    with style_engine.connect() as conn:
        conn.execute(text(STYLE_PROFILES_SCHEMA))
        conn.commit()
    logger.info("✅ 风格画像表已初始化")

    # 初始化AI使用日志表
    logs_engine = manager.get_ai_database("ai_usage_logs")
    with logs_engine.connect() as conn:
        conn.execute(text(AI_USAGE_LOGS_SCHEMA))
        conn.commit()
    logger.info("✅ AI使用日志表已初始化")
```

**Step 3: 运行测试确认通过**

Run: `pytest tests/database/test_ai_schema.py -v`

**Step 4: 提交**

```bash
git add server/database/ai_schema.py tests/database/test_ai_schema.py
git commit -m "feat: add AI database schema definitions"
```

---

## Task 3: 创建数据库目录初始化脚本

**Files:**
- Create: `server/database/init_db.py`
- Modify: `server/database/__init__.py`

**Step 1: 创建数据库初始化脚本**

创建 `server/database/__init__.py`：

```python
"""数据库模块"""
from server.database.sqlite_manager import (
    SQLiteDatabaseManager,
    SQLiteConfig,
    get_sqlite_manager,
    close_sqlite,
)
from server.database.ai_schema import init_ai_tables

__all__ = [
    "SQLiteDatabaseManager",
    "SQLiteConfig",
    "get_sqlite_manager",
    "close_sqlite",
    "init_ai_tables",
]
```

创建 `server/database/init_db.py`：

```python
"""数据库初始化脚本

用法:
    python -m server.database.init_db
"""
import logging
from server.database import get_sqlite_manager, init_ai_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """初始化数据库"""
    logger.info("🚀 开始初始化SQLite数据库...")

    # 获取数据库管理器
    manager = get_sqlite_manager()
    logger.info("✅ 数据库管理器已初始化")

    # 初始化AI表
    init_ai_tables(manager)
    logger.info("✅ AI数据表已创建")

    logger.info("🎉 数据库初始化完成！")
    logger.info("   数据目录: data/")
    logger.info("   - data/timao.db (主数据库)")
    logger.info("   - data/ai/memory_vectors.db (向量记忆)")
    logger.info("   - data/ai/style_profiles.db (风格画像)")
    logger.info("   - data/ai/ai_usage_logs.db (使用日志)")


if __name__ == "__main__":
    main()
```

**Step 2: 测试初始化脚本**

Run: `python -m server.database.init_db`

**Step 3: 提交**

```bash
git add server/database/__init__.py server/database/init_db.py
git commit -m "feat: add database initialization script"
```

---

## Task 4: 更新DatabaseManager支持SQLite

**Files:**
- Modify: `server/app/database.py`
- Modify: `server/config.py`

**Step 1: 更新配置类**

在 `server/config.py` 中修改 `DatabaseConfig`：

```python
@dataclass
class DatabaseConfig:
    """数据库配置"""
    # 数据库类型
    db_type: str = "sqlite"  # 支持 'mysql' 或 'sqlite'

    # SQLite配置
    sqlite_data_dir: str = "data"

    # MySQL配置（保留用于兼容）
    mysql_host: str = os.getenv("RDS_HOST", "localhost")
    # ... 其他MySQL配置
```

**Step 2: 更新DatabaseManager**

修改 `server/app/database.py`，添加SQLite支持：

```python
from server.database.sqlite_manager import SQLiteDatabaseManager, SQLiteConfig

class DatabaseManager:
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

        # SQLite管理器
        self._sqlite_manager: Optional[SQLiteDatabaseManager] = None

    def initialize(self) -> None:
        if self.config.db_type == "sqlite":
            self._init_sqlite()
        elif self.config.db_type == "mysql":
            self._init_mysql()
        else:
            raise ValueError(f"不支持的数据库类型: {self.config.db_type}")

    def _init_sqlite(self) -> None:
        """初始化SQLite数据库"""
        sqlite_config = SQLiteConfig(data_dir=self.config.sqlite_data_dir)
        self._sqlite_manager = SQLiteDatabaseManager(sqlite_config)
        self._sqlite_manager.initialize()

        self._engine = self._sqlite_manager._main_engine
        self._session_factory = self._sqlite_manager._main_session_factory

        logger.info("✅ 使用 SQLite 数据库: %s/timao.db", self.config.sqlite_data_dir)
```

**Step 3: 运行测试**

Run: `pytest tests/ -v`

**Step 4: 提交**

```bash
git add server/app/database.py server/config.py
git commit -m "feat: add SQLite support to DatabaseManager"
```

---

## Task 5: 更新.env.example和文档

**Files:**
- Modify: `.env.example`
- Create: `docs/database/SQLite-Migration-Guide.md`

**Step 1: 更新.env.example**

```bash
# 数据库配置
DB_TYPE=sqlite  # 可选: mysql, sqlite

# SQLite配置（当DB_TYPE=sqlite时使用）
SQLITE_DATA_DIR=data

# MySQL配置（当DB_TYPE=mysql时使用）
RDS_HOST=localhost
RDS_PORT=3306
# ...
```

**Step 2: 创建迁移指南**

创建 `docs/database/SQLite-Migration-Guide.md`：

```markdown
# SQLite迁移指南

## 概述

本指南帮助你从MySQL迁移到SQLite数据库。

## 为什么迁移到SQLite？

1. **简化部署**: 无需安装和配置MySQL服务
2. **降低资源占用**: 适合Electron桌面应用
3. **便于备份**: 单文件数据库，易于复制和备份
4. **性能优化**: WAL模式提供良好的并发性能

## 迁移步骤

### 1. 导出MySQL数据

```bash
mysqldump -u timao -p timao_live > backup.sql
```

### 2. 修改配置

编辑 `.env` 文件：

```bash
DB_TYPE=sqlite
SQLITE_DATA_DIR=data
```

### 3. 运行迁移

```bash
python -m server.database.init_db
```

### 4. 验证数据

```bash
sqlite3 data/timao.db ".tables"
```

## 数据目录结构

```
data/
├── timao.db                 # 主数据库
├── ai/
│   ├── memory_vectors.db    # 向量记忆
│   ├── style_profiles.db    # 风格画像
│   └── ai_usage_logs.db     # 使用日志
└── sessions/
    ├── live_2025-01.db      # 按月分库
    └── live_2025-02.db
```

## 常见问题

### Q: SQLite支持多少并发连接？

A: SQLite使用WAL模式，支持多读单写。对于桌面应用足够。

### Q: 如何备份数据库？

A: 直接复制 `data/` 目录即可。

### Q: 数据库文件最大多大？

A: 理论上支持140TB，实际使用中几十GB没有问题。
```

**Step 3: 提交**

```bash
git add .env.example docs/database/
git commit -m "docs: add SQLite migration guide"
```

---

## Task 6: 集成测试

**Files:**
- Create: `tests/database/test_sqlite_integration.py`

**Step 1: 创建集成测试**

```python
"""SQLite集成测试"""
import pytest
import tempfile
from pathlib import Path

from server.database import get_sqlite_manager, init_ai_tables, close_sqlite


class TestSQLiteIntegration:
    """SQLite集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. 初始化
            manager = get_sqlite_manager()
            manager.data_dir = Path(tmpdir)
            manager.initialize()

            # 2. 初始化AI表
            init_ai_tables(manager)

            # 3. 测试主数据库
            with manager.get_session() as session:
                session.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
                session.execute("INSERT INTO test VALUES (1)")

            # 4. 测试AI数据库
            ai_db = manager.get_ai_database("memory_vectors")
            assert ai_db is not None

            # 5. 测试会话数据库
            session_db = manager.get_current_session_database()
            assert session_db is not None

            # 6. 关闭
            manager.close()
```

**Step 2: 运行测试**

Run: `pytest tests/database/test_sqlite_integration.py -v`

**Step 3: 提交**

```bash
git add tests/database/test_sqlite_integration.py
git commit -m "test: add SQLite integration tests"
```

---

## 执行说明

1. **严格TDD流程**: 每个任务都遵循"写测试→失败→写代码→通过→提交"的循环
2. **频繁提交**: 每个小步骤完成后立即提交
3. **向后兼容**: 保持MySQL支持，通过配置切换
4. **创建目录**: 确保创建 `server/database/` 和 `tests/database/` 目录

**下一步：**

选择执行方式后，将逐步执行每个Task。
