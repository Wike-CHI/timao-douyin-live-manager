#!/usr/bin/env python3
"""
测试登录和注册API的脚本
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://127.0.0.1:10090"

def test_registration_and_login():
    """测试注册和登录流程"""
    timestamp = int(time.time())
    
    # 测试数据
    test_user = {
        "username": f"logintest_{timestamp}",
        "email": f"logintest_{timestamp}@example.com", 
        "password": "testpass123",
        "nickname": f"Login Test {timestamp}"
    }
    
    print("=== 测试注册新用户 ===")
    print(f"发送注册请求到: {BASE_URL}/api/auth/register")
    print(f"请求数据: {json.dumps(test_user, indent=2, ensure_ascii=False)}")
    
    try:
        # 注册新用户
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"响应状态码: {register_response.status_code}")
        
        if register_response.status_code == 201:
            print("✅ 注册成功!")
            register_data = register_response.json()
            print(f"响应数据: {json.dumps(register_data, indent=2, ensure_ascii=False)}")
            
            # 立即测试登录
            print("\n=== 测试登录新注册用户 ===")
            login_data = {
                "username_or_email": test_user["email"],
                "password": test_user["password"]
            }
            
            print(f"发送登录请求到: {BASE_URL}/api/auth/login")
            print(f"请求数据: {json.dumps(login_data, indent=2, ensure_ascii=False)}")
            
            login_response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"响应状态码: {login_response.status_code}")
            print(f"响应头: {dict(login_response.headers)}")
            
            if login_response.status_code == 200:
                print("✅ 登录成功!")
                login_result = login_response.json()
                print(f"响应数据: {json.dumps(login_result, indent=2, ensure_ascii=False)}")
                return True
            else:
                print("❌ 登录失败!")
                try:
                    error_detail = login_response.json()
                    print(f"错误详情: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
                except:
                    print(f"错误详情: {login_response.text}")
                return False
        else:
            print("❌ 注册失败!")
            try:
                error_detail = register_response.json()
                print(f"错误详情: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                print(f"错误详情: {register_response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败! 请确保API服务器正在运行在", BASE_URL)
        return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    success = test_registration_and_login()
    if success:
        print("\n🎉 所有测试通过！登录和注册功能正常工作。")
    else:
        print("\n❌ 测试失败，请检查错误信息。")