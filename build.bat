@echo off
echo 开始构建提猫直播助手 Windows 安装包...
echo.

REM 检查 Node.js 环境
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Node.js，请先安装 Node.js
    pause
    exit /b 1
)

REM 检查 npm 依赖
echo 检查依赖包...
npm list electron-builder >nul 2>&1
if errorlevel 1 (
    echo 安装依赖包...
    npm install
)

REM 清理之前的构建
echo 清理之前的构建文件...
if exist dist rmdir /s /q dist

REM 开始构建
echo 开始构建 Windows 安装包...
npm run build -- --win

if errorlevel 1 (
    echo 构建失败！
    pause
    exit /b 1
) else (
    echo.
    echo 构建成功！
    echo 安装包位置: dist\
    echo.
    dir dist\*.exe
    echo.
    echo 按任意键退出...
    pause >nul
)