#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查MySQL数据表"""

import pymysql

try:
    # 连接数据库
    conn = pymysql.connect(
        host='localhost',
        user='timao',
        password='timao-20251030',
        database='timao_live'
    )
    
    cursor = conn.cursor()
    
    # 查询所有表
    cursor.execute('SHOW TABLES')
    tables = cursor.fetchall()
    
    print('=' * 60)
    print('🐱 提猫直播助手 - MySQL 数据表检查')
    print('=' * 60)
    print()
    
    if tables:
        print(f'✅ 数据库 timao_live 中已存在 {len(tables)} 个表:')
        print('-' * 60)
        for idx, table in enumerate(tables, 1):
            print(f'  {idx}. {table[0]}')
    else:
        print('⚠️ 数据库中没有找到任何表')
        print()
        print('需要运行初始化脚本创建表:')
        print('  python -c "from server.app.database import DatabaseManager; from server.config import config_manager; db = DatabaseManager(config_manager.config.database); db.initialize()"')
    
    print()
    print('=' * 60)
    
    # 如果有表，显示每个表的结构
    if tables and len(tables) > 0:
        print()
        print('📊 表结构详情:')
        print('=' * 60)
        for table_name in tables:
            cursor.execute(f'DESCRIBE {table_name[0]}')
            columns = cursor.fetchall()
            print(f'\n表名: {table_name[0]} ({len(columns)} 个字段)')
            print('-' * 60)
            for col in columns[:5]:  # 只显示前5个字段
                print(f'  - {col[0]}: {col[1]}')
            if len(columns) > 5:
                print(f'  ... 还有 {len(columns) - 5} 个字段')
    
    cursor.close()
    conn.close()
    
    print()
    print('✅ 检查完成!')
    
except pymysql.Error as e:
    print(f'❌ 数据库连接失败: {e}')
    print()
    print('请检查:')
    print('  1. MySQL 服务是否运行')
    print('  2. 数据库 timao_live 是否存在')
    print('  3. 用户 timao 是否有访问权限')
    print('  4. .env 文件中的密码是否正确')
except Exception as e:
    print(f'❌ 发生错误: {e}')
