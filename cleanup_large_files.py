#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理大文件脚本
用于识别和处理Git仓库中的大文件
"""

import os
import sys
from pathlib import Path

def find_large_files(directory: str, size_threshold: int = 50 * 1024 * 1024) -> list:
    """查找大于指定大小的文件
    
    Args:
        directory: 要搜索的目录
        size_threshold: 文件大小阈值（字节），默认50MB
        
    Returns:
        大文件列表
    """
    large_files = []
    
    # 定义要忽略的目录和文件模式
    ignore_patterns = [
        '.git', '__pycache__', 'node_modules', 
        '.vscode', '.idea', 'logs'
    ]
    
    # 定义要忽略的文件扩展名
    ignore_extensions = [
        '.mp3', '.wav', '.mp4', '.mov', '.avi', '.mkv', '.flv', '.webm',
        '.m4a', '.aac', '.flac', '.ogg', '.wmv', '.zip', '.tar.gz', '.rar', '.7z'
    ]
    
    for root, dirs, files in os.walk(directory):
        # 移除要忽略的目录
        dirs[:] = [d for d in dirs if d not in ignore_patterns]
        
        for file in files:
            file_path = Path(root) / file
            try:
                file_size = file_path.stat().st_size
                
                # 检查文件大小
                if file_size > size_threshold:
                    # 检查文件扩展名
                    should_ignore = False
                    for ext in ignore_extensions:
                        if file.endswith(ext):
                            should_ignore = True
                            break
                    
                    if not should_ignore:
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
    print("🔍 查找大文件...")
    
    # 获取当前目录
    current_dir = Path(__file__).parent
    
    # 查找大于10MB的文件
    large_files = find_large_files(str(current_dir), 10 * 1024 * 1024)
    
    if not large_files:
        print("✅ 没有找到大于10MB的文件")
        return
    
    print(f"📁 找到 {len(large_files)} 个大于10MB的文件:")
    print("-" * 80)
    
    for file_path, size in large_files:
        relative_path = os.path.relpath(file_path, current_dir)
        print(f"{format_size(size):>10} | {relative_path}")
    
    print("-" * 80)
    print("💡 建议:")
    print("1. 将大文件添加到 .gitignore 中")
    print("2. 使用 Git LFS 管理大文件")
    print("3. 考虑将大文件存储到云存储中")

if __name__ == "__main__":
    main()