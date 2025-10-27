#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最简化的测试脚本
"""

import os
import sys

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("Python版本:", sys.version)
print("当前工作目录:", os.getcwd())
print("项目根目录:", project_root)

# 测试基本导入
print("\n测试基本导入...")
try:
    import pymysql
    print("✅ pymysql导入成功")
except Exception as e:
    print(f"❌ pymysql导入失败: {e}")

try:
    from dotenv import load_dotenv
    print("✅ dotenv导入成功")
except Exception as e:
    print(f"❌ dotenv导入失败: {e}")

# 加载环境变量
print("\n加载环境变量...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    db_type = os.getenv('DB_TYPE')
    mysql_host = os.getenv('MYSQL_HOST')
    mysql_user = os.getenv('MYSQL_USER')
    print(f"DB_TYPE: {db_type}")
    print(f"MYSQL_HOST: {mysql_host}")
    print(f"MYSQL_USER: {mysql_user}")
except Exception as e:
    print(f"❌ 环境变量加载失败: {e}")

print("\n测试完成!")