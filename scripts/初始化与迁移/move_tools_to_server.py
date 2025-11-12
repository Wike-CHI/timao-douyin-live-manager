#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将 tools/ 目录移动到 server/tools/ 并更新所有引用
"""

import os
import shutil
import re
from pathlib import Path

ROOT = Path(__file__).parent.resolve()

# 需要更新的文件
FILES_TO_UPDATE = [
    "electron/main.js",
    "server/utils/bootstrap.py",
    "server/app/api/live_audio.py",
    "server/app/services/live_audio_stream_service.py",
    "README.md",
    "docs/开发规范与流程/PROJECT_STRUCTURE.md",
]

def update_file_content(file_path: Path, replacements: list):
    """更新文件内容"""
    if not file_path.exists():
        print(f"⚠️  文件不存在: {file_path}")
        return False
    
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        for old_pattern, new_pattern in replacements:
            content = content.replace(old_pattern, new_pattern)
            # 也尝试正则替换（更灵活）
            content = re.sub(
                re.escape(old_pattern.replace('\\', '/')),
                new_pattern.replace('\\', '/'),
                content
            )
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            print(f"✅ 已更新: {file_path}")
            return True
        else:
            print(f"ℹ️  无需更新: {file_path}")
            return False
    except Exception as e:
        print(f"❌ 更新失败: {file_path}, 错误: {e}")
        return False

def move_tools_directory(dry_run: bool = False):
    """移动 tools/ 目录到 server/tools/"""
    src = ROOT / "tools"
    dst = ROOT / "server" / "tools"
    
    if not src.exists():
        print(f"⚠️  tools/ 目录不存在: {src}")
        return False
    
    if dst.exists():
        print(f"⚠️  目标目录已存在: {dst}")
        return False
    
    if dry_run:
        print(f"📋 [DRY RUN] 将移动: {src} -> {dst}")
        return True
    
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        print(f"✅ 已移动: tools/ -> server/tools/")
        return True
    except Exception as e:
        print(f"❌ 移动失败: {src} -> {dst}, 错误: {e}")
        return False

def update_references(dry_run: bool = False):
    """更新所有引用"""
    print("\n" + "=" * 60)
    print("更新文件引用")
    print("=" * 60)
    
    replacements = [
        # 路径替换
        ('tools/prepare_torch.py', 'server/tools/prepare_torch.py'),
        ('tools/download_sensevoice.py', 'server/tools/download_sensevoice.py'),
        ('tools/download_vad_model.py', 'server/tools/download_vad_model.py'),
        ('tools/ffmpeg', 'server/tools/ffmpeg'),
        ('"tools/', '"server/tools/'),
        ("'tools/", "'server/tools/"),
        ('/tools/', '/server/tools/'),
        # JavaScript 路径（相对路径）
        (["tools/prepare_torch.py"], ["server/tools/prepare_torch.py"]),  # 在 electron/main.js 中
    ]
    
    updated_count = 0
    
    for file_path_str in FILES_TO_UPDATE:
        file_path = ROOT / file_path_str
        if not file_path.exists():
            continue
        
        # 特殊处理 electron/main.js
        if file_path_str == "electron/main.js":
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            # 更新路径：tools/prepare_torch.py -> server/tools/prepare_torch.py
            content = content.replace("'tools/prepare_torch.py'", "'server/tools/prepare_torch.py'")
            if content != original_content:
                if not dry_run:
                    file_path.write_text(content, encoding='utf-8')
                print(f"✅ 已更新: {file_path}")
                updated_count += 1
            continue
        
        # 其他文件的替换
        for old_pattern, new_pattern in replacements:
            if isinstance(old_pattern, str) and isinstance(new_pattern, str):
                if update_file_content(file_path, [(old_pattern, new_pattern)]):
                    updated_count += 1
                    break
    
    return updated_count

def main():
    import sys
    dry_run = "--apply" not in sys.argv
    
    print("=" * 60)
    print("📦 将 tools/ 移动到 server/tools/")
    print("=" * 60)
    if dry_run:
        print("🔍 [DRY RUN 模式] 仅预览，不会实际移动文件")
    print()
    
    # 1. 移动目录
    if move_tools_directory(dry_run):
        # 2. 更新引用
        if not dry_run:
            updated = update_references(dry_run)
            print(f"\n✅ 完成！更新了 {updated} 个文件")
        else:
            print("\n📋 [DRY RUN] 预览完成")
            print("💡 实际执行请运行: python scripts/初始化与迁移/move_tools_to_server.py --apply")
    else:
        print("\n❌ 移动失败，请检查错误信息")

if __name__ == "__main__":
    main()

