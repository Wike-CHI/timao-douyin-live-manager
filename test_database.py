#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库连接测试脚本
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_database_connection():
    """测试数据库连接"""
    print("=" * 60)
    print("🗄️ 数据库连接测试")
    print("=" * 60)
    
    try:
        # 导入配置
        from server.config import config_manager
        db_config = config_manager.config.database
        
        print(f"数据库类型: {db_config.db_type}")
        print(f"MySQL主机: {db_config.mysql_host}:{db_config.mysql_port}")
        print(f"MySQL数据库: {db_config.mysql_database}")
        print(f"MySQL用户: {db_config.mysql_user}")
        
        # 测试MySQL连接
        if db_config.db_type == "mysql":
            import pymysql
            print("\n尝试连接MySQL数据库...")
            connection = pymysql.connect(
                host=db_config.mysql_host,
                port=db_config.mysql_port,
                user=db_config.mysql_user,
                password=db_config.mysql_password,
                database=db_config.mysql_database,
                charset=db_config.mysql_charset
            )
            
            print("✅ MySQL连接成功!")
            
            # 测试查询
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"数据库中的表数量: {len(tables)}")
            
            cursor.close()
            connection.close()
            
        else:
            print("使用SQLite数据库")
            
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        print("请安装: pip install pymysql")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        import traceback
        traceback.print_exc()

def test_database_manager():
    """测试数据库管理器"""
    print("\n" + "=" * 60)
    print("🔧 数据库管理器测试")
    print("=" * 60)
    
    try:
        from server.config import config_manager
        from server.app.database import DatabaseManager
        
        db_config = config_manager.config.database
        db_manager = DatabaseManager(db_config)
        db_manager.initialize()
        
        print("✅ 数据库管理器初始化成功!")
        
        # 尝试获取会话
        with db_manager.get_session() as session:
            print("✅ 数据库会话获取成功!")
            
    except Exception as e:
        print(f"❌ 数据库管理器测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🚀 开始数据库连接测试")
    
    # 测试数据库连接
    test_database_connection()
    
    # 测试数据库管理器
    test_database_manager()
    
    print("\n🎉 数据库测试完成!")

if __name__ == "__main__":
    main()