@echo off
echo 提猫直播助手 - 用户注册测试
echo ================================

cd /d D:\gsxm\timao-douyin-live-manager

echo 启动后端服务...
start "后端服务" /min cmd /c "python -m server.app.main"

timeout /t 10 /nobreak >nul

echo 运行注册测试...
python test_auth.py

echo.
echo 测试完成!
pause