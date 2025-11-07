#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境变量配置迁移脚本

功能:
1. 从根目录.env分离配置到前后端
2. 自动识别配置项归属
3. 生成新的前后端.env文件
4. 备份原配置

使用:
    python scripts/migrate_env_config.py

审查人: 叶维哲
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# 前端相关环境变量前缀
FRONTEND_PREFIXES = ['VITE_', 'ELECTRON_']

# 后端相关环境变量关键词
BACKEND_KEYWORDS = [
    'BACKEND_', 'DB_', 'MYSQL_', 'REDIS_', 'SECRET_', 'ENCRYPTION_',
    'OPENAI_', 'QWEN_', 'BAIDU_', 'GEMINI_', 'AI_', 'DEFAULT_AI_',
    'DOUYIN_', 'SENSEVOICE_', 'LOG_', 'CORS_', 'DATA_', 'UPLOAD_',
    'REPORT_', 'DEBUG', 'TIMEZONE', 'WEBSOCKET_', 'COMMENT_', 'SENTIMENT_'
]

def parse_env_file(env_path: str) -> List[Tuple[str, str, str]]:
    """
    解析.env文件
    
    Returns:
        List of (key, value, comment) tuples
    """
    if not Path(env_path).exists():
        return []
    
    entries = []
    current_comment = []
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line_stripped = line.strip()
            
            # 注释行
            if line_stripped.startswith('#'):
                current_comment.append(line_stripped)
            # 空行
            elif not line_stripped:
                current_comment = []
            # 配置行
            elif '=' in line_stripped:
                key, value = line_stripped.split('=', 1)
                key = key.strip()
                value = value.strip()
                comment = '\n'.join(current_comment) if current_comment else ''
                entries.append((key, value, comment))
                current_comment = []
    
    return entries

def classify_env_var(key: str) -> str:
    """
    判断环境变量归属
    
    Returns:
        'frontend', 'backend', or 'unknown'
    """
    # 检查前端前缀
    for prefix in FRONTEND_PREFIXES:
        if key.startswith(prefix):
            return 'frontend'
    
    # 检查后端关键词
    for keyword in BACKEND_KEYWORDS:
        if keyword in key:
            return 'backend'
    
    return 'unknown'

def generate_env_file(entries: List[Tuple[str, str, str]], target: str) -> str:
    """生成.env文件内容"""
    lines = []
    
    # 添加头部
    if target == 'frontend':
        lines.append("# ============================================")
        lines.append("# 提猫直播助手 - 前端开发环境变量")
        lines.append("# ============================================")
        lines.append("# 📝 由根目录.env迁移而来")
        lines.append(f"# 📅 迁移时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
    else:
        lines.append("# ============================================")
        lines.append("# 提猫直播助手 - 后端服务环境变量")
        lines.append("# ============================================")
        lines.append("# 📝 由根目录.env迁移而来")
        lines.append(f"# 📅 迁移时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
    
    # 添加配置项
    for key, value, comment in entries:
        if comment:
            lines.append(comment)
        lines.append(f"{key}={value}")
        lines.append("")
    
    return '\n'.join(lines)

def main():
    """主函数"""
    print("="*60)
    print("🔄 环境变量配置迁移")
    print("="*60)
    print()
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    root_env = project_root / ".env"
    backend_env = project_root / "server" / ".env"
    frontend_env = project_root / "electron" / "renderer" / ".env"
    
    # 检查根目录.env是否存在
    if not root_env.exists():
        print("❌ 根目录.env文件不存在，无需迁移")
        print("ℹ️  如果您已经分离配置，可以忽略此消息")
        return 0
    
    print(f"✅ 找到根目录配置文件: {root_env}")
    print()
    
    # 解析根目录.env
    print("📋 解析配置项...")
    all_entries = parse_env_file(str(root_env))
    print(f"✅ 找到 {len(all_entries)} 个配置项")
    print()
    
    # 分类配置项
    frontend_entries = []
    backend_entries = []
    unknown_entries = []
    
    for key, value, comment in all_entries:
        category = classify_env_var(key)
        if category == 'frontend':
            frontend_entries.append((key, value, comment))
        elif category == 'backend':
            backend_entries.append((key, value, comment))
        else:
            unknown_entries.append((key, value, comment))
    
    print("📊 配置分类结果:")
    print(f"  前端配置: {len(frontend_entries)} 项")
    print(f"  后端配置: {len(backend_entries)} 项")
    print(f"  未分类: {len(unknown_entries)} 项")
    print()
    
    # 显示未分类项
    if unknown_entries:
        print("⚠️  以下配置项未能自动分类，默认归入后端:")
        for key, _, _ in unknown_entries:
            print(f"  - {key}")
        print()
        backend_entries.extend(unknown_entries)
    
    # 确认迁移
    response = input("确认开始迁移? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ 迁移已取消")
        return 0
    
    print()
    print("🚀 开始迁移...")
    
    # 备份原配置
    backup_path = project_root / f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy(root_env, backup_path)
    print(f"✅ 已备份原配置到: {backup_path}")
    
    # 生成前端配置
    if frontend_entries:
        frontend_content = generate_env_file(frontend_entries, 'frontend')
        frontend_env.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果前端.env已存在,备份
        if frontend_env.exists():
            frontend_backup = frontend_env.parent / f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy(frontend_env, frontend_backup)
            print(f"✅ 已备份前端原配置到: {frontend_backup}")
        
        with open(frontend_env, 'w', encoding='utf-8') as f:
            f.write(frontend_content)
        print(f"✅ 已生成前端配置: {frontend_env}")
    else:
        print("ℹ️  未找到前端配置项,跳过生成")
    
    # 生成后端配置
    if backend_entries:
        backend_content = generate_env_file(backend_entries, 'backend')
        backend_env.parent.mkdir(parents=True, exist_ok=True)
        
        # 如果后端.env已存在,备份
        if backend_env.exists():
            backend_backup = backend_env.parent / f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy(backend_env, backend_backup)
            print(f"✅ 已备份后端原配置到: {backend_backup}")
        
        with open(backend_env, 'w', encoding='utf-8') as f:
            f.write(backend_content)
        print(f"✅ 已生成后端配置: {backend_env}")
    else:
        print("ℹ️  未找到后端配置项,跳过生成")
    
    print()
    print("="*60)
    print("✅ 配置迁移完成!")
    print("="*60)
    print()
    print("📝 后续步骤:")
    print("  1. 检查生成的配置文件是否正确")
    print("  2. 运行验证脚本: python scripts/validate_port_config.py")
    print("  3. 测试前后端服务是否正常启动")
    print("  4. 确认无误后可删除根目录.env (已备份)")
    print()
    print(f"📖 参考文档: docs/PORT_CONFIGURATION.md")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

