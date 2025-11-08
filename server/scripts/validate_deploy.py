#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署配置验证脚本
遵循：奥卡姆剃刀 + 希克定律
只检查6个必需配置项
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# 必需配置项（6个）
REQUIRED_CONFIGS = {
    "BACKEND_PORT": "服务端口",
    "DB_TYPE": "数据库类型",
    "MYSQL_HOST": "MySQL主机",
    "MYSQL_USER": "MySQL用户",
    "MYSQL_PASSWORD": "MySQL密码",
    "MYSQL_DATABASE": "MySQL数据库名",
}

def validate_config():
    """验证配置"""
    print("🔍 验证部署配置...")
    print("=" * 50)
    
    missing = []
    for key, desc in REQUIRED_CONFIGS.items():
        value = os.getenv(key)
        if not value:
            missing.append(f"  ❌ {key} ({desc})")
        else:
            # 隐藏敏感信息
            display_value = value if key != "MYSQL_PASSWORD" else "***"
            print(f"  ✅ {key}: {display_value}")
    
    if missing:
        print("\n❌ 缺少必需配置:")
        for item in missing:
            print(item)
        print("\n请编辑 .env 文件，设置以上配置项")
        return False
    
    print("\n✅ 配置验证通过（6个必需项）")
    return True

def test_database():
    """测试数据库连接"""
    print("\n🔍 测试数据库连接...")
    print("=" * 50)
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from server.app.database import engine
        
        with engine.connect() as conn:
            print("✅ 数据库连接成功")
            return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("\n请检查:")
        print("  1. 数据库服务是否运行")
        print("  2. MYSQL_HOST 是否正确")
        print("  3. MYSQL_USER 和 MYSQL_PASSWORD 是否正确")
        print("  4. 网络是否可达")
        return False

def main():
    """主函数"""
    print("🚀 提猫直播助手 - 部署验证")
    print("=" * 50)
    print("遵循：奥卡姆剃刀 + 希克定律")
    print("只检查6个必需配置项\n")
    
    # 验证配置
    if not validate_config():
        sys.exit(1)
    
    # 测试数据库
    if not test_database():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ 部署验证通过！可以启动服务了")
    print("=" * 50)
    print("\n启动命令:")
    print("  python server/app/main.py")
    print("\n或使用快速启动脚本:")
    print("  ./scripts/quick_start.sh  # Linux/macOS")
    print("  .\\scripts\\quick_start.ps1  # Windows")

if __name__ == "__main__":
    main()

