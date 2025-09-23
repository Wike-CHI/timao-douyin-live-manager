@echo off
title 语音转录服务自动启动器

echo ========================================
echo 语音转录服务自动启动器
echo ========================================

REM 切换到项目目录
cd /d "%~dp0"

REM 检查Python是否已安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python
    echo 请先安装Python 3.7或更高版本
    echo.
    pause
    exit /b 1
)

echo Python环境检查通过

REM 启动自动启动服务脚本
echo 正在启动语音转录服务...
python auto_launch_service.py

echo 服务已启动
pause