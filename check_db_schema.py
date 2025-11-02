"""检查数据库表结构"""
from server.app.database import DatabaseManager
from server.config import DatabaseConfig
from sqlalchemy import text

config = DatabaseConfig()
dm = DatabaseManager(config)
dm.initialize()

with dm.get_session() as db:
    if config.db_type == "mysql":
        result = db.execute(text("""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = :db_name
              AND TABLE_NAME = 'live_review_reports'
            ORDER BY ORDINAL_POSITION
        """), {"db_name": config.mysql_database})
    else:
        result = db.execute(text("PRAGMA table_info(live_review_reports)"))
    
    print("\n📊 live_review_reports 表结构：")
    print("=" * 60)
    for row in result:
        print(row)
    print("=" * 60)
