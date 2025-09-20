# 创建服务器目录结构
import os

def create_project_structure():
    """创建项目目录结构"""
    
    directories = [
        'server/app',
        'server/app/api',
        'server/app/core',
        'server/app/models',
        'server/app/services',
        'server/app/utils',
        'frontend',
        'frontend/css',
        'frontend/js',
        'frontend/assets',
        'data',
        'logs',
        'tests'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        
        # 创建 __init__.py 文件 (Python包)
        if directory.startswith('server/app'):
            init_file = os.path.join(directory, '__init__.py')
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write('# -*- coding: utf-8 -*-\n')
    
    print("✅ 项目目录结构创建完成")

if __name__ == "__main__":
    create_project_structure()