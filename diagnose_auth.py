#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整的认证系统诊断脚本
用于找出500错误的根本原因
"""

import requests
import json
import os
import sys
import traceback

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def check_environment():
    """检查环境配置"""
    print("=" * 60)
    print("🌍 环境配置检查")
    print("=" * 60)
    
    # 检查环境变量文件
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        print("✅ .env文件存在")
        # 读取关键配置
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'DB_TYPE=mysql' in content:
                print("✅ 数据库类型设置为MySQL")
            if 'MYSQL_HOST=localhost' in content:
                print("✅ MySQL主机设置为localhost")
    else:
        print("❌ .env文件不存在")
    
    # 检查必要的环境变量
    required_vars = ['DB_TYPE', 'MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ 环境变量 {var} 已设置")
        else:
            print(f"❌ 环境变量 {var} 未设置")

def check_dependencies():
    """检查依赖包"""
    print("\n" + "=" * 60)
    print("📦 依赖包检查")
    print("=" * 60)
    
    required_packages = [
        'pymysql',
        'sqlalchemy',
        'passlib',
        'python-jose',
        'cryptography'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            print(f"❌ {package} 未安装")

def check_mysql_service():
    """检查MySQL服务"""
    print("\n" + "=" * 60)
    print("🐬 MySQL服务检查")
    print("=" * 60)
    
    try:
        import pymysql
        
        # 从环境变量获取配置
        mysql_host = os.getenv('MYSQL_HOST', 'localhost')
        mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
        mysql_user = os.getenv('MYSQL_USER', 'timao')
        mysql_password = os.getenv('MYSQL_PASSWORD', 'timao-1030')
        mysql_database = os.getenv('MYSQL_DATABASE', 'timao_live')
        
        print(f"尝试连接到: {mysql_host}:{mysql_port}")
        
        # 测试连接
        connection = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            charset='utf8mb4',
            connect_timeout=5
        )
        
        print("✅ MySQL连接成功!")
        
        # 检查数据库
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE()")
        current_db = cursor.fetchone()
        print(f"当前数据库: {current_db[0] if current_db else 'N/A'}")
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"数据表数量: {len(tables)}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ MySQL连接失败: {e}")
        print("可能的原因:")
        print("  1. MySQL服务未运行")
        print("  2. MySQL配置不正确")
        print("  3. 用户权限不足")
        print("  4. 数据库不存在")

def check_backend_api():
    """检查后端API"""
    print("\n" + "=" * 60)
    print("🌐 后端API检查")
    print("=" * 60)
    
    base_url = "http://localhost:10090"
    
    # 检查根路径
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"根路径状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ 后端服务正在运行")
        else:
            print("❌ 后端服务响应异常")
    except Exception as e:
        print(f"❌ 无法访问后端服务: {e}")
        print("请确保运行: npm run dev")
        return False
    
    # 检查API文档
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        print(f"API文档状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ API文档可访问")
    except Exception as e:
        print(f"❌ API文档不可访问: {e}")
    
    return True

def test_registration_with_debug():
    """带调试信息的注册测试"""
    print("\n" + "=" * 60)
    print("📝 注册功能测试")
    print("=" * 60)
    
    base_url = "http://localhost:10090"
    register_endpoint = "/api/auth/register"
    
    # 注册数据
    register_data = {
        "email": "3132812664@qq.com",
        "password": "987987123",
        "nickname": "WIke",
        "username": "WIke"
    }
    
    print(f"发送注册请求到: {base_url}{register_endpoint}")
    print(f"请求数据: {json.dumps(register_data, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            f"{base_url}{register_endpoint}",
            json=register_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        except:
            print(f"响应文本: {response.text}")
        
        if response.status_code in [200, 201]:
            print("✅ 注册成功!")
            return True
        else:
            print(f"❌ 注册失败，状态码: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"❌ 注册过程中发生错误: {e}")
        traceback.print_exc()
        return False

def check_project_structure():
    """检查项目结构"""
    print("\n" + "=" * 60)
    print("📁 项目结构检查")
    print("=" * 60)
    
    required_paths = [
        'server/app/api/auth.py',
        'server/app/services/user_service.py',
        'server/app/models/user.py',
        'server/app/database.py'
    ]
    
    for path in required_paths:
        full_path = os.path.join(os.path.dirname(__file__), path)
        if os.path.exists(full_path):
            print(f"✅ {path}")
        else:
            print(f"❌ {path} 不存在")

def main():
    """主函数"""
    print("🚀 开始完整的认证系统诊断")
    
    # 检查环境配置
    check_environment()
    
    # 检查依赖包
    check_dependencies()
    
    # 检查项目结构
    check_project_structure()
    
    # 检查MySQL服务
    check_mysql_service()
    
    # 检查后端API
    backend_ok = check_backend_api()
    
    if backend_ok:
        # 测试注册功能
        test_registration_with_debug()
    
    print("\n" + "=" * 60)
    print("🏁 诊断完成")
    print("=" * 60)

if __name__ == "__main__":
    main()