@echo off
chcp 65001 >nul
echo ============================================================
echo 提猫直播助手 - 本地演示环境启动
echo ============================================================
echo.
echo 📌 端口配置：
echo    后端：8080
echo    前端：3000
echo.
echo 📌 启动方式：使用 Integrated Launcher
echo.

cd /d "%~dp0"

echo [1/2] 检查端口配置...
type server\.env | findstr "BACKEND_PORT"
echo.

echo [2/2] 启动所有服务...
echo.
npm run start:integrated

pause

