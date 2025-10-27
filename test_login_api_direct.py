#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试登录API的脚本
"""

import requests
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_login_api():
    """测试登录API"""
    print("🔍 测试登录API...")
    
    # API端点
    api_url = "http://127.0.0.1:10090/api/auth/login"
    
    # 测试数据 - 使用正确的字段名
    test_credentials = [
        {"username_or_email": "admin", "password": "admin123"},
        {"username_or_email": "test", "password": "test123"},
        {"username_or_email": "admin", "password": "wrongpassword"},
    ]
    
    for i, creds in enumerate(test_credentials, 1):
        print(f"\n--- 测试 {i}: {creds['username_or_email']} ---")
        
        try:
            # 发送POST请求
            response = requests.post(
                api_url,
                json=creds,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            # 尝试解析JSON响应
            try:
                response_data = response.json()
                print(f"响应内容: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError:
                print(f"响应内容 (非JSON): {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ 连接失败 - 服务器可能未启动")
        except requests.exceptions.Timeout:
            print("❌ 请求超时")
        except Exception as e:
            print(f"❌ 请求异常: {e}")

def test_health_check():
    """测试健康检查端点"""
    print("\n🔍 测试健康检查端点...")
    
    try:
        response = requests.get("http://127.0.0.1:10090/health", timeout=5)
        print(f"健康检查状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"健康检查响应: {response.json()}")
        else:
            print(f"健康检查响应: {response.text}")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")

def test_root_endpoint():
    """测试根端点"""
    print("\n🔍 测试根端点...")
    
    try:
        response = requests.get("http://127.0.0.1:10090/", timeout=5)
        print(f"根端点状态码: {response.status_code}")
        print(f"根端点响应长度: {len(response.text)} 字符")
    except Exception as e:
        print(f"❌ 根端点测试失败: {e}")

if __name__ == "__main__":
    print("🚀 开始API测试...")
    
    # 测试基本端点
    test_health_check()
    test_root_endpoint()
    
    # 测试登录API
    test_login_api()
    
    print("\n✅ 测试完成")