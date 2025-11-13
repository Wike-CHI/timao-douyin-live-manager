#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
诊断脚本 - 检查导入和基本功能
"""

import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

print("项目根目录:", project_root)
print("Python路径:", sys.path[:3])

def test_imports():
    """测试关键模块导入"""
    print("\n" + "=" * 50)
    print("🔍 测试模块导入")
    print("=" * 50)
    
    modules_to_test = [
        'server.config',
        'server.app.database',
        'server.app.models.user',
        'server.app.services.user_service',
        'server.app.api.auth'
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module}: {e}")

def test_database_config():
    """测试数据库配置"""
    print("\n" + "=" * 50)
    print("🗄️ 测试数据库配置")
    print("=" * 50)
    
    try:
        from server.config import config_manager
        db_config = config_manager.config.database
        print(f"数据库类型: {db_config.db_type}")
        print(f"MySQL主机: {db_config.mysql_host}:{db_config.mysql_port}")
        print(f"MySQL用户: {db_config.mysql_user}")
        print(f"MySQL数据库: {db_config.mysql_database}")
    except Exception as e:
        print(f"❌ 数据库配置测试失败: {e}")

def test_direct_user_service():
    """测试直接调用用户服务"""
    print("\n" + "=" * 50)
    print("👤 测试用户服务")
    print("=" * 50)
    
    try:
        from server.config import config_manager
        from server.app.database import init_database
        from server.app.services.user_service import UserService
        from server.app.models.user import UserRoleEnum
        
        print("初始化数据库...")
        init_database(config_manager.config.database)
        print("✅ 数据库初始化成功")
        
        print("尝试创建用户...")
        user = UserService.create_user(
            username="TestUser",
            email="test@example.com",
            password="testpassword123",
            nickname="Test User"
        )
        print("✅ 用户创建成功!")
        print(f"用户ID: {user.id}")
        
    except Exception as e:
        print(f"❌ 用户服务测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("🚀 开始诊断测试")
    
    test_imports()
    test_database_config()
    test_direct_user_service()
    
    print("\n🏁 诊断测试完成!")

if __name__ == "__main__":
    main()