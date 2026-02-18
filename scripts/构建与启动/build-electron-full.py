#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整打包脚本
使用 Python 运行，避免 Windows 命令行中文路径问题
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd, cwd=None, shell=False):
    """运行命令并返回结果"""
    print(f"执行: {cmd}")
    print(f"目录: {cwd}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        shell=shell or sys.platform == 'win32',
        capture_output=True,
        text=True
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode


def main():
    """主函数"""
    print("=" * 60)
    print("提猫直播助手 - 完整打包脚本")
    print("=" * 60)

    # 项目根目录
    project_root = Path(__file__).parent.parent.parent.resolve()
    print(f"项目目录: {project_root}")

    # 1. 构建前端
    print("\n[1/5] 构建前端应用...")
    renderer_dir = project_root / "electron" / "renderer"
    result = run_command(["npm", "run", "build"], cwd=str(renderer_dir))
    if result != 0:
        print("[ERROR] 前端构建失败")
        return False
    print("[OK] 前端构建完成")

    # 2. 打包转写服务
    print("\n[2/5] 打包 Python 转写服务...")
    transcriber_dir = project_root / "electron" / "python-transcriber"

    # 安装 PyInstaller
    result = run_command([sys.executable, "-m", "pip", "install", "pyinstaller>=5.0"])
    if result != 0:
        print("[ERROR] PyInstaller 安装失败")
        return False

    # 运行 PyInstaller
    result = run_command([sys.executable, "build_spec.py"], cwd=str(transcriber_dir))
    if result != 0:
        print("[ERROR] 转写服务打包失败")
        return False
    print("[OK] 转写服务打包完成")

    # 3. 打包后端服务
    print("\n[3/5] 打包后端服务...")
    backend_script = project_root / "scripts" / "构建与启动" / "build_backend.py"

    if not backend_script.exists():
        print(f"[ERROR] 后端打包脚本不存在: {backend_script}")
        return False

    # 使用虚拟环境中的 Python
    if sys.platform == 'win32':
        python_path = project_root / ".venv" / "Scripts" / "python.exe"
    else:
        python_path = project_root / ".venv" / "bin" / "python"

    if not python_path.exists():
        python_path = sys.executable

    result = run_command([str(python_path), str(backend_script)])
    if result != 0:
        print("[ERROR] 后端服务打包失败")
        return False
    print("[OK] 后端服务打包完成")

    # 4. 准备资源文件
    print("\n[4/5] 准备资源文件...")
    resources_dir = project_root / "electron" / "resources"
    resources_dir.mkdir(parents=True, exist_ok=True)

    backend_resources = resources_dir / "backend"
    backend_resources.mkdir(parents=True, exist_ok=True)

    transcriber_resources = resources_dir / "python-transcriber"
    transcriber_resources.mkdir(parents=True, exist_ok=True)

    # 复制转写服务
    transcriber_exe = transcriber_dir / "dist" / "transcriber_service.exe"
    if transcriber_exe.exists():
        shutil.copy2(transcriber_exe, transcriber_resources / "transcriber_service.exe")
        print("  - 复制 transcriber_service.exe")
    else:
        print(f"[WARNING] 转写服务可执行文件不存在: {transcriber_exe}")

    # 复制后端服务
    backend_exe = project_root / "backend_dist" / "timao_backend_service.exe"
    if backend_exe.exists():
        shutil.copy2(backend_exe, backend_resources / "timao_backend_service.exe")
        print("  - 复制 timao_backend_service.exe")
    else:
        print(f"[WARNING] 后端服务可执行文件不存在: {backend_exe}")

    print("[OK] 资源文件准备完成")

    # 5. 构建 Electron 便携版
    print("\n[5/5] 构建 Electron 便携版...")

    # 清理旧的打包文件
    dist_dir = project_root / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    # 确保 extraResources 目录存在
    backend_dist = project_root / "backend_dist"
    backend_dist.mkdir(parents=True, exist_ok=True)

    # 复制资源到 extraResources 位置
    for f in backend_resources.iterdir():
        shutil.copy2(f, backend_dist / f.name)

    # 运行 electron-builder
    result = run_command(
        ["npx", "electron-builder", "--win", "--x64", "--config", "build-config.json"],
        cwd=str(project_root)
    )
    if result != 0:
        print("[ERROR] Electron 打包失败")
        return False

    print("\n" + "=" * 60)
    print("打包完成!")
    print(f"输出目录: {dist_dir}")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
