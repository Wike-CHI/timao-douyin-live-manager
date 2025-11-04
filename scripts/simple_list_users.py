#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单查询数据库中的所有用户账户信息
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 直接从.env文件读取配置
def load_env_config():
    config = {}
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config

def list_users_from_mysql():
    """从MySQL数据库列出所有用户"""
    session = None
    try:
        # 导入必要的模块
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from server.app.models.user import User
        from server.app.models.base import Base
        
        # 从.env文件获取配置
        config = load_env_config()
        
        # MySQL配置
        mysql_host = config.get('MYSQL_HOST', 'localhost')
        mysql_port = config.get('MYSQL_PORT', '3306')
        mysql_user = config.get('MYSQL_USER', 'timao')
        mysql_password = config.get('MYSQL_PASSWORD', 'timao-20251030')
        mysql_database = config.get('MYSQL_DATABASE', 'timao_live')
        
        # 创建数据库引擎
        connection_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
        engine = create_engine(connection_url)
        
        # 创建会话
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print(f"正在从MySQL数据库 {mysql_user}@{mysql_host}:{mysql_port}/{mysql_database} 查询用户信息...")
        print("=" * 80)
        
        # 查询所有用户
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
        if session:
            try:
                session.close()
            except:
                pass

if __name__ == "__main__":
    list_users_from_mysql()