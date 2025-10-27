#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版注册测试脚本
用于直接调用后端服务而不是通过HTTP API
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_direct_user_creation():
    """直接测试用户创建"""
    print("=" * 60)
    print("🔧 直接用户创建测试")
    print("=" * 60)
    
    try:
        # 初始化数据库
        from server.config import config_manager
        from server.app.database import init_database, db_session
        from server.app.services.user_service import UserService
        from server.app.models.user import UserRoleEnum
        
        print("初始化数据库...")
        init_database(config_manager.config.database)
        print("✅ 数据库初始化成功")
        
        # 测试直接创建用户
        print("\n创建测试用户...")
        user = UserService.create_user(
            username="WIke",
            email="3132812664@qq.com",
            password="987987123",
            nickname="WIke",
            role=UserRoleEnum.USER
        )
        
        print("✅ 用户创建成功!")
        print(f"用户ID: {user.id}")
        print(f"用户名: {user.username}")
        print(f"邮箱: {user.email}")
        print(f"昵称: {user.nickname}")
        print(f"角色: {user.role.value}")
        print(f"状态: {user.status.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 用户创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_session():
    """测试数据库会话"""
    print("\n" + "=" * 60)
    print("🔌 数据库会话测试")
    print("=" * 60)
    
    try:
        from server.app.database import db_session
        
        with db_session() as session:
            print("✅ 数据库会话获取成功")
            # 执行简单查询
            from sqlalchemy import text
            result = session.execute(text("SELECT 1")).fetchone()
            print(f"✅ 简单查询成功: {result[0] if result else 'N/A'}")
            return True
            
    except Exception as e:
        print(f"❌ 数据库会话测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 开始简化版认证测试")
    
    # 测试数据库会话
    session_ok = test_database_session()
    
    if session_ok:
        # 测试直接用户创建
        test_direct_user_creation()
    
    print("\n🏁 测试完成!")

if __name__ == "__main__":
    main()