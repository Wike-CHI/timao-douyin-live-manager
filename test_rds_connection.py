#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试阿里云RDS连接
配置好白名单后运行此脚本
"""
import os
import sys
from pathlib import Path

# 设置标准输出为UTF-8编码（解决Windows PowerShell GBK编码问题）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import pymysql
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ 缺少依赖库: {e}")
    print("\n💡 请先安装依赖:")
    print("   pip install pymysql python-dotenv")
    sys.exit(1)

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_rds_connection():
    """测试RDS连接"""
    try:
        
        # 加载环境变量
        env_path = project_root / ".env"
        load_dotenv(env_path)
        
        # 读取RDS配置
        host = os.getenv("RDS_HOST")
        port = int(os.getenv("RDS_PORT", "3306"))
        user = os.getenv("RDS_USER")
        password = os.getenv("RDS_PASSWORD")
        database = os.getenv("RDS_DATABASE")
        
        print("=" * 60)
        print("🔗 正在测试RDS连接...")
        print("=" * 60)
        print(f"主机: {host}")
        print(f"端口: {port}")
        print(f"用户: {user}")
        print(f"数据库: {database}")
        print()
        
        # 尝试连接
        print("⏳ 连接中... (超时10秒)")
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            connect_timeout=10
        )
        
        print("✅ 连接成功！")
        print()
        
        # 测试查询
        with conn.cursor() as cursor:
            # 查看MySQL版本
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"📊 MySQL版本: {version[0]}")
            
            # 查看当前数据库
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()
            print(f"📂 当前数据库: {current_db[0]}")
            
            # 查看现有表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"📋 现有表数量: {len(tables)}")
            
            if tables:
                print(f"   表列表:")
                for table in tables[:10]:  # 只显示前10个
                    print(f"     - {table[0]}")
                if len(tables) > 10:
                    print(f"     ... 还有 {len(tables) - 10} 个表")
            else:
                print("   ⚠️ 数据库为空，还没有表")
            
            # 测试写入权限
            print()
            print("🔐 测试写入权限...")
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS __test_connection__ (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        test_time DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("INSERT INTO __test_connection__ VALUES ()")
                cursor.execute("DROP TABLE __test_connection__")
                conn.commit()
                print("✅ 写入权限正常")
            except Exception as e:
                print(f"❌ 写入权限异常: {e}")
        
        conn.close()
        
        print()
        print("=" * 60)
        print("🎉 RDS连接测试完成！")
        print("=" * 60)
        print()
        print("✅ 下一步:")
        print("   1. 运行 'python init_tables.py' 初始化数据表")
        print("   2. 运行 'npm run dev' 启动应用")
        print()
        
        return True
        
    except ImportError as e:
        print()
        print("❌ 缺少依赖库")
        print(f"   错误: {e}")
        print()
        print("💡 解决方法:")
        print("   pip install pymysql python-dotenv")
        print()
        return False
        
    except pymysql.Error as e:
        print()
        print("❌ RDS连接失败")
        print(f"   错误: {e}")
        print()
        print("💡 可能的原因:")
        print("   1. 【最常见】RDS白名单未添加本机IP")
        print(f"      → 你的IPv6: 2001:19f0:0:7aea:5400:5ff:fe66:6bd5")
        print("      → 前往: https://rdsnext.console.aliyun.com/")
        print("      → 操作: 实例 → 数据安全性 → 白名单设置 → 添加")
        print()
        print(f"   2. 数据库 '{database}' 不存在")
        print("      → 登录RDS控制台创建数据库")
        print()
        print(f"   3. 用户 '{user}' 权限不足")
        print("      → 检查用户权限设置")
        print()
        print("   4. 密码错误")
        print("      → 检查 .env 文件中的 RDS_PASSWORD")
        print()
        return False
        
    except Exception as e:
        print()
        print(f"❌ 未知错误: {e}")
        print()
        return False


if __name__ == "__main__":
    success = test_rds_connection()
    sys.exit(0 if success else 1)
