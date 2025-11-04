#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""初始化数据库表"""

from server.app.database import DatabaseManager
from server.config import config_manager

print('=' * 60)
print('🐱 提猫直播助手 - 数据表初始化')
print('=' * 60)
print()

try:
    # 获取数据库配置
    db_config = config_manager.config.database
    
    print('数据库配置:')
    print(f'  类型: {db_config.db_type}')
    if db_config.db_type == 'mysql':
        print(f'  主机: {db_config.mysql_host}:{db_config.mysql_port}')
        print(f'  数据库: {db_config.mysql_database}')
        print(f'  用户: {db_config.mysql_user}')
    else:
        print(f'  路径: {db_config.sqlite_path}')
    
    print()
    print('开始初始化...')
    print('-' * 60)
    
    # 初始化数据库管理器
    db_manager = DatabaseManager(db_config)
    db_manager.initialize()
    
    print('✅ 数据库连接成功')
    print('✅ 数据表已创建')
    
    print()
    print('=' * 60)
    print('✅ 初始化完成!')
    print('=' * 60)
    print()
    print('下一步: 启动应用服务')
    print('  npm run dev')
    print()
    
except Exception as e:
    print(f'\n❌ 初始化失败: {e}')
    print()
    print('解决方法:')
    print('  1. 确保MySQL服务正在运行')
    print('  2. 确保数据库timao_live已创建')
    print('  3. 确保用户timao有访问权限')
    print('  4. 运行: python init_mysql.py')
    print()
