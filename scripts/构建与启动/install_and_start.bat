@echo off
chcp 65001 >nul
title 提猫直播助手 - 一站式安装启动器

echo ========================================
echo 提猫直播助手 - 一站式安装启动器
echo ========================================
echo.

REM 设置项目根目录
cd /d "%~dp0"
set PROJECT_ROOT=%CD%

echo 🚀 开始安装和配置环境...
echo.

REM ========================================
REM 1. 检查Python环境
REM ========================================
echo 📋 步骤 1/6: 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python
    echo 请先从 https://www.python.org/downloads/ 下载并安装Python 3.8+
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

REM 获取Python版本
python --version 2>nul
if %errorlevel% equ 0 (
    echo ✅ Python已安装
) else (
    echo ❌ 错误: 未找到Python
    echo 请先从 https://www.python.org/downloads/ 下载并安装Python 3.8+
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
echo.

REM ========================================
REM 2. 创建和激活虚拟环境
REM ========================================
echo 📋 步骤 2/6: 配置Python虚拟环境
if not exist ".venv" (
    echo 🔧 创建Python虚拟环境...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo ❌ 错误: 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
) else (
    echo ✅ 虚拟环境已存在
)

REM 激活虚拟环境
echo 🔧 激活虚拟环境...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ 错误: 虚拟环境激活失败
    pause
    exit /b 1
)
echo ✅ 虚拟环境激活成功
echo.

REM ========================================
REM 3. 安装Python依赖
REM ========================================
echo 📋 步骤 3/6: 安装Python依赖
if exist "requirements.txt" (
    echo 🔧 安装Python依赖包...
    pip install --upgrade pip
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ 错误: Python依赖安装失败
        echo 请检查网络连接或尝试使用国内镜像源
        echo 命令: pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
        pause
        exit /b 1
    )
    echo ✅ Python依赖安装成功
) else (
    echo ⚠️  警告: 未找到requirements.txt文件
)
echo.

REM ========================================
REM 4. 检查Node.js环境
REM ========================================
echo 📋 步骤 4/6: 检查Node.js环境
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Node.js
    echo 请先从 https://nodejs.org/ 下载并安装Node.js LTS版本
    echo.
    pause
    exit /b 1
)

REM 获取Node.js版本
for /f "tokens=1" %%i in ('node --version 2^>^&1') do set NODE_VERSION=%%i
echo ✅ Node.js版本: %NODE_VERSION%

npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到npm
    echo 请确保Node.js已正确安装（包含npm）
    pause
    exit /b 1
)

for /f "tokens=1" %%i in ('npm --version 2^>^&1') do set NPM_VERSION=%%i
echo ✅ npm版本: %NPM_VERSION%
echo.

REM ========================================
REM 5. 安装Node.js依赖
REM ========================================
echo 📋 步骤 5/6: 安装Node.js依赖
if exist "package.json" (
    echo 🔧 安装项目依赖...
    npm install
    if %errorlevel% neq 0 (
        echo ❌ 错误: 项目依赖安装失败
        echo 尝试清理缓存后重新安装...
        npm cache clean --force
        npm install
        if %errorlevel% neq 0 (
            echo ❌ 错误: 依赖安装仍然失败
            pause
            exit /b 1
        )
    )
    echo ✅ 项目依赖安装成功
) else (
    echo ⚠️  警告: 未找到package.json文件
)

REM 安装前端依赖
if exist "electron\renderer\package.json" (
    echo 🔧 安装前端依赖...
    cd electron\renderer
    npm install
    if %errorlevel% neq 0 (
        echo ❌ 错误: 前端依赖安装失败
        cd "%PROJECT_ROOT%"
        pause
        exit /b 1
    )
    cd "%PROJECT_ROOT%"
    echo ✅ 前端依赖安装成功
)
echo.

REM ========================================
REM 6. 启动应用
REM ========================================
echo 📋 步骤 6/6: 启动应用
echo.
echo 🎉 环境配置完成！正在启动应用...
echo.
echo 📝 启动信息:
echo    - 后端服务: http://127.0.0.1:9019
echo    - 前端开发服务器: http://127.0.0.1:10030
echo    - 健康检查: http://127.0.0.1:9019/health
echo.
echo 🔄 启动中，请稍候...
echo.

REM 启动开发环境
npm run dev

REM 如果启动失败，显示错误信息
if %errorlevel% neq 0 (
    echo.
    echo ❌ 应用启动失败
    echo.
    echo 🔍 故障排除建议:
    echo 1. 检查端口是否被占用 (9019, 9020, 9021, 10030)
    echo 2. 检查防火墙设置
    echo 3. 查看错误日志
    echo 4. 尝试手动启动: npm run dev
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ 应用启动成功！
echo 💡 按 Ctrl+C 停止应用
pause