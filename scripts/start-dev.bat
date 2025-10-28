@echo off
chcp 65001 >nul
echo 🚀 提猫直播助手 - 开发环境启动脚本
echo =====================================
echo.

echo 📋 启动顺序:
echo 1. 后端 FastAPI 服务 (端口 9019)
echo 2. 前端 Vite 开发服务器 (端口 10030)  
echo 3. Electron 应用
echo.

echo ⚙️  检查依赖...
if not exist "node_modules" (
    echo ❌ 未找到 node_modules，请先运行 npm install
    pause
    exit /b 1
)

if not exist "server\app" (
    echo ❌ 未找到后端代码，请检查项目结构
    pause
    exit /b 1
)

echo ✅ 依赖检查完成
echo.

echo 🔄 启动开发环境...
echo 提示: 使用 Ctrl+C 可以停止所有服务
echo.

rem 使用 npm run quick:start 启动所有服务
npm run quick:start

echo.
echo 👋 开发环境已停止
pause