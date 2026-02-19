"""AI数据库Schema定义

定义AI功能所需的数据库表结构：
- memory_vectors: 向量记忆存储
- style_profiles: 风格画像
- memory_summaries: 记忆摘要
- ai_usage_logs: AI调用日志
"""
import logging
from typing import List
from sqlalchemy import text

from server.database.sqlite_manager import SQLiteDatabaseManager

logger = logging.getLogger(__name__)


def _split_sql_statements(sql: str) -> List[str]:
    """将SQL字符串分割成独立的语句

    Args:
        sql: 包含多个SQL语句的字符串

    Returns:
        分割后的SQL语句列表
    """
    statements = []
    for statement in sql.strip().split(";"):
        statement = statement.strip()
        if statement:
            statements.append(statement)
    return statements


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
)
"""

MEMORY_VECTORS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_memory_anchor ON memory_vectors(anchor_id)",
    "CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_vectors(memory_type)",
    "CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory_vectors(importance_score)",
]

# 风格画像表DDL
STYLE_PROFILES_SCHEMA = """
CREATE TABLE IF NOT EXISTS style_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    anchor_id TEXT NOT NULL UNIQUE,
    profile_data TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

STYLE_PROFILES_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_style_anchor ON style_profiles(anchor_id)",
]

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
)
"""

MEMORY_SUMMARIES_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_summary_anchor ON memory_summaries(anchor_id)",
]

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
)
"""

AI_USAGE_LOGS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_usage_provider ON ai_usage_logs(provider)",
    "CREATE INDEX IF NOT EXISTS idx_usage_function ON ai_usage_logs(function)",
    "CREATE INDEX IF NOT EXISTS idx_usage_created ON ai_usage_logs(created_at)",
]


def init_ai_tables(manager: SQLiteDatabaseManager) -> None:
    """初始化AI相关数据库表

    Args:
        manager: SQLite数据库管理器
    """
    # 初始化向量记忆表
    memory_engine = manager.get_ai_database("memory_vectors")
    with memory_engine.connect() as conn:
        conn.execute(text(MEMORY_VECTORS_SCHEMA))
        conn.commit()
        # 创建索引
        for index_sql in MEMORY_VECTORS_INDEXES:
            conn.execute(text(index_sql))
        conn.commit()
        # 创建记忆摘要表（在同一数据库中）
        conn.execute(text(MEMORY_SUMMARIES_SCHEMA))
        conn.commit()
        for index_sql in MEMORY_SUMMARIES_INDEXES:
            conn.execute(text(index_sql))
        conn.commit()
    logger.info("✅ 向量记忆表已初始化")

    # 初始化风格画像表
    style_engine = manager.get_ai_database("style_profiles")
    with style_engine.connect() as conn:
        conn.execute(text(STYLE_PROFILES_SCHEMA))
        conn.commit()
        for index_sql in STYLE_PROFILES_INDEXES:
            conn.execute(text(index_sql))
        conn.commit()
    logger.info("✅ 风格画像表已初始化")

    # 初始化AI使用日志表
    logs_engine = manager.get_ai_database("ai_usage_logs")
    with logs_engine.connect() as conn:
        conn.execute(text(AI_USAGE_LOGS_SCHEMA))
        conn.commit()
        for index_sql in AI_USAGE_LOGS_INDEXES:
            conn.execute(text(index_sql))
        conn.commit()
    logger.info("✅ AI使用日志表已初始化")


__all__ = [
    "init_ai_tables",
    "MEMORY_VECTORS_SCHEMA",
    "MEMORY_VECTORS_INDEXES",
    "STYLE_PROFILES_SCHEMA",
    "STYLE_PROFILES_INDEXES",
    "MEMORY_SUMMARIES_SCHEMA",
    "MEMORY_SUMMARIES_INDEXES",
    "AI_USAGE_LOGS_SCHEMA",
    "AI_USAGE_LOGS_INDEXES",
]
