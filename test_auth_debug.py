#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
登录API调试脚本
"""

import sys
import os
import traceback

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_database_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("🗄️ 测试数据库连接")
    print("=" * 60)
    
    try:
        from server.config import config_manager
        from server.app.database import init_database, db_session
        from sqlalchemy import text
        
        print("初始化数据库...")
        init_database(config_manager.config.database)
        print("✅ 数据库初始化成功")
        
        print("测试数据库查询...")
        with db_session() as session:
            result = session.execute(text("SELECT 1")).fetchone()
            print(f"✅ 数据库查询测试成功: {result[0] if result else 'N/A'}")
            
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        traceback.print_exc()
        return False

def test_user_authentication():
    """测试用户认证"""
    print("\n" + "=" * 60)
    print("🔐 测试用户认证")
    print("=" * 60)
    
    try:
        from server.app.services.user_service import UserService
        
        print("测试用户认证服务...")
        
        # 尝试认证默认管理员账户
        test_credentials = [
            ("admin", "admin123"),
            ("admin", "admin"),
            ("test", "test123"),
        ]
        
        for username, password in test_credentials:
            try:
                print(f"尝试认证用户: {username}")
                user = UserService.authenticate_user(username, password, "127.0.0.1")
                if user:
                    print(f"✅ 用户认证成功: {user.username}")
                    return True
                else:
                    print(f"❌ 用户认证失败: {username}")
            except Exception as e:
                print(f"❌ 认证过程出错: {e}")
                
        return False
        
    except Exception as e:
        print(f"❌ 用户认证测试失败: {e}")
        traceback.print_exc()
        return False

def test_user_creation():
    """测试创建测试用户"""
    print("\n" + "=" * 60)
    print("👤 测试创建用户")
    print("=" * 60)
    
    try:
        from server.app.services.user_service import UserService
        from server.app.models.user import UserRoleEnum
        
        # 检查是否已存在admin用户
        existing_user = UserService.get_user_by_username("admin")
        if existing_user:
            print(f"✅ 用户 'admin' 已存在: {existing_user.username}")
            return True
        
        # 创建测试用户
        print("创建测试用户...")
        user = UserService.create_user(
            username="admin",
            email="admin@test.com",
            password="admin123",
            role=UserRoleEnum.ADMIN
        )
        
        print(f"✅ 用户创建成功: {user.username}")
        return True
        
    except Exception as e:
        print(f"❌ 用户创建失败: {e}")
        traceback.print_exc()
        return False

def test_login_api():
    """测试登录API"""
    print("\n" + "=" * 60)
    print("🌐 测试登录API")
    print("=" * 60)
    
    try:
        import requests
        
        login_url = "http://127.0.0.1:10090/api/auth/login"
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        print(f"发送登录请求到: {login_url}")
        response = requests.post(login_url, json=login_data, timeout=10)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 登录API测试成功")
            return True
        else:
            print(f"❌ 登录API返回错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 登录API测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 开始登录API调试")
    
    # 测试数据库连接
    if not test_database_connection():
        print("❌ 数据库连接失败，停止测试")
        return
    
    # 测试用户创建
    if not test_user_creation():
        print("❌ 用户创建失败，停止测试")
        return
    
    # 测试用户认证
    if not test_user_authentication():
        print("❌ 用户认证失败，停止测试")
        return
    
    # 测试登录API
    test_login_api()
    
    print("\n🎉 调试测试完成!")

if __name__ == "__main__":
    main()