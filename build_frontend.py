#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端Electron应用构建脚本
"""

import os
import sys
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime

# 全局变量存储npm命令路径
npm_command = 'npm'

def check_node_npm():
    """检查Node.js和npm是否安装"""
    print("🔍 检查Node.js和npm...")
    
    # 检查Node.js
    try:
        node_result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if node_result.returncode == 0:
            print(f"✅ Node.js 版本: {node_result.stdout.strip()}")
        else:
            print("❌ Node.js 未安装")
            return False
    except FileNotFoundError:
        print("❌ Node.js 未找到")
        return False
    
    # 检查npm - 尝试多种路径
    try:
        npm_paths = [
            'npm',
            r'C:\Program Files\nodejs\npm.cmd',
            r'C:\Program Files (x86)\nodejs\npm.cmd'
        ]
        
        npm_found = False
        for npm_path in npm_paths:
            try:
                npm_result = subprocess.run([npm_path, '--version'], capture_output=True, text=True)
                if npm_result.returncode == 0:
                    print(f"✅ npm 版本: {npm_result.stdout.strip()}")
                    npm_found = True
                    # 保存找到的npm路径供后续使用
                    global npm_command
                    npm_command = npm_path
                    break
            except FileNotFoundError:
                continue
        
        if not npm_found:
            print("❌ npm 未找到")
            return False
            
    except Exception as e:
        print(f"❌ npm 检查失败: {e}")
        return False
    
    return True

def install_dependencies():
    """安装项目依赖"""
    print("📦 安装项目依赖...")
    
    # 安装根目录依赖
    try:
        subprocess.check_call([npm_command, 'install'], cwd='.')
        print("✅ 根目录依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"❌ 根目录依赖安装失败: {e}")
        return False
    
    # 安装renderer依赖
    renderer_path = Path("electron/renderer")
    if renderer_path.exists():
        try:
            subprocess.check_call([npm_command, 'install'], cwd=str(renderer_path))
            print("✅ Renderer依赖安装完成")
        except subprocess.CalledProcessError as e:
            print(f"❌ Renderer依赖安装失败: {e}")
            return False
    
    return True

def build_renderer():
    """构建React前端"""
    print("🏗️ 构建React前端...")
    
    renderer_path = Path("electron/renderer")
    if not renderer_path.exists():
        print("❌ 未找到renderer目录")
        return False
    
    try:
        subprocess.check_call([npm_command, 'run', 'build'], cwd=str(renderer_path))
        print("✅ React前端构建完成")
        
        # 检查构建输出
        dist_path = renderer_path / "dist"
        if dist_path.exists():
            print(f"📁 构建输出: {dist_path.absolute()}")
            return True
        else:
            print("❌ 未找到构建输出目录")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ React前端构建失败: {e}")
        return False

def update_main_js_for_production():
    """更新main.js以适配生产环境"""
    main_js_path = Path("electron/main.js")
    if not main_js_path.exists():
        print("❌ 未找到main.js文件")
        return False
    
    # 读取原文件
    with open(main_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建生产版本的main.js
    production_content = content.replace(
        'const isDev = !app.isPackaged;',
        'const isDev = false; // 强制生产模式'
    )
    
    # 确保使用本地构建的前端文件
    production_content = production_content.replace(
        "const rendererDevServerURL = process.env.ELECTRON_RENDERER_URL || 'http://127.0.0.1:30013';",
        "const rendererDevServerURL = null; // 生产模式不使用开发服务器"
    )
    
    # 备份原文件
    backup_path = main_js_path.with_suffix('.js.backup')
    shutil.copy2(main_js_path, backup_path)
    print(f"📋 备份原文件: {backup_path}")
    
    # 写入生产版本
    with open(main_js_path, 'w', encoding='utf-8') as f:
        f.write(production_content)
    
    print("✅ 更新main.js为生产模式")
    return True

def restore_main_js():
    """恢复原始的main.js"""
    main_js_path = Path("electron/main.js")
    backup_path = main_js_path.with_suffix('.js.backup')
    
    if backup_path.exists():
        shutil.copy2(backup_path, main_js_path)
        backup_path.unlink()
        print("✅ 恢复原始main.js")

def build_electron_app():
    """构建Electron应用"""
    print("📱 构建Electron应用...")
    
    try:
        subprocess.check_call([npm_command, 'run', 'make'], cwd='.')
        print("✅ Electron应用构建完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Electron应用构建失败: {e}")
        return False

def create_integrated_launcher():
    """创建集成启动脚本"""
    launcher_content = '''@echo off
chcp 65001 >nul
echo 🚀 启动提猫直播助手...
cd /d "%~dp0"

REM 检查后端服务
if exist "backend\\timao-backend.exe" (
    echo 📡 启动后端服务...
    start /b "Backend" "backend\\timao-backend.exe"
    timeout /t 3 /nobreak >nul
) else (
    echo ⚠️  未找到后端服务，仅启动前端应用
)

REM 启动前端应用
echo 🖥️  启动前端应用...
if exist "TalkingCat-Portable-*.exe" (
    for %%f in (TalkingCat-Portable-*.exe) do (
        echo 正在启动: %%f
        start "" "%%f"
        goto :end
    )
) else (
    echo ❌ 未找到前端应用可执行文件
    echo 请确保已正确构建应用
    pause
    exit /b 1
)

:end
echo ✅ 应用启动完成
'''
    
    launcher_path = Path("dist/start_app.bat")
    launcher_path.parent.mkdir(exist_ok=True)
    
    with open(launcher_path, 'w', encoding='gbk') as f:
        f.write(launcher_content)
    
    print(f"✅ 创建集成启动脚本: {launcher_path}")

def main():
    """主函数"""
    print("=" * 50)
    print("🎯 提猫直播助手 - 前端应用打包工具")
    print("=" * 50)
    
    # 检查环境
    if not check_node_npm():
        sys.exit(1)
    
    # 检查当前目录
    if not Path("electron").exists():
        print("❌ 错误: 请在项目根目录运行此脚本")
        sys.exit(1)
    
    try:
        # 安装依赖
        if not install_dependencies():
            sys.exit(1)
        
        # 构建React前端
        if not build_renderer():
            sys.exit(1)
        
        # 更新main.js为生产模式
        if not update_main_js_for_production():
            sys.exit(1)
        
        # 构建Electron应用
        if build_electron_app():
            create_integrated_launcher()
            print("\n🎉 前端应用打包完成!")
            print("📁 输出目录: dist/")
            print("🚀 运行方式: 执行 dist/start_app.bat")
        else:
            print("\n❌ 前端应用打包失败!")
            sys.exit(1)
            
    finally:
        # 恢复原始main.js
        restore_main_js()

if __name__ == "__main__":
    main()