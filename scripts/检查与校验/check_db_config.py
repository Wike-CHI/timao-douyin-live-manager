#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查当前数据库配置"""
import os
import sys
from pathlib import Path

# 方法1: 先确定项目根目录
# 当前文件: /项目根/scripts/检查与校验/check_db_config.py
# 需要回退2层到项目根
SCRIPT_DIR = Path(__file__).resolve().parent  # scripts/检查与校验/
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # 项目根目录

print(f"🔍 脚本路径: {Path(__file__).resolve()}")
print(f"📁 项目根目录: {PROJECT_ROOT}")
print(f"📂 检查 server 目录: {PROJECT_ROOT / 'server'}")
print(f"   存在: {(PROJECT_ROOT / 'server').exists()}\n")

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(PROJECT_ROOT))

# 加载环境变量
from dotenv import load_dotenv
env_path = PROJECT_ROOT / ".env"
print(f"📄 加载 .env: {env_path}")
print(f"   存在: {env_path.exists()}\n")
load_dotenv(env_path)

print("=" * 60)
print("🔍 数据库配置检查")
print("=" * 60)

# 检查环境变量
rds_host = os.getenv("RDS_HOST")
rds_database = os.getenv("RDS_DATABASE")
rds_user = os.getenv("RDS_USER")

print("\n📋 .env 文件配置:")
print(f"   RDS_HOST: {rds_host}")
print(f"   RDS_DATABASE: {rds_database}")
print(f"   RDS_USER: {rds_user}")

# 尝试导入实际配置
try:
    from server.config import config
    
    print("\n📊 实际生效的配置:")
    print(f"   主机地址: {config.database.mysql_host}")
    print(f"   数据库名: {config.database.mysql_database}")
    print(f"   用户名: {config.database.mysql_user}")
    
    print("\n" + "=" * 60)
    if rds_host and "aliyuncs.com" in config.database.mysql_host:
        print("✅ 当前使用 阿里云RDS 数据库")
        print(f"   {config.database.mysql_host}")
    elif config.database.mysql_host == "localhost":
        print("⚠️ 当前使用 本地MySQL 数据库")
        print(f"   {config.database.mysql_host}:3306")
    else:
        print("❓ 使用其他数据库")
        print(f"   {config.database.mysql_host}")
    print("=" * 60)
    
except ImportError as e:
    print(f"\n❌ 导入 server.config 失败: {e}")
    print("\n🔧 排查建议:")
    print("1. 检查 server 目录是否存在")
    print("2. 检查 server/__init__.py 是否存在")
    print("3. 检查 server/config.py 是否存在")
    print("\n当前 sys.path:")
    for p in sys.path[:5]:
        print(f"   - {p}")