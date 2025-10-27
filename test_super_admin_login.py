#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试超级管理员登录功能
验证超级管理员账号是否正常工作
"""

import requests
import json
from datetime import datetime


def test_super_admin_login():
    """测试超级管理员登录"""
    
    BASE_URL = "http://127.0.0.1:10090"
    
    print("=" * 60)
    print("🔐 超级管理员登录测试")
    print("=" * 60)
    
    # 超级管理员登录信息
    admin_credentials = {
        "username_or_email": "dev_admin",
        "password": "DevAdmin@2024!"
    }
    
    print(f"🌐 API服务器: {BASE_URL}")
    print(f"👤 用户名: {admin_credentials['username_or_email']}")
    print(f"🔑 密码: {admin_credentials['password']}")
    print("-" * 60)
    
    try:
        # 测试登录
        print("🚀 正在测试超级管理员登录...")
        
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=admin_credentials,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📊 登录响应状态码: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            print("✅ 超级管理员登录成功!")
            print(f"   访问令牌: {login_data.get('access_token', 'N/A')[:50]}...")
            print(f"   令牌类型: {login_data.get('token_type', 'N/A')}")
            
            # 获取用户信息
            user_info = login_data.get('user', {})
            print(f"   用户ID: {user_info.get('id', 'N/A')}")
            print(f"   用户名: {user_info.get('username', 'N/A')}")
            print(f"   邮箱: {user_info.get('email', 'N/A')}")
            print(f"   昵称: {user_info.get('nickname', 'N/A')}")
            print(f"   角色: {user_info.get('role', 'N/A')}")
            print(f"   状态: {user_info.get('status', 'N/A')}")
            print(f"   无限AI配额: {user_info.get('ai_unlimited', 'N/A')}")
            
            # 验证权限
            access_token = login_data.get('access_token')
            if access_token:
                test_admin_permissions(BASE_URL, access_token)
            
            return True
            
        else:
            print("❌ 超级管理员登录失败!")
            print(f"   错误信息: {login_response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        print("   请确保API服务器正在运行在 http://127.0.0.1:10090")
        return False
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 登录测试过程中发生错误: {e}")
        return False


def test_admin_permissions(base_url: str, access_token: str):
    """测试管理员权限"""
    
    print("\n🔍 测试管理员权限...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 测试用户管理权限
    try:
        print("📋 测试用户列表访问权限...")
        users_response = requests.get(
            f"{base_url}/api/admin/users",
            headers=headers,
            timeout=10
        )
        
        if users_response.status_code == 200:
            users_data = users_response.json()
            print(f"✅ 用户管理权限验证成功 (找到 {len(users_data.get('users', []))} 个用户)")
        else:
            print(f"⚠️  用户管理权限测试失败: {users_response.status_code}")
            
    except Exception as e:
        print(f"⚠️  用户管理权限测试异常: {e}")
    
    # 测试系统信息访问权限
    try:
        print("🖥️  测试系统信息访问权限...")
        system_response = requests.get(
            f"{base_url}/api/admin/system/info",
            headers=headers,
            timeout=10
        )
        
        if system_response.status_code == 200:
            print("✅ 系统信息访问权限验证成功")
        else:
            print(f"⚠️  系统信息访问权限测试失败: {system_response.status_code}")
            
    except Exception as e:
        print(f"⚠️  系统信息访问权限测试异常: {e}")


def test_regular_user_endpoints(base_url: str, access_token: str):
    """测试普通用户端点访问"""
    
    print("\n👤 测试普通用户端点访问...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 测试用户信息获取
    try:
        print("📝 测试用户信息获取...")
        profile_response = requests.get(
            f"{base_url}/api/auth/me",
            headers=headers,
            timeout=10
        )
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print("✅ 用户信息获取成功")
            print(f"   用户名: {profile_data.get('username', 'N/A')}")
            print(f"   角色: {profile_data.get('role', 'N/A')}")
        else:
            print(f"⚠️  用户信息获取失败: {profile_response.status_code}")
            
    except Exception as e:
        print(f"⚠️  用户信息获取异常: {e}")


def main():
    """主函数"""
    print(f"🕒 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试超级管理员登录
    success = test_super_admin_login()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 超级管理员登录测试完成!")
        print("✅ 超级管理员账号工作正常，可以用于开发和调试")
    else:
        print("❌ 超级管理员登录测试失败!")
        print("请检查账号创建是否成功，或API服务器是否正常运行")
    print("=" * 60)


if __name__ == "__main__":
    main()