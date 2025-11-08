@echo off
REM Windows 11 快速打包脚本
REM 使用方法: 双击运行或在命令行执行 build-local.bat

echo ========================================
echo   Windows 11 Electron 应用打包脚本
echo ========================================
echo.

REM 设置环境变量（通过Nginx反向代理，使用80端口）
set VITE_FASTAPI_URL=http://129.211.218.135
set VITE_STREAMCAP_URL=http://129.211.218.135
set VITE_DOUYIN_URL=http://129.211.218.135
set ELECTRON_START_API=false

echo [1/4] 安装根目录依赖...
call npm install
if errorlevel 1 (
    echo ❌ 安装根目录依赖失败！
    pause
    exit /b 1
)

echo.
echo [2/4] 安装前端依赖...
cd electron\renderer
call npm install
if errorlevel 1 (
    echo ❌ 安装前端依赖失败！
    cd ..\..
    pause
    exit /b 1
)
cd ..\..

echo.
echo [3/4] 构建前端...
cd electron\renderer
call npm run build
if errorlevel 1 (
    echo ❌ 构建前端失败！
    cd ..\..
    pause
    exit /b 1
)
cd ..\..

echo.
echo [4/4] 打包Electron应用...
call npm run build:win
if errorlevel 1 (
    echo ❌ 打包Electron应用失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ 打包完成！
echo ========================================
echo.
echo 📁 安装包位置: dist\TalkingCat-Portable-*.exe
echo.
echo 按任意键退出...
pause >nul

