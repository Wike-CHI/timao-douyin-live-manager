@echo off
echo 开始构建提猫直播助手 Windows 便携版...
echo.

REM 设置环境变量禁用代码签名
set CSC_IDENTITY_AUTO_DISCOVERY=false
set ELECTRON_BUILDER_ALLOW_UNRESOLVED_DEPENDENCIES=true

REM 检查 Node.js 环境
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Node.js，请先安装 Node.js
    pause
    exit /b 1
)

REM 清理缓存
echo 清理构建缓存...
if exist dist rmdir /s /q dist
if exist "%LOCALAPPDATA%\electron-builder\Cache" rmdir /s /q "%LOCALAPPDATA%\electron-builder\Cache"

REM 开始构建便携版
echo 开始构建 Windows 便携版应用...
npx electron-builder --win --x64 --config.win.target=portable --config.win.artifactName="TalkingCat-Portable-${version}-${arch}.exe"

if errorlevel 1 (
    echo 构建失败！
    pause
    exit /b 1
) else (
    echo.
    echo 构建成功！
    echo 便携版应用位置: dist\
    echo.
    dir dist\*.exe
    echo.
    echo 按任意键退出...
    pause >nul
)