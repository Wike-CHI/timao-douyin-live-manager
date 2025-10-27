#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 useFree API 接口
"""

import requests
import json

def test_usefree_api():
    """测试 useFree API"""
    
    # API 基础URL
    base_url = "http://127.0.0.1:10090"
    
    print("🚀 开始测试 useFree API...")
    
    # 1. 先登录获取token
    print("\n🔍 步骤1: 登录获取token...")
    login_url = f"{base_url}/api/auth/login"
    login_data = {
        "username_or_email": "dev_admin",
        "password": "DevAdmin@2024!"
    }
    
    try:
        login_response = requests.post(login_url, json=login_data)
        print(f"登录状态码: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get("token")
            print(f"登录成功，获取到token: {token[:20]}...")
            
            # 2. 测试 useFree 接口
            print("\n🔍 步骤2: 测试 useFree 接口...")
            usefree_url = f"{base_url}/api/auth/useFree"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            usefree_response = requests.post(usefree_url, headers=headers)
            print(f"useFree 状态码: {usefree_response.status_code}")
            print(f"useFree 响应头: {dict(usefree_response.headers)}")
            
            if usefree_response.status_code == 200:
                usefree_result = usefree_response.json()
                print(f"useFree 响应内容: {json.dumps(usefree_result, indent=2, ensure_ascii=False)}")
                print("✅ useFree 接口测试成功！")
            else:
                print(f"❌ useFree 接口测试失败")
                try:
                    error_detail = usefree_response.json()
                    print(f"错误详情: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
                except:
                    print(f"错误响应: {usefree_response.text}")
                    
        else:
            print(f"❌ 登录失败，状态码: {login_response.status_code}")
            try:
                error_detail = login_response.json()
                print(f"登录错误详情: {json.dumps(error_detail, indent=2, ensure_ascii=False)}")
            except:
                print(f"登录错误响应: {login_response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保后端服务器正在运行")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    test_usefree_api()