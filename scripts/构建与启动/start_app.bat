@echo off
title 语音转录服务启动器

echo ========================================
echo 语音转录服务桌面应用启动器
echo ========================================

REM 检查Node.js是否已安装
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Node.js
    echo 请先从 https://nodejs.org/ 下载并安装Node.js
    echo.
    pause
    exit /b 1
)

REM 检查npm是否已安装
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到npm
    echo 请确保Node.js已正确安装（包含npm）
    echo.
    pause
    exit /b 1
)

echo Node.js环境检查通过

REM 切换到项目目录
cd /d "%~dp0"

REM 检查Electron目录是否存在
if not exist "electron" (
    echo 错误: 未找到electron目录
    echo.
    pause
    exit /b 1
)

REM 安装Electron依赖（如果需要）
if not exist "electron\node_modules" (
    echo 正在安装Electron依赖...
    cd electron
    npm install
    if %errorlevel% neq 0 (
        echo 错误: Electron依赖安装失败
        echo.
        pause
        exit /b 1
    )
    cd ..
    echo Electron依赖安装完成
)

echo 正在启动语音转录服务桌面应用...
echo.

REM 启动Electron应用
cd electron
npx electron .
cd ..

echo 应用已启动
pause