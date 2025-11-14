@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 提猫直播助手 - Windows打包脚本
echo ========================================
echo.

:: 检查Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)

:: 检查npm
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到npm，请检查Node.js安装
    pause
    exit /b 1
)

echo [信息] Node.js版本:
node --version
echo [信息] npm版本:
npm --version
echo.

:: 进入项目根目录
cd /d "%~dp0..\.."

:: 步骤1: 清理旧的构建文件
echo [1/5] 清理旧的构建文件...
if exist "dist" (
    echo 正在删除 dist 目录...
    rd /s /q "dist"
)
if exist "electron\renderer\dist" (
    echo 正在删除 electron\renderer\dist 目录...
    rd /s /q "electron\renderer\dist"
)
echo 清理完成
echo.

:: 步骤2: 安装根目录依赖
echo [2/5] 安装根目录依赖...
call npm install
if %errorlevel% neq 0 (
    echo [错误] 安装根目录依赖失败
    pause
    exit /b 1
)
echo.

:: 步骤3: 安装渲染进程依赖
echo [3/5] 安装渲染进程依赖...
cd electron\renderer
call npm install
if %errorlevel% neq 0 (
    echo [错误] 安装渲染进程依赖失败
    pause
    exit /b 1
)
cd ..\..
echo.

:: 步骤4: 构建前端
echo [4/5] 构建前端应用...
cd electron\renderer
call npm run build
if %errorlevel% neq 0 (
    echo [错误] 构建前端失败
    pause
    exit /b 1
)
cd ..\..
echo.

:: 步骤5: 打包Electron应用
echo [5/5] 打包Electron应用...
echo 目标平台: Windows x64
echo 打包格式: Portable + NSIS
echo.

call npx electron-builder --win --x64 --config build-config.json
if %errorlevel% neq 0 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成！
echo ========================================
echo 输出目录: %cd%\dist
echo.

:: 列出生成的文件
if exist "dist" (
    echo 生成的文件:
    dir /b dist\*.exe
    echo.
)

echo 按任意键退出...
pause >nul

