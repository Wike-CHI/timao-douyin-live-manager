#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户注册和登录测试脚本
测试账号: 3132812664@qq.com
用户名: WIke
密码: 987987123
"""

import requests
import json
import time

# 配置
BASE_URL = "http://localhost:10090"  # FastAPI后端地址
REGISTER_ENDPOINT = "/api/auth/register"
LOGIN_ENDPOINT = "/api/auth/login"
ME_ENDPOINT = "/api/auth/me"

def test_register():
    """测试用户注册"""
    print("=" * 60)
    print("🐱 提猫直播助手 - 用户注册测试")
    print("=" * 60)
    
    # 注册数据
    register_data = {
        "email": "3132812664@qq.com",
        "password": "987987123",
        "nickname": "WIke",
        "username": "WIke"
    }
    
    print(f"正在注册用户: {register_data['email']}")
    print(f"用户名: {register_data['username']}")
    print(f"昵称: {register_data['nickname']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}{REGISTER_ENDPOINT}",
            json=register_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n注册响应状态码: {response.status_code}")
        
        if response.status_code == 201:
            user_data = response.json()
            print("✅ 注册成功!")
            print(f"用户ID: {user_data['id']}")
            print(f"用户名: {user_data['username']}")
            print(f"邮箱: {user_data['email']}")
            print(f"昵称: {user_data.get('nickname', 'N/A')}")
            print(f"角色: {user_data['role']}")
            print(f"状态: {user_data['status']}")
            return True
        else:
            error_data = response.text
            print(f"❌ 注册失败: {error_data}")
            # 如果是邮箱或用户名已存在，也算测试通过
            if "已存在" in error_data:
                print("⚠️  用户已存在，这在测试中是可以接受的")
                return True
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保后端服务正在运行")
        print("请运行: npm run dev")
        return False
    except Exception as e:
        print(f"❌ 注册过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_login():
    """测试用户登录"""
    print("\n" + "=" * 60)
    print("🔐 提猫直播助手 - 用户登录测试")
    print("=" * 60)
    
    # 登录数据
    login_data = {
        "username_or_email": "3132812664@qq.com",
        "password": "987987123"
    }
    
    print(f"正在登录用户: {login_data['username_or_email']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}{LOGIN_ENDPOINT}",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n登录响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            login_response = response.json()
            print("✅ 登录成功!")
            print(f"访问令牌: {login_response['access_token'][:20]}...")
            print(f"刷新令牌: {login_response['refresh_token'][:20]}...")
            print(f"令牌类型: {login_response['token_type']}")
            print(f"过期时间: {login_response['expires_in']} 秒")
            
            user_data = login_response['user']
            print(f"用户ID: {user_data['id']}")
            print(f"用户名: {user_data['username']}")
            print(f"邮箱: {user_data['email']}")
            print(f"昵称: {user_data.get('nickname', 'N/A')}")
            
            # 保存令牌用于后续测试
            access_token = login_response['access_token']
            
            # 测试获取当前用户信息
            test_get_user_info(access_token)
            
            return access_token
        else:
            error_data = response.text
            print(f"❌ 登录失败: {error_data}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保后端服务正在运行")
        return None
    except Exception as e:
        print(f"❌ 登录过程中发生错误: {e}")
        return None

def test_get_user_info(access_token):
    """测试获取用户信息"""
    print("\n" + "-" * 40)
    print("👤 获取用户信息测试")
    print("-" * 40)
    
    try:
        response = requests.get(
            f"{BASE_URL}{ME_ENDPOINT}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        print(f"获取用户信息响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ 获取用户信息成功!")
            print(f"用户名: {user_data['username']}")
            print(f"邮箱: {user_data['email']}")
            print(f"角色: {user_data['role']}")
            print(f"状态: {user_data['status']}")
            return True
        else:
            error_data = response.text
            print(f"❌ 获取用户信息失败: {error_data}")
            return False
            
    except Exception as e:
        print(f"❌ 获取用户信息时发生错误: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始提猫直播助手认证测试")
    
    # 测试注册
    register_success = test_register()
    
    if register_success:
        print("\n⏳ 等待2秒后进行登录测试...")
        time.sleep(2)
        
        # 测试登录
        access_token = test_login()
        
        if access_token:
            print("\n🎉 所有测试完成!")
            print("✅ 用户注册和登录功能正常工作")
        else:
            print("\n❌ 登录测试失败")
    else:
        print("\n❌ 注册测试失败，无法继续登录测试")

if __name__ == "__main__":
    main()