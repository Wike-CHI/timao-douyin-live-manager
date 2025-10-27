#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""初始化MySQL数据库和用户"""

import pymysql
import getpass

print('=' * 60)
print('🐱 提猫直播助手 - MySQL 数据库初始化')
print('=' * 60)
print()

# 获取MySQL root密码
root_password = getpass.getpass('请输入 MySQL root 密码: ')

try:
    # 使用root用户连接
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password=root_password
    )
    
    cursor = conn.cursor()
    
    print('\n✅ 成功连接到 MySQL 服务器')
    print()
    print('开始初始化...')
    print('-' * 60)
    
    # 1. 创建数据库
    print('1. 创建数据库 timao_live...')
    cursor.execute("CREATE DATABASE IF NOT EXISTS timao_live CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    print('   ✅ 数据库已创建')
    
    # 2. 创建用户（先删除可能存在的旧用户）
    print('2. 创建用户 timao@localhost...')
    cursor.execute("DROP USER IF EXISTS 'timao'@'localhost'")
    cursor.execute("CREATE USER 'timao'@'localhost' IDENTIFIED BY 'timao-20251030'")
    print('   ✅ 用户已创建')
    
    # 3. 授予权限
    print('3. 授予权限...')
    cursor.execute("GRANT ALL PRIVILEGES ON timao_live.* TO 'timao'@'localhost'")
    cursor.execute("FLUSH PRIVILEGES")
    print('   ✅ 权限已授予')
    
    cursor.close()
    conn.close()
    
    print()
    print('=' * 60)
    print('✅ MySQL 数据库初始化完成!')
    print('=' * 60)
    print()
    print('数据库配置:')
    print('  主机: localhost')
    print('  端口: 3306')
    print('  数据库: timao_live')
    print('  用户: timao')
    print('  密码: timao-20251030')
    print()
    print('下一步: 运行以下命令创建数据表')
    print('  python init_tables.py')
    print()
    
except pymysql.Error as e:
    print(f'\n❌ 初始化失败: {e}')
    print()
    print('常见问题:')
    print('  - MySQL 服务未运行: net start MySQL80')
    print('  - root 密码错误: 请重新输入正确密码')
    print('  - 权限不足: 确保使用 root 账户')
except Exception as e:
    print(f'\n❌ 发生错误: {e}')
