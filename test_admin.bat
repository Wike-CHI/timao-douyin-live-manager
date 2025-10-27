@echo off
cd /d d:\gsxm\timao-douyin-live-manager
echo 测试管理员模块导入...
python -c "from server.app.api import admin; print('SUCCESS: admin module imported'); print('Router prefix:', admin.router.prefix); print('Router tags:', admin.router.tags)"
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ 管理员模块导入测试通过!
) else (
    echo.
    echo ❌ 管理员模块导入失败!
)
pause