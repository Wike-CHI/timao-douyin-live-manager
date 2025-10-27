#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
详细用户注册和登录测试脚本
用于调试500错误问题
"""

import requests
import json
import time
import traceback

# 配置
BASE_URL = "http://localhost:10090"  # FastAPI后端地址
REGISTER_ENDPOINT = "/api/auth/register"
LOGIN_ENDPOINT = "/api/auth/login"

def detailed_register_test():
    """详细测试用户注册"""
    print("=" * 60)
    print("🔍 详细用户注册测试")
    print("=" * 60)
    
    # 注册数据
    register_data = {
        "email": "3132812664@qq.com",
        "password": "987987123",
        "nickname": "WIke",
        "username": "WIke"
    }
    
    print(f"注册数据: {json.dumps(register_data, ensure_ascii=False, indent=2)}")
    
    try:
        print(f"\n发送POST请求到: {BASE_URL}{REGISTER_ENDPOINT}")
        response = requests.post(
            f"{BASE_URL}{REGISTER_ENDPOINT}",
            json=register_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"响应JSON: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        except:
            print(f"响应文本: {response.text}")
        
        if response.status_code == 201:
            print("✅ 注册成功!")
            return True
        else:
            print(f"❌ 注册失败，状态码: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {e}")
        print("请确保后端服务正在运行 (npm run dev 或 python -m server.app.main)")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ 请求超时: {e}")
        return False
    except Exception as e:
        print(f"❌ 注册过程中发生未预期错误: {e}")
        traceback.print_exc()
        return False

def check_backend_health():
    """检查后端健康状态"""
    print("\n" + "=" * 60)
    print("🏥 检查后端健康状态")
    print("=" * 60)
    
    try:
        # 检查根路径
        response = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"根路径状态码: {response.status_code}")
        
        # 检查健康检查端点
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"健康检查状态码: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"健康检查数据: {json.dumps(health_data, ensure_ascii=False, indent=2)}")
            
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")

def check_database_connection():
    """检查数据库连接"""
    print("\n" + "=" * 60)
    print("🗄️ 检查数据库连接")
    print("=" * 60)
    
    try:
        # 尝试导入数据库配置
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
        
        from server.config import config_manager
        db_config = config_manager.config.database
        
        print(f"数据库类型: {db_config.db_type}")
        if db_config.db_type == "mysql":
            print(f"MySQL主机: {db_config.mysql_host}:{db_config.mysql_port}")
            print(f"MySQL数据库: {db_config.mysql_database}")
            print(f"MySQL用户: {db_config.mysql_user}")
        else:
            print(f"SQLite路径: {db_config.sqlite_path}")
            
    except Exception as e:
        print(f"❌ 数据库配置检查失败: {e}")
        traceback.print_exc()

def main():
    """主函数"""
    print("🚀 开始详细提猫直播助手认证测试")
    
    # 检查后端健康状态
    check_backend_health()
    
    # 检查数据库连接
    check_database_connection()
    
    # 测试注册
    print("\n" + "=" * 60)
    print("📝 开始注册测试")
    print("=" * 60)
    
    register_success = detailed_register_test()
    
    if register_success:
        print("\n🎉 注册测试成功!")
    else:
        print("\n❌ 注册测试失败，请检查以上错误信息")

if __name__ == "__main__":
    main()