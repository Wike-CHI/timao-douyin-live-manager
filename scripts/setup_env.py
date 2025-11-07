#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键配置环境变量脚本

功能:
1. 自动创建前后端.env文件
2. 使用项目当前数据库配置
3. 遵循KISS原则和希克定律

使用:
    python scripts/setup_env.py

审查人: 叶维哲
"""

import os
import sys
from pathlib import Path

# 后端环境变量模板 (使用项目当前配置)
BACKEND_ENV_TEMPLATE = """# ============================================
# 提猫直播助手 - 后端服务环境变量
# ============================================
# 审查人: 叶维哲
# 自动生成于: {timestamp}

# ------------------------------------------
# 🚀 服务端口配置 (必需)
# ------------------------------------------
BACKEND_PORT=9030

# ------------------------------------------
# 🗄️ 数据库配置 (必需)
# ------------------------------------------
DB_TYPE=mysql
MYSQL_HOST=rm-bp1sqxf05yom2hwdhko.mysql.rds.aliyuncs.com
MYSQL_PORT=3306
MYSQL_USER=timao
MYSQL_PASSWORD=Yw123456
MYSQL_DATABASE=timao

# ------------------------------------------
# 🔐 安全配置 (生产环境必须修改！)
# ------------------------------------------
SECRET_KEY=timao-secret-key-change-in-production-must-be-64-chars-minimum
ENCRYPTION_KEY=timao-encryption-key-32chars

# ------------------------------------------
# 🤖 AI服务配置 (可选)
# ------------------------------------------
GEMINI_API_KEY=
DEFAULT_AI_PROVIDER=gemini

# ------------------------------------------
# 📝 应用配置
# ------------------------------------------
LOG_LEVEL=INFO
LOG_DIR=logs
CORS_ORIGINS=*
DEBUG=false
TIMEZONE=Asia/Shanghai
WEBSOCKET_ENABLED=true
"""

# 前端环境变量模板
FRONTEND_ENV_TEMPLATE = """# ============================================
# 提猫直播助手 - 前端开发环境变量
# ============================================
# 审查人: 叶维哲
# 自动生成于: {timestamp}

# ------------------------------------------
# 🌐 开发服务器配置 (必需)
# ------------------------------------------
VITE_PORT=10013
VITE_HOST=127.0.0.1

# ------------------------------------------
# 🔗 后端服务地址 (必需)
# ------------------------------------------
VITE_FASTAPI_URL=http://127.0.0.1:9030
VITE_STREAMCAP_URL=http://127.0.0.1:9030
VITE_DOUYIN_URL=http://127.0.0.1:9030

# ------------------------------------------
# 🛠️ 开发配置 (可选)
# ------------------------------------------
VITE_HMR=true
VITE_SOURCEMAP=true
"""

def create_env_file(path: Path, content: str, service_name: str) -> bool:
    """创建.env文件"""
    from datetime import datetime
    
    # 检查是否已存在
    if path.exists():
        response = input(f"⚠️  {service_name} .env 文件已存在，是否覆盖? (y/N): ").strip().lower()
        if response != 'y':
            print(f"⏭️  跳过 {service_name} 配置")
            return False
        
        # 备份现有文件
        backup_path = path.parent / f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        path.rename(backup_path)
        print(f"✅ 已备份到: {backup_path}")
    
    # 创建新文件
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.format(timestamp=timestamp))
    
    print(f"✅ 已创建 {service_name} 配置: {path}")
    return True

def main():
    """主函数"""
    print("="*60)
    print("🚀 提猫直播助手 - 一键环境配置")
    print("="*60)
    print()
    print("📋 遵循原则: KISS、单一职责、希克定律")
    print()
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    
    # 后端配置路径
    backend_env = project_root / "server" / ".env"
    # 前端配置路径
    frontend_env = project_root / "electron" / "renderer" / ".env"
    
    print("📝 将创建以下配置文件:")
    print(f"  1. 后端: {backend_env}")
    print(f"  2. 前端: {frontend_env}")
    print()
    
    print("✨ 配置内容 (遵循希克定律 - 只关注核心配置):")
    print()
    print("后端核心配置 (6项):")
    print("  1. ✅ BACKEND_PORT=9030")
    print("  2. ✅ DB_TYPE=mysql")
    print("  3. ✅ MYSQL_HOST=rm-bp1sqxf05yom2hwdhko.mysql.rds.aliyuncs.com")
    print("  4. ✅ MYSQL_USER=timao")
    print("  5. ✅ MYSQL_PASSWORD=Yw123456")
    print("  6. ✅ MYSQL_DATABASE=timao")
    print()
    print("前端核心配置 (3项):")
    print("  1. ✅ VITE_PORT=10013")
    print("  2. ✅ VITE_HOST=127.0.0.1")
    print("  3. ✅ VITE_FASTAPI_URL=http://127.0.0.1:9030")
    print()
    
    response = input("确认创建配置? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ 配置已取消")
        return 0
    
    print()
    print("🚀 开始创建配置...")
    print()
    
    # 创建后端配置
    backend_created = create_env_file(backend_env, BACKEND_ENV_TEMPLATE, "后端")
    
    # 创建前端配置
    frontend_created = create_env_file(frontend_env, FRONTEND_ENV_TEMPLATE, "前端")
    
    print()
    print("="*60)
    print("✅ 配置完成!")
    print("="*60)
    print()
    
    if backend_created or frontend_created:
        print("📝 后续步骤:")
        print("  1. 验证配置: python scripts/validate_port_config.py")
        print("  2. 启动后端: cd server && python app/main.py")
        print("  3. 启动前端: cd electron/renderer && npm run dev")
        print()
        print("📖 详细文档: docs/PORT_CONFIGURATION.md")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

