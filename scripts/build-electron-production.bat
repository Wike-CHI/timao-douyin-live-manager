@echo off
REM ============================================================================
REM 提猫直播助手 - Electron应用生产环境打包脚本 (Windows版本)
REM 
REM 功能：构建连接到公网后端的Electron桌面应用
REM 后端地址：http://129.211.218.135
REM 
REM 使用方法：
REM   双击运行此文件
REM   或在命令行中: build-electron-production.bat
REM
REM 作者：提猫直播助手团队
REM 日期：2025-11-13
REM ============================================================================

setlocal enabledelayedexpansion

REM 设置UTF-8编码
chcp 65001 > nul

REM 获取项目根目录
cd /d %~dp0..
set PROJECT_ROOT=%CD%
set ELECTRON_DIR=%PROJECT_ROOT%\electron
set RENDERER_DIR=%ELECTRON_DIR%\renderer
set BUILD_DIR=%PROJECT_ROOT%\dist

REM 生产环境API配置
set PRODUCTION_API_URL=http://129.211.218.135

echo ========================================================================
echo 提猫直播助手 - Electron应用打包
echo ========================================================================
echo.

REM ============================================================================
REM 步骤1：环境检查
REM ============================================================================

echo [1/7] 环境检查...
echo.

REM 检查Node.js
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js 未安装！请先安装 Node.js
    pause
    exit /b 1
)
node -v
echo Node.js 已安装

REM 检查npm
where npm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] npm 未安装！
    pause
    exit /b 1
)
npm -v
echo npm 已安装
echo.

REM ============================================================================
REM 步骤2：清理旧构建
REM ============================================================================

echo [2/7] 清理旧构建...
echo.

if exist "%BUILD_DIR%" (
    echo 删除旧的 dist 目录...
    rd /s /q "%BUILD_DIR%"
)

if exist "%RENDERER_DIR%\dist" (
    echo 删除旧的前端构建...
    rd /s /q "%RENDERER_DIR%\dist"
)

echo 清理完成
echo.

REM ============================================================================
REM 步骤3：创建生产环境配置
REM ============================================================================

echo [3/7] 配置生产环境...
echo.

echo 创建环境配置文件: %RENDERER_DIR%\.env.production
(
    echo # 生产环境配置 - 连接到公网后端
    echo # 生成时间: %date% %time%
    echo.
    echo # API基础URL（公网地址）
    echo VITE_FASTAPI_URL=%PRODUCTION_API_URL%
    echo VITE_STREAMCAP_URL=%PRODUCTION_API_URL%
    echo VITE_DOUYIN_URL=%PRODUCTION_API_URL%
    echo.
    echo # 环境标识
    echo VITE_APP_ENV=production
    echo.
    echo # 构建信息
    echo VITE_BUILD_TIME=%date%-%time%
    echo VITE_BUILD_VERSION=1.0.0
) > "%RENDERER_DIR%\.env.production"

echo 后端API地址: %PRODUCTION_API_URL%
echo 配置完成
echo.

REM ============================================================================
REM 步骤4：安装依赖
REM ============================================================================

echo [4/7] 安装依赖...
echo.

REM 安装根目录依赖
echo 安装项目根目录依赖...
cd /d "%PROJECT_ROOT%"
if exist "package.json" (
    call npm install
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] 根目录依赖安装失败
        pause
        exit /b 1
    )
)

REM 安装Electron依赖
echo 安装Electron依赖...
cd /d "%ELECTRON_DIR%"
call npm install
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Electron依赖安装失败
    pause
    exit /b 1
)

REM 安装前端依赖
echo 安装前端依赖...
cd /d "%RENDERER_DIR%"
call npm install
if %ERRORLEVEL% neq 0 (
    echo [ERROR] 前端依赖安装失败
    pause
    exit /b 1
)

echo 依赖安装完成
echo.

REM ============================================================================
REM 步骤5：构建前端
REM ============================================================================

echo [5/7] 构建前端...
echo.

cd /d "%RENDERER_DIR%"
echo 构建命令: npm run build
call npm run build
if %ERRORLEVEL% neq 0 (
    echo [ERROR] 前端构建失败
    pause
    exit /b 1
)

if not exist "%RENDERER_DIR%\dist" (
    echo [ERROR] 前端构建产物不存在
    pause
    exit /b 1
)

echo 前端构建成功
echo.

REM ============================================================================
REM 步骤6：打包Electron应用
REM ============================================================================

echo [6/7] 打包Electron应用...
echo.

cd /d "%PROJECT_ROOT%"

REM 设置electron-builder环境变量（国内镜像加速）
set ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
set ELECTRON_BUILDER_BINARIES_MIRROR=https://npmmirror.com/mirrors/electron-builder-binaries/

echo 打包Windows x64版本...
call npm run build:win64
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Electron打包失败
    pause
    exit /b 1
)

echo Electron打包成功
echo.

REM ============================================================================
REM 步骤7：验证结果
REM ============================================================================

echo [7/7] 验证打包结果...
echo.

if not exist "%BUILD_DIR%" (
    echo [ERROR] 打包产物目录不存在
    pause
    exit /b 1
)

echo 打包产物目录: %BUILD_DIR%
echo.
echo 目录内容:
dir /b "%BUILD_DIR%\*.exe" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [WARNING] 未找到.exe文件
    dir /b "%BUILD_DIR%"
)

echo.

REM ============================================================================
REM 完成
REM ============================================================================

echo ========================================================================
echo 打包完成！
echo ========================================================================
echo.
echo 📦 打包摘要:
echo   - 后端地址: %PRODUCTION_API_URL%
echo   - 产物目录: %BUILD_DIR%
echo.
echo 🚀 下一步操作:
echo   1. 进入 dist 目录查看安装包
echo   2. 双击运行 TalkingCat-Portable-*.exe（便携版）
echo   3. 或安装 TalkingCat-Setup-*.exe（安装版）
echo   4. 测试应用连接到后端
echo.
echo 📝 测试连接:
echo   打开应用后访问: http://129.211.218.135/health
echo   应该能看到服务状态信息
echo.
echo ========================================================================
echo 🎉 所有步骤完成！
echo ========================================================================
echo.

pause
exit /b 0

