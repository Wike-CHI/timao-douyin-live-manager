#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查当前数据库配置"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 60)
print("🔍 数据库配置检查")
print("=" * 60)

# 检查环境变量
rds_host = os.getenv("RDS_HOST")
rds_database = os.getenv("RDS_DATABASE")

print("\n📋 .env 文件配置:")
print(f"   RDS_HOST: {rds_host}")
print(f"   RDS_DATABASE: {rds_database}")

# 导入实际配置
from server.config import config

print("\n📊 实际生效的配置:")
print(f"   主机地址: {config.database.mysql_host}")
print(f"   数据库名: {config.database.mysql_database}")

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
