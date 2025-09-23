#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版 .gitignore 验证脚本
检查大文件是否被正确忽略
"""

import os
import sys
from pathlib import Path
import fnmatch

def load_gitignore_patterns(gitignore_path: str) -> list:
    """加载 .gitignore 文件中的模式"""
    patterns = []
    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
    except FileNotFoundError:
        print(f"⚠️ 未找到 .gitignore 文件: {gitignore_path}")
    return patterns

def should_ignore(file_path: str, patterns: list, root_path: str) -> bool:
    """检查文件是否应该被忽略"""
    relative_path = os.path.relpath(file_path, root_path)
    
    for pattern in patterns:
        # 处理绝对路径模式
        if pattern.startswith('/'):
            if fnmatch.fnmatch(relative_path, pattern[1:]):
                return True
        else:
            # 处理相对路径模式
            if fnmatch.fnmatch(relative_path, pattern):
                return True
            # 处理目录模式
            if pattern.endswith('/'):
                if relative_path.startswith(pattern) or relative_path.startswith(pattern[:-1]):
                    return True
    return False

def find_large_files(directory: str, size_threshold: int = 1 * 1024 * 1024) -> list:
    """查找大于指定大小的文件"""
    large_files = []
    
    for root, dirs, files in os.walk(directory):
        # 跳过 .git 和 node_modules 目录
        if '.git' in root or 'node_modules' in root:
            continue
            
        for file in files:
            file_path = Path(root) / file
            try:
                file_size = file_path.stat().st_size
                
                # 检查文件大小
                if file_size > size_threshold:
                    large_files.append((str(file_path), file_size))
            except (OSError, FileNotFoundError):
                # 忽略无法访问的文件
                continue
    
    # 按大小排序
    large_files.sort(key=lambda x: x[1], reverse=True)
    return large_files

def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def main():
    """主函数"""
    print("🔍 验证 .gitignore 配置...")
    
    # 获取当前目录
    current_dir = Path(__file__).parent
    gitignore_path = current_dir / '.gitignore'
    
    # 加载 .gitignore 模式
    patterns = load_gitignore_patterns(str(gitignore_path))
    print(f"📄 加载了 {len(patterns)} 个忽略模式")
    
    # 查找大文件
    print("\n🔍 查找大于1MB的文件...")
    large_files = find_large_files(str(current_dir), 1 * 1024 * 1024)
    
    if not large_files:
        print("✅ 没有找到大于1MB的文件")
        return
    
    print(f"📁 找到 {len(large_files)} 个大于1MB的文件:")
    print("-" * 80)
    
    ignored_count = 0
    unignored_count = 0
    
    for file_path, size in large_files:
        relative_path = os.path.relpath(file_path, current_dir)
        
        if should_ignore(file_path, patterns, str(current_dir)):
            status = "✅ 已忽略"
            ignored_count += 1
        else:
            status = "❌ 未忽略"
            unignored_count += 1
            
        print(f"{status} | {format_size(size):>10} | {relative_path}")
    
    print("-" * 80)
    print(f"📊 统计: {ignored_count} 个文件已忽略, {unignored_count} 个文件未忽略")
    
    if unignored_count > 0:
        print("\n⚠️ 建议将未忽略的大文件添加到 .gitignore 中")
        print("   或考虑使用 Git LFS 管理大文件")
    else:
        print("\n✅ 所有大文件都已正确忽略!")

if __name__ == "__main__":
    main()