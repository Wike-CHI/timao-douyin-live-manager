@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 快速打包脚本 - 跳过依赖安装
echo ========================================
echo 提猫直播助手 - Windows快速打包脚本
echo (跳过依赖安装)
echo ========================================
echo.

cd /d "%~dp0..\.."

:: 清理旧构建
echo [1/3] 清理旧的构建文件...
if exist "dist" rd /s /q "dist"
if exist "electron\renderer\dist" rd /s /q "electron\renderer\dist"
echo.

:: 构建前端
echo [2/3] 构建前端应用...
cd electron\renderer
call npm run build
if %errorlevel% neq 0 (
    echo [错误] 构建前端失败
    pause
    exit /b 1
)
cd ..\..
echo.

:: 打包
echo [3/3] 打包Electron应用...
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

if exist "dist" (
    echo 生成的文件:
    dir /b dist\*.exe
    echo.
)

pause

