#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查 server/local 中的所有导入问题
"""

import os
import re
from pathlib import Path

def check_imports(root_dir):
    """检查所有Python文件中的导入"""
    issues = []
    
    for py_file in Path(root_dir).rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查是否有指向外部server模块的导入
            patterns = [
                r'from server\.app\.',
                r'from server\.ai\.',
                r'from server\.nlp\.',
                r'from server\.ingest\.',
                r'from server\.knowledge\.',
                r'from server\.utils\.',
                r'import server\.app',
                r'import server\.ai',
                r'import server\.nlp',
            ]
            
            for line_num, line in enumerate(content.split('\n'), 1):
                for pattern in patterns:
                    if re.search(pattern, line):
                        issues.append({
                            'file': str(py_file.relative_to(root_dir)),
                            'line': line_num,
                            'content': line.strip(),
                            'pattern': pattern
                        })
                        
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    return issues

if __name__ == "__main__":
    root = Path("server/local")
    issues = check_imports(root)
    
    if issues:
        print(f"发现 {len(issues)} 个外部导入问题:\n")
        for issue in issues:
            print(f"{issue['file']}:{issue['line']}")
            print(f"   {issue['content']}")
            print()
    else:
        print("没有发现外部导入问题!")
