@echo off
chcp 65001 >nul
echo ====================================
echo 提猫直播助手 - 管理后台
echo ====================================
echo.

if not exist "node_modules" (
    echo [1/2] 正在安装依赖...
    call npm install
    if errorlevel 1 (
        echo 依赖安装失败！
        pause
        exit /b 1
    )
    echo 依赖安装完成！
    echo.
)

echo [2/2] 启动开发服务器...
echo 访问地址: http://localhost:10050
echo.
call npm run dev

pause

