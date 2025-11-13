#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建admin用户
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def create_admin_user():
    """创建admin用户"""
    print("🔍 创建admin用户...")
    
    try:
        # 导入必要的模块
        from server.config import config_manager
        from server.app import database
        from server.app.models.user import User, UserRoleEnum, UserStatusEnum
        from server.app.services.user_service import UserService
        from werkzeug.security import generate_password_hash
        
        # 初始化数据库
        db_config = config_manager.config.database
        if database.db_manager is None:
            database.init_database(db_config)
            print("✅ 数据库已初始化")
        
        with database.db_session() as session:
            # 检查是否已存在admin用户
            existing_admin = session.query(User).filter(
                (User.username == "admin") | (User.email == "admin@example.com")
            ).first()
            
            if existing_admin:
                print(f"⚠️ admin用户已存在: {existing_admin.username} ({existing_admin.email})")
                return existing_admin
            
            # 创建admin用户
            admin_user = User(
                username="admin",
                email="admin@example.com",
                nickname="管理员",
                role=UserRoleEnum.SUPER_ADMIN,
                status=UserStatusEnum.ACTIVE,
                email_verified=True,
                failed_login_count=0
            )
            # 设置密码，这会自动生成salt
            admin_user.set_password("admin123")
            
            session.add(admin_user)
            session.commit()
            
            print(f"✅ admin用户创建成功:")
            print(f"   - 用户名: {admin_user.username}")
            print(f"   - 邮箱: {admin_user.email}")
            print(f"   - 角色: {admin_user.role}")
            print(f"   - 状态: {admin_user.status}")
            print(f"   - ID: {admin_user.id}")
            
            return admin_user
            
    except Exception as e:
        print(f"❌ 创建admin用户失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_admin_login():
    """测试admin用户登录"""
    print("\n🔍 测试admin用户登录...")
    
    try:
        from server.app.services.user_service import UserService
        
        # 测试认证
        result = UserService.authenticate_user("admin", "admin123")
        
        if result:
            print(f"✅ admin用户认证成功:")
            print(f"   - 用户ID: {result.id}")
            print(f"   - 用户名: {result.username}")
            print(f"   - 邮箱: {result.email}")
            print(f"   - 角色: {result.role}")
        else:
            print("❌ admin用户认证失败")
            
        return result
        
    except Exception as e:
        print(f"❌ 测试admin登录失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🚀 开始创建admin用户...")
    
    # 创建admin用户
    admin_user = create_admin_user()
    
    if admin_user:
        # 测试登录
        test_admin_login()
    
    print("\n✅ 完成")