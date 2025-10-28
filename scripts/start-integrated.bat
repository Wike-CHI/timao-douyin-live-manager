@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ========================================
echo 提猫直播助手 - 一体化启动器
echo ========================================
echo.

:: 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 Node.js
    echo 请先安装 Node.js: https://nodejs.org/
    pause
    exit /b 1
)

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 Python
    echo 请先安装 Python: https://python.org/
    pause
    exit /b 1
)

:: 切换到项目根目录
cd /d "%~dp0.."

:: 检查必要文件
if not exist "package.json" (
    echo ❌ 错误: 未找到 package.json
    echo 请确保在项目根目录运行此脚本
    pause
    exit /b 1
)

if not exist "scripts\integrated-launcher.js" (
    echo ❌ 错误: 未找到启动器脚本
    echo 请确保 scripts\integrated-launcher.js 存在
    pause
    exit /b 1
)

echo ✅ 环境检查通过
echo.

:: 解析命令行参数
set "COMMAND=start"
if not "%1"=="" set "COMMAND=%1"

echo 🚀 执行命令: %COMMAND%
echo.

:: 执行启动器
node scripts/integrated-launcher.js %COMMAND%

:: 检查执行结果
if errorlevel 1 (
    echo.
    echo ❌ 启动器执行失败
    echo.
    echo 💡 故障排除建议:
    echo    1. 检查端口占用: npm run port:check
    echo    2. 清理端口占用: npm run port:clean
    echo    3. 检查环境配置: npm run env:check
    echo    4. 查看帮助信息: npm run launcher:help
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ 启动器执行完成
pause