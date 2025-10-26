# -*- coding: utf-8 -*-
"""
数据库迁移：添加直播和团队功能

运行方式：
python -m server.app.scripts.migrate_add_live_team
"""

from sqlalchemy import create_engine, text
from server.config import config_manager
from server.app.database import DatabaseManager
from server.app.models import Base, LiveSession, Team, TeamMember
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """执行数据库迁移"""
    try:
        # 初始化数据库管理器
        db_config = config_manager.config.database
        db_manager = DatabaseManager(db_config)
        
        logger.info("开始数据库迁移...")
        
        # 创建所有表（如果不存在）
        Base.metadata.create_all(db_manager._engine)
        
        logger.info("✅ 数据库迁移完成！")
        logger.info("新增表：")
        logger.info("  - live_sessions (直播会话)")
        logger.info("  - teams (团队)")
        logger.info("  - team_members (团队成员)")
        logger.info("")
        logger.info("User 表新增字段：")
        logger.info("  - douyin_user_id, douyin_nickname, douyin_avatar")
        logger.info("  - douyin_room_id, douyin_cookies")
        logger.info("  - streamer_verified, streamer_level, streamer_followers")
        logger.info("  - live_settings (JSON)")
        logger.info("  - ai_quota_monthly, ai_quota_used, ai_quota_reset_at, ai_unlimited")
        
    except Exception as e:
        logger.error(f"❌ 数据库迁移失败: {e}")
        raise


if __name__ == "__main__":
    migrate()
