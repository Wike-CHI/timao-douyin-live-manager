#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户注册功能诊断脚本
直接测试用户注册功能，捕获详细错误信息
"""

import sys
import os
import traceback
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

def test_database_connection():
    """测试数据库连接"""
    print("\n" + "=" * 50)
    print("🔗 测试数据库连接")
    print("=" * 50)
    
    try:
        from server.config import config_manager
        from server.app.database import init_database, get_db_session
        
        print("初始化数据库...")
        init_database(config_manager.config.database)
        print("✅ 数据库初始化成功")
        
        print("测试数据库会话...")
        from server.app.database import db_session
        from sqlalchemy import text
        with db_session() as session:
            result = session.execute(text("SELECT 1")).fetchone()
            print(f"✅ 数据库连接测试成功: {result}")
            
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        traceback.print_exc()
        return False

def test_user_service_direct():
    """直接测试用户服务"""
    print("\n" + "=" * 50)
    print("👤 直接测试用户服务")
    print("=" * 50)
    
    try:
        from server.app.services.user_service import UserService
        from server.app.models.user import UserRoleEnum
        
        # 生成唯一的测试用户数据
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_username = f"testuser_{timestamp}"
        test_email = f"test_{timestamp}@example.com"
        
        print(f"创建测试用户: {test_username}")
        print(f"邮箱: {test_email}")
        
        user = UserService.create_user(
            username=test_username,
            email=test_email,
            password="testpassword123",
            nickname=f"Test User {timestamp}",
            role=UserRoleEnum.USER
        )
        
        print("✅ 用户创建成功!")
        print(f"用户ID: {user.id}")
        print(f"用户名: {user.username}")
        print(f"邮箱: {user.email}")
        print(f"昵称: {user.nickname}")
        print(f"角色: {user.role}")
        print(f"状态: {user.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ 用户服务测试失败: {e}")
        traceback.print_exc()
        return False

def test_registration_api():
    """测试注册API"""
    print("\n" + "=" * 50)
    print("🌐 测试注册API")
    print("=" * 50)
    
    try:
        import requests
        import json
        
        # 生成唯一的测试用户数据
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_data = {
            "username": f"apitest_{timestamp}",
            "email": f"apitest_{timestamp}@example.com",
            "password": "testpassword123",
            "nickname": f"API Test User {timestamp}"
        }
        
        print(f"发送注册请求: {test_data['username']}")
        
        response = requests.post(
            "http://127.0.0.1:8000/api/auth/register",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        except:
            print(f"响应文本: {response.text}")
        
        if response.status_code == 201:
            print("✅ API注册测试成功!")
            return True
        else:
            print(f"❌ API注册测试失败，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        traceback.print_exc()
        return False

def test_redis_connection():
    """测试Redis连接"""
    print("\n" + "=" * 50)
    print("🔴 测试Redis连接")
    print("=" * 50)
    
    try:
        from server.utils.redis_manager import init_redis, get_redis
        from server.config import get_config
        
        # 获取配置并初始化Redis
        config = get_config()
        redis_manager = init_redis(config.redis)
        
        if redis_manager and redis_manager.is_enabled():
            # 测试Redis连接
            result = redis_manager.ping()
            print(f"✅ Redis连接测试成功: {result}")
            
            # 测试基本操作
            set_result = redis_manager.set("test_key", "test_value", ttl=60)
            print(f"✅ Redis设置测试: {'成功' if set_result else '失败'}")
            
            value = redis_manager.get("test_key")
            print(f"✅ Redis读取测试成功: {value}")
            
            # 清理测试数据
            redis_manager.delete("test_key")
            
            return True
        else:
            print("⚠️ Redis未启用或连接失败")
            return False
            
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        traceback.print_exc()
        return False

def test_config_loading():
    """测试配置加载"""
    print("\n" + "=" * 50)
    print("⚙️ 测试配置加载")
    print("=" * 50)
    
    try:
        from server.config import config_manager
        
        config = config_manager.config
        print("✅ 配置加载成功")
        
        print(f"数据库配置: {config.database}")
        print(f"Redis配置: {config.redis}")
        print(f"服务器配置: {config.server}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 开始用户注册功能诊断")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # 测试配置加载
    results['config'] = test_config_loading()
    
    # 测试数据库连接
    results['database'] = test_database_connection()
    
    # 测试Redis连接
    results['redis'] = test_redis_connection()
    
    # 如果数据库连接成功，测试用户服务
    if results['database']:
        results['user_service'] = test_user_service_direct()
    else:
        results['user_service'] = False
        print("⚠️ 跳过用户服务测试（数据库连接失败）")
    
    # 测试注册API
    results['api'] = test_registration_api()
    
    # 总结结果
    print("\n" + "=" * 50)
    print("📊 诊断结果总结")
    print("=" * 50)
    
    for test_name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 所有测试通过！注册功能正常")
    else:
        print("\n⚠️ 部分测试失败，需要进一步调试")
    
    print("\n🏁 诊断完成!")

if __name__ == "__main__":
    main()