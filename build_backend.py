#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
后端Python服务打包脚本
使用PyInstaller将FastAPI服务打包为可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def install_pyinstaller():
    """安装PyInstaller"""
    try:
        import PyInstaller
        print("PyInstaller 已安装")
        return True
    except ImportError:
        print("正在安装 PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("PyInstaller 安装成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"PyInstaller 安装失败: {e}")
            return False

def create_backend_spec():
    """创建PyInstaller spec文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# 项目根目录
project_root = Path(os.getcwd())

# 数据文件和隐藏导入
datas = [
    (str(project_root / 'server'), 'server'),
    (str(project_root / 'AST_module'), 'AST_module'),
    (str(project_root / 'DouyinLiveWebFetcher'), 'DouyinLiveWebFetcher'),
    (str(project_root / 'config'), 'config'),
    (str(project_root / 'schemas'), 'schemas'),
    (str(project_root / 'models'), 'models'),
]

# 隐藏导入的模块
hiddenimports = [
    'uvicorn',
    'fastapi',
    'pydantic',
    'sqlalchemy',
    'asyncio',
    'websockets',
    'json',
    'logging',
    'datetime',
    'pathlib',
    'typing',
    'server.main',
    'server.api',
    'server.websocket',
    'server.database',
    'server.models',
    'server.schemas',
    'server.utils',
    'AST_module',
    'DouyinLiveWebFetcher',
]

a = Analysis(
    ['server/app/main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='backend',
)'''
    
    spec_path = Path("backend.spec")
    with open(spec_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"创建 spec 文件: {spec_path}")
    return spec_path

def build_backend():
    """构建后端可执行文件"""
    print("开始构建后端服务...")
    
    # 安装PyInstaller
    if not install_pyinstaller():
        return False
    
    # 创建spec文件
    spec_path = create_backend_spec()
    
    # 清理之前的构建
    build_dir = Path("build")
    dist_dir = Path("dist")
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("清理 build 目录")
    
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("清理 dist 目录")
    
    # 运行PyInstaller
    try:
        cmd = [sys.executable, "-m", "PyInstaller", "--clean", str(spec_path)]
        print(f"执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("后端服务构建成功!")
            
            # 检查生成的文件
            exe_path = dist_dir / "timao-backend.exe"
            if exe_path.exists():
                print(f"可执行文件位置: {exe_path.absolute()}")
                print(f"文件大小: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")
                return True
            else:
                print("未找到生成的可执行文件")
                return False
        else:
            print(f"构建失败:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"构建过程出错: {e}")
        return False

def create_backend_launcher():
    """创建后端启动脚本"""
    launcher_content = '''@echo off
chcp 65001 > nul
title 提猫直播助手 - 后端服务

echo ========================================
echo 提猫直播助手 - 后端服务
echo ========================================
echo.

echo 正在启动后端服务...
echo 服务地址: http://localhost:8000
echo 管理界面: http://localhost:8000/docs
echo.

REM 设置环境变量
set PYTHONIOENCODING=utf-8
set PYTHONPATH=%~dp0

REM 启动服务
"%~dp0timao-backend.exe"

echo.
echo 服务已停止，按任意键退出...
pause > nul
'''
    
    launcher_path = Path("dist/start_backend.bat")
    launcher_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(launcher_path, 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    
    print(f"创建启动脚本: {launcher_path}")

def print_banner():
    """打印构建横幅"""
    banner = """
    ========================================
    提猫直播助手 - 后端服务打包工具
    ========================================
    """
    print(banner)

def main():
    """主函数"""
    print_banner()
    
    # 检查当前目录
    if not Path("server").exists():
        print("错误: 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 构建后端
    if build_backend():
        create_backend_launcher()
        print("\n后端服务打包完成!")
        print("输出目录: dist/")
        print("运行方式: 执行 dist/start_backend.bat")
    else:
        print("\n后端服务打包失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()