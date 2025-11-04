# -*- coding: utf-8 -*-
"""
快速初始化数据库脚本

用于快速创建/更新数据库表结构，包括新增的复盘报告表。
适用于开发和测试环境。

使用方法：
python tools/init_database_quick.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from server.app.database import db_manager, init_database
from server.config import DatabaseConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    print("=" * 60)
    print("提猫直播助手 - 数据库初始化工具")
    print("=" * 60)
    print()
    
    # 加载数据库配置
    db_config = DatabaseConfig()
    
    print(f"数据库类型: {db_config.db_type}")
    if db_config.db_type == "mysql":
        print(f"MySQL 地址: {db_config.mysql_host}:{db_config.mysql_port}")
        print(f"MySQL 数据库: {db_config.mysql_database}")
        print(f"MySQL 用户: {db_config.mysql_user}")
    else:
        print(f"SQLite 路径: {db_config.sqlite_path}")
    
    print()
    print("正在初始化数据库...")
    
    try:
        # 初始化数据库
        init_database(db_config)
        
        # 创建所有表
        if db_manager:
            db_manager.create_tables()
            print()
            print("✅ 数据库表创建成功！")
            print()
            print("已创建的表包括：")
            print("  - users (用户表)")
            print("  - live_sessions (直播会话表)")
            print("  - live_review_reports (直播复盘报告表) [新增]")
            print("  - user_sessions (用户会话表)")
            print("  - subscription_plans (订阅计划表)")
            print("  - user_subscriptions (用户订阅表)")
            print("  - payment_records (支付记录表)")
            print("  - teams (团队表)")
            print("  - team_members (团队成员表)")
            print("  - permissions (权限表)")
            print("  - role_permissions (角色权限表)")
            print("  - audit_logs (审计日志表)")
            print()
            print("=" * 60)
            print("✅ 数据库初始化完成！")
            print("=" * 60)
        else:
            print("❌ 数据库管理器初始化失败")
            sys.exit(1)
            
    except Exception as e:
        print()
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
