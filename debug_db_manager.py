#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试数据库管理器状态
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def debug_db_manager():
    """调试数据库管理器状态"""
    print("🔍 调试数据库管理器状态...")
    
    try:
        # 导入配置管理器
        from server.config import config_manager
        print("✅ 配置管理器导入成功")
        
        # 获取数据库配置
        db_config = config_manager.config.database
        print(f"📋 数据库配置: {db_config}")
        
        # 导入数据库模块
        from server.app import database
        print("✅ 数据库模块导入成功")
        
        # 检查全局db_manager状态
        print(f"🔍 全局db_manager状态: {database.db_manager}")
        
        if database.db_manager is None:
            print("⚠️ db_manager未初始化，尝试手动初始化...")
            database.init_database(db_config)
            print(f"✅ 手动初始化后db_manager状态: {database.db_manager}")
        
        # 测试会话创建
        print("🔍 测试数据库会话创建...")
        try:
            with database.db_session() as session:
                print("✅ 数据库会话创建成功")
                
                # 测试简单查询
                result = session.execute("SELECT 1 as test").fetchone()
                print(f"✅ 测试查询结果: {result}")
                
        except Exception as e:
            print(f"❌ 数据库会话创建失败: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ 调试过程出错: {e}")
        import traceback
        traceback.print_exc()

def test_user_service():
    """测试用户服务"""
    print("\n🔍 测试用户服务...")
    
    try:
        from server.app.services.user_service import UserService
        print("✅ 用户服务导入成功")
        
        # 测试authenticate_user方法
        print("🔍 测试用户认证...")
        try:
            result = UserService.authenticate_user("admin", "admin123")
            print(f"✅ 用户认证结果: {result}")
        except Exception as e:
            print(f"❌ 用户认证失败: {e}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ 用户服务测试失败: {e}")
        import traceback
        traceback.print_exc()

def check_user_table():
    """检查用户表"""
    print("\n🔍 检查用户表...")
    
    try:
        from server.app import database
        from server.app.models.user import User
        
        with database.db_session() as session:
            # 查询用户数量
            user_count = session.query(User).count()
            print(f"📊 用户表中的用户数量: {user_count}")
            
            # 查询admin用户
            admin_user = session.query(User).filter(
                (User.username == "admin") | (User.email == "admin")
            ).first()
            
            if admin_user:
                print(f"✅ 找到admin用户: {admin_user.username} ({admin_user.email})")
                print(f"   - ID: {admin_user.id}")
                print(f"   - 状态: {admin_user.status}")
                print(f"   - 角色: {admin_user.role}")
                print(f"   - 失败次数: {admin_user.failed_login_attempts}")
                print(f"   - 锁定状态: {admin_user.is_locked}")
            else:
                print("⚠️ 未找到admin用户")
                
                # 列出所有用户
                users = session.query(User).limit(5).all()
                print(f"📋 前5个用户:")
                for user in users:
                    print(f"   - {user.username} ({user.email})")
                    
    except Exception as e:
        print(f"❌ 检查用户表失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 开始数据库管理器调试...")
    
    # 调试数据库管理器
    debug_db_manager()
    
    # 检查用户表
    check_user_table()
    
    # 测试用户服务
    test_user_service()
    
    print("\n✅ 调试完成")