@echo off
echo 正在启动提猫直播助手开发环境...
echo.

REM 检查虚拟环境是否存在
if not exist ".venv\Scripts\activate.bat" (
    echo 错误：虚拟环境不存在，请先创建虚拟环境
    echo 运行命令：python -m venv .venv
    pause
    exit /b 1
)

REM 激活虚拟环境
echo 激活Python虚拟环境...
call .venv\Scripts\activate.bat

REM 检查npm是否可用
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误：npm未找到，请确保Node.js已安装
    pause
    exit /b 1
)

REM 检查package.json是否存在
if not exist "package.json" (
    echo 错误：package.json文件不存在
    pause
    exit /b 1
)

REM 运行npm dev
echo 启动开发服务器...
npm run dev

REM 如果npm命令失败，暂停以查看错误信息
if %errorlevel% neq 0 (
    echo.
    echo 启动失败，请检查错误信息
    pause
)