@echo off
chcp 65001 >nul
echo ========================================
echo 以管理员身份启动本地演示环境
echo ========================================
echo.

REM 检查是否以管理员身份运行
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ 需要管理员权限！
    echo.
    echo 正在请求管理员权限...
    echo 请在UAC对话框中选择"是"
    echo.
    
    REM 请求管理员权限并重新运行脚本
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d %CD% && %~f0 admin' -Verb RunAs"
    exit /b
)

if "%1"=="admin" (
    echo ✅ 已获得管理员权限
    echo.
    
    echo [1/3] 清理端口...
    call npm run kill:ports
    echo.
    
    echo [2/3] 验证配置...
    type server\.env | findstr "BACKEND_PORT"
    echo.
    
    echo [3/3] 启动服务...
    echo 提示：按 Ctrl+C 停止所有服务
    echo.
    call npm run dev
    
    echo.
    echo 服务已停止。按任意键关闭窗口...
    pause >nul
)

