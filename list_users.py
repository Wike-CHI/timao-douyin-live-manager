#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询数据库中的所有用户账户信息
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server.config import DatabaseConfig
from server.app.database import DatabaseManager
from server.app.models.user import User
from server.app.database import db_session


def list_all_users():
    """列出所有用户"""
    db_manager = None
    try:
        # 初始化数据库连接
        db_config = DatabaseConfig()
        
        # 打印数据库配置信息用于调试
        print(f"数据库类型: {db_config.db_type}")
        print(f"MySQL用户: {db_config.mysql_user}")
        print(f"MySQL密码: {'*' * len(db_config.mysql_password) if db_config.mysql_password else '空'}")
        print(f"MySQL主机: {db_config.mysql_host}")
        print(f"MySQL端口: {db_config.mysql_port}")
        print(f"MySQL数据库: {db_config.mysql_database}")
        print(f"SQLite路径: {db_config.sqlite_path}")
        print("-" * 50)
        
        # 如果MySQL连接失败，尝试使用SQLite
        try:
            db_manager = DatabaseManager(db_config)
            db_manager.initialize()
            print("✅ MySQL数据库连接成功")
        except Exception as e:
            print(f"⚠️  MySQL连接失败: {e}")
            print("🔄 尝试使用SQLite数据库...")
            # 切换到SQLite
            db_config.db_type = "sqlite"
            db_manager = DatabaseManager(db_config)
            db_manager.initialize()
            print("✅ SQLite数据库连接成功")
        
        print("正在查询数据库中的所有用户账户...")
        print("=" * 80)
        
        # 查询所有用户
        with db_session() as session:
            users = session.query(User).all()
            
            if not users:
                print("数据库中没有找到任何用户账户。")
                return
            
            print(f"共找到 {len(users)} 个用户账户：")
            print("-" * 80)
            
            # 输出用户信息表头
            print(f"{'ID':<5} {'用户名':<15} {'邮箱':<25} {'角色':<10} {'状态':<10} {'注册时间':<20}")
            print("-" * 80)
            
            # 输出每个用户的信息
            for user in users:
                # 格式化用户角色
                role_str = str(user.role.value) if user.role is not None else "N/A"
                
                # 格式化用户状态
                status_str = str(user.status.value) if user.status is not None else "N/A"
                
                # 格式化注册时间
                created_at_str = user.created_at.strftime("%Y-%m-%d %H:%M") if user.created_at else "N/A"
                
                print(f"{user.id:<5} {user.username:<15} {user.email:<25} {role_str:<10} {status_str:<10} {created_at_str:<20}")
            
            print("-" * 80)
            print(f"总计: {len(users)} 个用户")
            
    except Exception as e:
        print(f"查询用户时发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭数据库连接
        if db_manager:
            try:
                db_manager.close()
            except:
                pass


if __name__ == "__main__":
    list_all_users()