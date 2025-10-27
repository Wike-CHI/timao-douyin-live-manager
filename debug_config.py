#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试配置管理器 - 检查环境变量读取
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_env_file():
    """调试.env文件内容"""
    print("=" * 60)
    print("🔍 调试 .env 文件内容")
    print("=" * 60)
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env 文件不存在")
        return
    
    print(f"📁 .env 文件路径: {env_file.absolute()}")
    
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"📄 .env 文件总行数: {len(lines)}")
    
    # 查找MySQL相关配置
    mysql_vars = {}
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            if 'MYSQL' in key:
                mysql_vars[key] = value
                print(f"  第{i}行: {key} = {value}")
    
    if not mysql_vars:
        print("❌ 未找到MySQL相关配置")
    else:
        print(f"✅ 找到 {len(mysql_vars)} 个MySQL配置项")
    
    return mysql_vars

def debug_os_environ():
    """调试操作系统环境变量"""
    print("\n" + "=" * 60)
    print("🌍 调试操作系统环境变量")
    print("=" * 60)
    
    mysql_env_vars = [
        'MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_USER', 
        'MYSQL_PASSWORD', 'MYSQL_DATABASE'
    ]
    
    for var in mysql_env_vars:
        value = os.getenv(var)
        if value:
            # 隐藏密码
            display_value = "***" if 'PASSWORD' in var else value
            print(f"  {var} = {display_value}")
        else:
            print(f"  {var} = (未设置)")

def debug_config_manager():
    """调试配置管理器"""
    print("\n" + "=" * 60)
    print("⚙️ 调试配置管理器")
    print("=" * 60)
    
    try:
        from server.config import config_manager
        
        print("✅ 配置管理器导入成功")
        
        # 获取数据库配置
        db_config = config_manager.config.database
        
        print(f"  数据库类型: {db_config.db_type}")
        print(f"  MySQL主机: {db_config.mysql_host}")
        print(f"  MySQL端口: {db_config.mysql_port}")
        print(f"  MySQL用户: {db_config.mysql_user}")
        print(f"  MySQL密码: {'***' if db_config.mysql_password else '(空)'}")
        print(f"  MySQL数据库: {db_config.mysql_database}")
        
        return db_config
        
    except Exception as e:
        print(f"❌ 配置管理器导入失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_mysql_connection(db_config):
    """测试MySQL连接"""
    print("\n" + "=" * 60)
    print("🔌 测试MySQL连接")
    print("=" * 60)
    
    if not db_config:
        print("❌ 无法获取数据库配置")
        return
    
    try:
        import pymysql
        
        connection = pymysql.connect(
            host=db_config.mysql_host,
            port=db_config.mysql_port,
            user=db_config.mysql_user,
            password=db_config.mysql_password,
            database=db_config.mysql_database,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ MySQL连接成功! 版本: {version[0]}")
            
            cursor.execute("SELECT DATABASE()")
            database = cursor.fetchone()
            print(f"✅ 当前数据库: {database[0]}")
            
        connection.close()
        
    except Exception as e:
        print(f"❌ MySQL连接失败: {e}")
        
        # 分析错误原因
        error_str = str(e)
        if "Access denied" in error_str:
            if "using password: NO" in error_str:
                print("💡 错误分析: 密码为空，可能是环境变量未正确读取")
            else:
                print("💡 错误分析: 用户名或密码错误")
        elif "Can't connect" in error_str:
            print("💡 错误分析: 无法连接到MySQL服务器")

def main():
    """主函数"""
    print("🐱 提猫直播助手 - 配置调试工具")
    
    # 1. 调试.env文件
    mysql_vars = debug_env_file()
    
    # 2. 调试操作系统环境变量
    debug_os_environ()
    
    # 3. 调试配置管理器
    db_config = debug_config_manager()
    
    # 4. 测试MySQL连接
    test_mysql_connection(db_config)
    
    print("\n" + "=" * 60)
    print("🎯 调试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()