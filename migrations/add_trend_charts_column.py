"""
添加 trend_charts 列到 live_review_reports 表

使用方法：
python migrations/add_trend_charts_column.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from server.app.database import DatabaseManager
from server.config import DatabaseConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """执行数据库迁移"""
    config = DatabaseConfig()
    db_manager = DatabaseManager(config)
    db_manager.initialize()
    
    # 使用 context manager 获取 session
    with db_manager.get_session() as db:
        try:
            # 检查列是否已存在 (针对 MySQL 和 SQLite)
            if config.db_type == "mysql":
                check_sql = text("""
                    SELECT COUNT(*) as count
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = :db_name
                      AND TABLE_NAME = 'live_review_reports'
                      AND COLUMN_NAME = 'trend_charts'
                """)
                result = db.execute(check_sql, {"db_name": config.mysql_database}).fetchone()
            else:
                # SQLite
                check_sql = text("""
                    SELECT COUNT(*) as count
                    FROM pragma_table_info('live_review_reports')
                    WHERE name = 'trend_charts'
                """)
                result = db.execute(check_sql).fetchone()
            
            if result and result[0] > 0:
                logger.info("✅ trend_charts 列已存在，无需迁移")
                return
            
            # 添加 trend_charts 列
            logger.info("📊 开始添加 trend_charts 列...")
            alter_sql = text("""
                ALTER TABLE live_review_reports
                ADD COLUMN trend_charts JSON
            """)
            
            db.execute(alter_sql)
            db.commit()
            
            logger.info("✅ 迁移完成！trend_charts 列已成功添加")
            
        except Exception as e:
            logger.error(f"❌ 迁移失败: {e}")
            db.rollback()
            raise


if __name__ == "__main__":
    migrate()
