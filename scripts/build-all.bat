@echo off
echo ========================================
echo 提猫直播助手 - 完整构建脚本
echo ========================================

:: 设置错误处理
setlocal enabledelayedexpansion

:: 检查Python环境
echo [1/6] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境，请先安装Python
    pause
    exit /b 1
)

:: 检查Node.js环境
echo [2/6] 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Node.js环境，请先安装Node.js
    pause
    exit /b 1
)

:: 安装依赖
echo [3/6] 安装项目依赖...
call npm run setup:dev
if errorlevel 1 (
    echo 错误: 依赖安装失败
    pause
    exit /b 1
)

:: 清理旧构建
echo [4/6] 清理旧构建文件...
call npm run clean
if errorlevel 1 (
    echo 警告: 清理过程中出现错误，继续构建...
)

:: 构建后端服务
echo [5/6] 构建后端服务...
call npm run build:backend
if errorlevel 1 (
    echo 错误: 后端构建失败
    pause
    exit /b 1
)

:: 构建前端和打包
echo [6/6] 构建前端并打包应用...
call npm run build
if errorlevel 1 (
    echo 错误: 应用打包失败
    pause
    exit /b 1
)

echo ========================================
echo 构建完成！
echo 输出目录: dist/
echo ========================================
pause