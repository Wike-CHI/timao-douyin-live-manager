@echo off
chcp 65001 >nul 2>&1

echo.
echo ========================================
echo    提猫直播助手 - 简化安装启动脚本
echo ========================================
echo.

:: 设置基本变量
set PROJECT_DIR=%~dp0
set PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
set NODE_URL=https://nodejs.org/dist/v22.17.0/node-v22.17.0-x64.msi
set TEMP_DIR=%TEMP%\timao_setup

echo [信息] 项目目录: %PROJECT_DIR%
echo [信息] 临时目录: %TEMP_DIR%
echo.

:: 检查项目结构
echo [验证] 检查项目结构...
if not exist "%PROJECT_DIR%package.json" (
    echo [错误] 未找到package.json文件
    pause
    exit /b 1
)
if not exist "%PROJECT_DIR%server" (
    echo [错误] 未找到server目录
    pause
    exit /b 1
)
if not exist "%PROJECT_DIR%electron" (
    echo [错误] 未找到electron目录
    pause
    exit /b 1
)
echo [成功] 项目结构验证通过
echo.

:: 创建临时目录
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

:: 检查Python
echo [步骤1] 检查Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [信息] Python未安装，开始下载安装...
    echo [下载] 正在下载Python 3.11.9...
    powershell -Command "Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%TEMP_DIR%\python-installer.exe'"
    if errorlevel 1 (
        echo [错误] Python下载失败
        pause
        exit /b 1
    )
    echo [安装] 正在安装Python...
    "%TEMP_DIR%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1
    timeout /t 30 /nobreak >nul
    echo [完成] Python安装完成
) else (
    echo [信息] Python已安装
)
echo.

:: 检查Node.js
echo [步骤2] 检查Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [信息] Node.js未安装，开始下载安装...
    echo [下载] 正在下载Node.js 22.17.0...
    powershell -Command "Invoke-WebRequest -Uri '%NODE_URL%' -OutFile '%TEMP_DIR%\node-installer.msi'"
    if errorlevel 1 (
        echo [错误] Node.js下载失败
        pause
        exit /b 1
    )
    echo [安装] 正在安装Node.js...
    msiexec /i "%TEMP_DIR%\node-installer.msi" /quiet /norestart
    timeout /t 45 /nobreak >nul
    echo [完成] Node.js安装完成
) else (
    echo [信息] Node.js已安装
)
echo.

:: 创建Python虚拟环境
echo [步骤3] 设置Python虚拟环境...
cd /d "%PROJECT_DIR%"
if not exist ".venv" (
    echo [创建] 正在创建虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
)
echo [激活] 激活虚拟环境...
call ".venv\Scripts\activate.bat"
echo [成功] 虚拟环境已激活
echo.

:: 安装Python依赖
echo [步骤4] 安装Python依赖...
if exist "requirements.txt" (
    echo [安装] 根目录Python依赖...
    pip install -r requirements.txt
)
if exist "server\requirements.txt" (
    echo [安装] server目录Python依赖...
    cd server
    pip install -r requirements.txt
    cd ..
)
echo [完成] Python依赖安装完成
echo.

:: 安装Node.js依赖
echo [步骤5] 安装Node.js依赖...
echo [安装] 根目录Node.js依赖...
npm install
if errorlevel 1 (
    echo [错误] 根目录依赖安装失败
    pause
    exit /b 1
)

if exist "electron\package.json" (
    echo [安装] electron目录依赖...
    cd electron
    npm install
    cd ..
)

if exist "electron\renderer\package.json" (
    echo [安装] electron\renderer目录依赖...
    cd electron\renderer
    npm install
    cd ..
    cd ..
)
echo [完成] Node.js依赖安装完成
echo.

:: 启动应用
echo [步骤6] 启动应用...
echo [启动] 后端服务器...
start "后端服务器" cmd /k "call "%PROJECT_DIR%.venv\Scripts\activate.bat" && cd /d "%PROJECT_DIR%server" && python app.py"

echo [等待] 等待后端启动...
timeout /t 5 /nobreak >nul

echo [启动] 前端开发服务器...
cd electron\renderer
start "前端服务器" cmd /k "npm run dev"

echo [等待] 等待前端启动...
timeout /t 8 /nobreak >nul

echo [启动] Electron应用...
cd ..
start "Electron应用" cmd /k "npm start"

echo.
echo ========================================
echo           启动完成！
echo ========================================
echo [成功] 提猫直播助手已启动！
echo.
echo [服务状态]
echo - 后端服务器: 已启动
echo - 前端开发服务器: 已启动  
echo - Electron桌面应用: 已启动
echo.
echo [提示] 按任意键退出安装脚本...
pause
exit /b 0