#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整应用打包脚本
同时构建前端Electron应用和后端Python服务，并创建集成安装包
"""

import os
import sys
import shutil
import subprocess
import json
import zipfile
from pathlib import Path
from datetime import datetime

def print_banner():
    """打印横幅"""
    print("=" * 60)
    print("🎯 提猫直播助手 - 完整应用打包工具")
    print("=" * 60)
    print("📦 功能: 构建前端 + 后端 + 集成打包")
    print("🕒 时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

def check_prerequisites():
    """检查构建前提条件"""
    print("🔍 检查构建环境...")
    
    # 检查Python
    print(f"✅ Python 版本: {sys.version}")
    
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
    
    # 检查npm
    try:
        # 尝试多种npm路径
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
                    break
            except FileNotFoundError:
                continue
        
        if not npm_found:
            print("❌ npm 未找到")
            return False
            
    except Exception as e:
        print(f"❌ npm 检查失败: {e}")
        return False
    
    # 检查项目结构
    required_dirs = ['electron', 'server', 'electron/renderer']
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            print(f"❌ 缺少必要目录: {dir_path}")
            return False
        print(f"✅ 目录存在: {dir_path}")
    
    return True

def clean_build_dirs():
    """清理构建目录"""
    print("🧹 清理构建目录...")
    
    dirs_to_clean = ['build', 'dist', 'electron/renderer/dist']
    for dir_path in dirs_to_clean:
        dir_path = Path(dir_path)
        if dir_path.exists():
            try:
                # 在Windows上，有时需要多次尝试删除
                for attempt in range(3):
                    try:
                        shutil.rmtree(dir_path)
                        print(f"🗑️  清理: {dir_path}")
                        break
                    except PermissionError:
                        if attempt < 2:
                            import time
                            time.sleep(1)
                            continue
                        else:
                            print(f"⚠️  无法清理 {dir_path}，权限不足，跳过")
            except Exception as e:
                print(f"⚠️  清理 {dir_path} 时出错: {e}，跳过")
    
    # 清理spec文件
    spec_files = ['backend.spec']
    for spec_file in spec_files:
        spec_path = Path(spec_file)
        if spec_path.exists():
            try:
                spec_path.unlink()
                print(f"🗑️  清理: {spec_path}")
            except Exception as e:
                print(f"⚠️  清理 {spec_path} 时出错: {e}，跳过")

def build_backend():
    """构建后端服务"""
    print("\n🔧 构建后端Python服务...")
    
    try:
        result = subprocess.run([sys.executable, 'build_backend.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 后端服务构建成功")
            return True
        else:
            print("❌ 后端服务构建失败:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 后端构建过程出错: {e}")
        return False

def build_frontend():
    """构建前端应用"""
    print("\n🔧 构建前端Electron应用...")
    
    try:
        result = subprocess.run([sys.executable, 'build_frontend.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 前端应用构建成功")
            return True
        else:
            print("❌ 前端应用构建失败:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 前端构建过程出错: {e}")
        return False

def create_integrated_package():
    """创建集成安装包"""
    print("\n📦 创建集成安装包...")
    
    # 创建集成目录
    package_dir = Path("dist/TalkingCat-Integrated")
    package_dir.mkdir(parents=True, exist_ok=True)
    
    # 复制后端文件
    backend_exe = Path("dist/timao-backend.exe")
    if backend_exe.exists():
        backend_dir = package_dir / "backend"
        backend_dir.mkdir(exist_ok=True)
        shutil.copy2(backend_exe, backend_dir / "timao-backend.exe")
        print("✅ 复制后端服务")
    else:
        print("⚠️  未找到后端服务，跳过")
    
    # 复制前端文件
    frontend_files = list(Path("dist").glob("TalkingCat-Portable-*.exe"))
    if frontend_files:
        for frontend_file in frontend_files:
            shutil.copy2(frontend_file, package_dir / frontend_file.name)
            print(f"✅ 复制前端应用: {frontend_file.name}")
    else:
        print("⚠️  未找到前端应用，跳过")
    
    # 创建配置文件
    config_content = {
        "app_name": "提猫直播助手",
        "version": "1.0.0",
        "build_time": datetime.now().isoformat(),
        "components": {
            "backend": backend_exe.exists(),
            "frontend": len(frontend_files) > 0
        },
        "backend_port": 10090,
        "frontend_port": 30013
    }
    
    config_path = package_dir / "config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_content, f, indent=2, ensure_ascii=False)
    print("✅ 创建配置文件")
    
    # 创建启动脚本
    launcher_content = '''@echo off
chcp 65001 >nul
title 提猫直播助手
echo.
echo ╔══════════════════════════════════════╗
echo ║          提猫直播助手 v1.0.0          ║
echo ║     抖音直播评论实时分析与AI话术      ║
echo ╚══════════════════════════════════════╝
echo.

cd /d "%~dp0"

REM 读取配置
if not exist "config.json" (
    echo ❌ 配置文件不存在
    pause
    exit /b 1
)

REM 启动后端服务
if exist "backend\\timao-backend.exe" (
    echo 🚀 启动后端服务...
    start /b "TalkingCat-Backend" "backend\\timao-backend.exe"
    echo ⏳ 等待后端服务启动...
    timeout /t 5 /nobreak >nul
    echo ✅ 后端服务已启动
) else (
    echo ⚠️  后端服务不存在，仅启动前端
)

REM 启动前端应用
echo 🖥️  启动前端应用...
for %%f in (TalkingCat-Portable-*.exe) do (
    if exist "%%f" (
        echo 正在启动: %%f
        start "" "%%f"
        echo ✅ 前端应用已启动
        goto :success
    )
)

echo ❌ 未找到前端应用
pause
exit /b 1

:success
echo.
echo 🎉 提猫直播助手启动完成！
echo 📱 前端界面将在几秒钟内打开
echo 📡 后端服务运行在 http://127.0.0.1:10090
echo.
echo 💡 提示: 关闭此窗口将停止后端服务
echo.
pause
'''
    
    launcher_path = package_dir / "启动提猫直播助手.bat"
    with open(launcher_path, 'w', encoding='gbk') as f:
        f.write(launcher_content)
    print("✅ 创建启动脚本")
    
    # 创建说明文件
    readme_content = '''# 提猫直播助手 - 集成版

## 简介
提猫直播助手是一款专业的抖音直播评论实时分析与AI话术生成工具。

## 使用方法
1. 双击 "启动提猫直播助手.bat" 启动应用
2. 等待前端界面打开
3. 在界面中配置直播间信息
4. 开始使用AI话术生成功能

## 系统要求
- Windows 10/11 (64位)
- 至少 4GB 内存
- 至少 2GB 可用磁盘空间

## 端口说明
- 前端界面: http://127.0.0.1:30013
- 后端API: http://127.0.0.1:10090

## 故障排除
1. 如果应用无法启动，请检查防火墙设置
2. 如果端口被占用，请关闭占用端口的程序
3. 如果遇到其他问题，请查看日志文件

## 技术支持
- 开发团队: 杭州星炬耀森人工智能科技有限公司
- 产品名称: 提猫直播助手
- 版本: v1.0.0

## 版权信息
Copyright © 2024 杭州星炬耀森人工智能科技有限公司
保留所有权利。
'''
    
    readme_path = package_dir / "使用说明.txt"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("✅ 创建使用说明")
    
    return package_dir

def create_zip_package(package_dir):
    """创建ZIP压缩包"""
    print("\n📦 创建ZIP压缩包...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"TalkingCat-Integrated-{timestamp}.zip"
    zip_path = Path("dist") / zip_name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in package_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir.parent)
                zipf.write(file_path, arcname)
                
    print(f"✅ 创建压缩包: {zip_path}")
    print(f"📊 压缩包大小: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    return zip_path

def print_summary(package_dir, zip_path):
    """打印构建总结"""
    print("\n" + "=" * 60)
    print("🎉 构建完成总结")
    print("=" * 60)
    
    print(f"📁 集成包目录: {package_dir.absolute()}")
    print(f"📦 压缩包文件: {zip_path.absolute()}")
    
    print("\n📋 包含文件:")
    for file_path in package_dir.rglob('*'):
        if file_path.is_file():
            size_mb = file_path.stat().st_size / 1024 / 1024
            print(f"  📄 {file_path.name} ({size_mb:.1f} MB)")
    
    print(f"\n🚀 使用方法:")
    print(f"  1. 解压 {zip_path.name}")
    print(f"  2. 进入解压目录")
    print(f"  3. 双击 '启动提猫直播助手.bat'")
    
    print("\n✨ 构建成功！")

def main():
    """主函数"""
    print_banner()
    
    try:
        # 检查环境
        if not check_prerequisites():
            print("\n❌ 环境检查失败，请解决上述问题后重试")
            sys.exit(1)
        
        # 清理构建目录
        clean_build_dirs()
        
        # 构建后端
        if not build_backend():
            print("\n❌ 后端构建失败")
            sys.exit(1)
        
        # 构建前端
        if not build_frontend():
            print("\n❌ 前端构建失败")
            sys.exit(1)
        
        # 创建集成包
        package_dir = create_integrated_package()
        
        # 创建ZIP压缩包
        zip_path = create_zip_package(package_dir)
        
        # 打印总结
        print_summary(package_dir, zip_path)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  构建被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 构建过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()