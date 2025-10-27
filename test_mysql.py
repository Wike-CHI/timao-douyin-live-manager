#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MySQL连接和权限测试脚本
"""

import pymysql
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_mysql_connection():
    """测试MySQL连接"""
    print("=" * 60)
    print("🐬 MySQL连接和权限测试")
    print("=" * 60)
    
    # 从环境变量获取配置
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
    mysql_user = os.getenv('MYSQL_USER', 'timao')
    mysql_password = os.getenv('MYSQL_PASSWORD', 'timao-1030')
    mysql_database = os.getenv('MYSQL_DATABASE', 'timao_live')
    
    print(f"MySQL配置:")
    print(f"  主机: {mysql_host}:{mysql_port}")
    print(f"  用户: {mysql_user}")
    print(f"  数据库: {mysql_database}")
    
    try:
        # 测试root连接（用于检查权限）
        print("\n1. 测试root用户连接...")
        root_connection = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            user='root',
            password='123456',  # 尝试空密码
            charset='utf8mb4'
        )
        print("✅ root用户连接成功")
        
        cursor = root_connection.cursor()
        cursor.execute("SELECT User, Host FROM mysql.user WHERE User='timao'")
        users = cursor.fetchall()
        print(f"timao用户信息: {users}")
        
        cursor.execute("SHOW DATABASES LIKE 'timao_live'")
        databases = cursor.fetchall()
        print(f"timao_live数据库是否存在: {len(databases) > 0}")
        
        cursor.close()
        root_connection.close()
        
    except Exception as e:
        print(f"⚠️  root用户连接失败: {e}")
        print("这可能是因为root密码不正确或MySQL服务未运行")
    
    try:
        # 测试timao用户连接
        print("\n2. 测试timao用户连接...")
        connection = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            charset='utf8mb4'
        )
        
        print("✅ timao用户连接成功!")
        
        # 测试查询权限
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"数据库中的表数量: {len(tables)}")
        
        # 尝试创建测试表
        try:
            cursor.execute("DROP TABLE IF EXISTS test_table")
            cursor.execute("""
                CREATE TABLE test_table (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(50) NOT NULL
                )
            """)
            print("✅ 表创建权限正常")
            
            # 插入测试数据
            cursor.execute("INSERT INTO test_table (name) VALUES ('test')")
            connection.commit()
            print("✅ 数据插入权限正常")
            
            # 查询测试数据
            cursor.execute("SELECT * FROM test_table")
            result = cursor.fetchall()
            print(f"✅ 数据查询正常: {result}")
            
            # 删除测试表
            cursor.execute("DROP TABLE IF EXISTS test_table")
            print("✅ 表删除权限正常")
            
        except Exception as e:
            print(f"⚠️  DDL/DML权限测试失败: {e}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ timao用户连接失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🚀 开始MySQL连接和权限测试")
    
    test_mysql_connection()
    
    print("\n🎉 MySQL测试完成!")

if __name__ == "__main__":
    main()