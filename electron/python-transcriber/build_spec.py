#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyInstaller 打包配置文件

打包命令:
  python build_spec.py

输出:
  dist/transcriber_service (Linux/Mac)
  dist/transcriber_service.exe (Windows)
"""

import os
import sys
import PyInstaller.__main__

# 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 模型目录（如果需要打包模型，可以指定）
# 注意：SenseVoice 模型约 1.5GB，可能需要从 modelscope cache 复制
MODEL_DIR = os.path.join(BASE_DIR, 'models')

# PyInstaller 参数
pyinstaller_args = [
    'transcriber_service.py',
    '--onefile',
    '--name=transcriber_service',
    '--console',
    '--clean',
    
    # 添加数据文件（如果需要打包模型）
    # f'--add-data={MODEL_DIR}:models',
    
    # 隐藏导入（确保所有依赖都被打包）
    '--hidden-import=funasr',
    '--hidden-import=modelscope',
    '--hidden-import=torch',
    '--hidden-import=torchaudio',
    '--hidden-import=flask',
    '--hidden-import=flask_cors',
    '--hidden-import=numpy',
    
    # 排除不需要的模块（减小体积）
    '--exclude-module=matplotlib',
    '--exclude-module=IPython',
    '--exclude-module=jupyter',
    '--exclude-module=notebook',
    
    # 输出目录
    '--distpath=dist',
    '--workpath=build',
    '--specpath=.',
]

if __name__ == '__main__':
    print("=" * 60)
    print("开始打包 Python Transcriber Service...")
    print("=" * 60)
    print(f"基础目录: {BASE_DIR}")
    print(f"输出目录: {os.path.join(BASE_DIR, 'dist')}")
    print("=" * 60)
    
    # 运行 PyInstaller
    PyInstaller.__main__.run(pyinstaller_args)
    
    print("=" * 60)
    print("打包完成！")
    print(f"可执行文件: {os.path.join(BASE_DIR, 'dist', 'transcriber_service')}")
    print("=" * 60)

