@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 设置脚本标题和颜色
title 提猫直播助手 - 自动化安装与启动脚本
color 0A

echo.
echo ========================================
echo    提猫直播助手 - 自动化安装与启动脚本
echo ========================================
echo.

:: 设置变量
set "PYTHON_VERSION=3.11.9"
set "NODE_VERSION=22.17.0"
set "PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
set "NODE_URL=https://nodejs.org/dist/v22.17.0/node-v22.17.0-x64.msi"
set "TEMP_DIR=%TEMP%\timao_setup"
set "PROJECT_DIR=%~dp0"

:: 创建临时目录
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

echo [信息] 开始环境检测和安装流程...
echo.

:: ========================================
:: 第一步：检测和安装Python 3.11.9
:: ========================================
echo [步骤1] 检测Python环境...

:: 检查Python是否已安装
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "CURRENT_PYTHON=%%i"
    echo [信息] 检测到Python版本: !CURRENT_PYTHON!
    
    :: 检查是否为目标版本
    if "!CURRENT_PYTHON!"=="!PYTHON_VERSION!" (
        echo [成功] Python 3.11.9 已安装
        set "PYTHON_OK=1"
    ) else (
        echo [警告] Python版本不匹配，需要安装Python 3.11.9
        set "PYTHON_OK=0"
    )
) else (
    echo [信息] 未检测到Python，需要安装Python 3.11.9
    set "PYTHON_OK=0"
)

:: 如果Python不符合要求，则下载安装
if "!PYTHON_OK!"=="0" (
    echo.
    echo [步骤1.1] 下载Python 3.11.9...
    
    :: 使用PowerShell下载Python安装包
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%TEMP_DIR%\python-installer.exe'}"
    
    if exist "%TEMP_DIR%\python-installer.exe" (
        echo [成功] Python安装包下载完成
        
        echo [步骤1.2] 安装Python 3.11.9...
        echo [信息] 正在静默安装Python，请稍候...
        
        :: 静默安装Python，添加到PATH
        "%TEMP_DIR%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        
        :: 等待安装完成
        timeout /t 30 /nobreak >nul
        
        :: 刷新环境变量
        call :refresh_env
        
        :: 验证安装
        python --version >nul 2>&1
        if !errorlevel! equ 0 (
            echo [成功] Python 3.11.9 安装完成
        ) else (
            echo [错误] Python安装失败，请手动安装
            pause
            exit /b 1
        )
    ) else (
        echo [错误] Python下载失败，请检查网络连接
        pause
        exit /b 1
    )
)

echo.

:: ========================================
:: 第二步：检测和安装Node.js 22.17.0
:: ========================================
echo [步骤2] 检测Node.js环境...

:: 检查Node.js是否已安装
node --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=1" %%i in ('node --version 2^>^&1') do set "CURRENT_NODE=%%i"
    set "CURRENT_NODE=!CURRENT_NODE:v=!"
    echo [信息] 检测到Node.js版本: !CURRENT_NODE!
    
    :: 检查是否为目标版本
    if "!CURRENT_NODE!"=="!NODE_VERSION!" (
        echo [成功] Node.js 22.17.0 已安装
        set "NODE_OK=1"
    ) else (
        echo [警告] Node.js版本不匹配，需要安装Node.js 22.17.0
        set "NODE_OK=0"
    )
) else (
    echo [信息] 未检测到Node.js，需要安装Node.js 22.17.0
    set "NODE_OK=0"
)

:: 如果Node.js不符合要求，则下载安装
if "!NODE_OK!"=="0" (
    echo.
    echo [步骤2.1] 下载Node.js 22.17.0...
    
    :: 使用PowerShell下载Node.js安装包
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%NODE_URL%' -OutFile '%TEMP_DIR%\node-installer.msi'}"
    
    if exist "%TEMP_DIR%\node-installer.msi" (
        echo [成功] Node.js安装包下载完成
        
        echo [步骤2.2] 安装Node.js 22.17.0...
        echo [信息] 正在静默安装Node.js，请稍候...
        
        :: 静默安装Node.js
        msiexec /i "%TEMP_DIR%\node-installer.msi" /quiet /norestart
        
        :: 等待安装完成
        timeout /t 30 /nobreak >nul
        
        :: 刷新环境变量
        call :refresh_env
        
        :: 验证安装
        node --version >nul 2>&1
        if !errorlevel! equ 0 (
            echo [成功] Node.js 22.17.0 安装完成
        ) else (
            echo [错误] Node.js安装失败，请手动安装
            pause
            exit /b 1
        )
    ) else (
        echo [错误] Node.js下载失败，请检查网络连接
        pause
        exit /b 1
    )
)

echo.

:: ========================================
:: 第三步：创建和管理Python虚拟环境
:: ========================================
echo [步骤3] 创建和管理Python虚拟环境...

:: 回到项目根目录
cd /d "%PROJECT_DIR%"

:: 检查是否已存在虚拟环境
if exist "%PROJECT_DIR%.venv" (
    echo [信息] 检测到已存在的虚拟环境 .venv
    
    :: 检查虚拟环境是否完整
    if exist "%PROJECT_DIR%.venv\Scripts\python.exe" (
        echo [成功] 虚拟环境完整，将使用现有环境
        set "VENV_EXISTS=1"
    ) else (
        echo [警告] 虚拟环境不完整，将重新创建
        rd /s /q "%PROJECT_DIR%.venv" >nul 2>&1
        set "VENV_EXISTS=0"
    )
) else (
    echo [信息] 未检测到虚拟环境，将创建新的虚拟环境
    set "VENV_EXISTS=0"
)

:: 如果虚拟环境不存在或不完整，则创建新的
if "!VENV_EXISTS!"=="0" (
    echo [步骤3.1] 创建Python虚拟环境...
    
    :: 创建虚拟环境
    python -m venv .venv
    
    if !errorlevel! equ 0 (
        echo [成功] 虚拟环境创建完成
    ) else (
        echo [错误] 虚拟环境创建失败
        pause
        exit /b 1
    )
)

:: 激活虚拟环境
echo [步骤3.2] 激活虚拟环境...
call "%PROJECT_DIR%.venv\Scripts\activate.bat"

if !errorlevel! equ 0 (
    echo [成功] 虚拟环境已激活
) else (
    echo [错误] 虚拟环境激活失败
    pause
    exit /b 1
)

:: 升级pip到最新版本
echo [步骤3.3] 升级pip到最新版本...
python -m pip install --upgrade pip

:: ========================================
:: 第四步：在虚拟环境中安装Python依赖
:: ========================================
echo [步骤4] 在虚拟环境中安装Python依赖包...

:: 定义需要安装依赖的目录列表
set "PYTHON_DIRS=. server AST_module StreamCap DouyinLiveWebFetcher"

for %%d in (%PYTHON_DIRS%) do (
    if exist "%PROJECT_DIR%%%d\requirements.txt" (
        echo [步骤4.%%d] 安装 %%d 目录的Python依赖...
        cd /d "%PROJECT_DIR%%%d"
        
        :: 在虚拟环境中使用pip安装依赖
        python -m pip install -r requirements.txt --upgrade
        
        if !errorlevel! equ 0 (
            echo [成功] %%d 目录依赖安装完成
        ) else (
            echo [警告] %%d 目录依赖安装可能存在问题，但继续执行
        )
        
        cd /d "%PROJECT_DIR%"
    ) else (
        echo [信息] %%d 目录不存在requirements.txt，跳过
    )
)

echo.

:: ========================================
:: 第五步：安装Node.js依赖
:: ========================================
echo [步骤5] 安装Node.js依赖包...

:: 定义需要安装依赖的目录列表
set "NODE_DIRS=. electron electron\renderer"

for %%d in (%NODE_DIRS%) do (
    if exist "%PROJECT_DIR%%%d\package.json" (
        echo [步骤5.%%d] 安装 %%d 目录的Node.js依赖...
        cd /d "%PROJECT_DIR%%%d"
        
        :: 使用npm安装依赖
        npm install
        
        if !errorlevel! equ 0 (
            echo [成功] %%d 目录依赖安装完成
        ) else (
            echo [警告] %%d 目录依赖安装可能存在问题，但继续执行
        )
        
        cd /d "%PROJECT_DIR%"
    ) else (
        echo [信息] %%d 目录不存在package.json，跳过
    )
)

echo.

:: ========================================
:: 第六步：启动应用程序
:: ========================================
echo [步骤6] 启动应用程序...
echo.

echo [信息] 即将启动三个组件：
echo   1. 后端服务器 (端口: 9019)
echo   2. 前端开发服务器 (端口: 10030)
echo   3. Electron桌面应用
echo.

:: 启动后端服务器（在虚拟环境中）
echo [步骤6.1] 启动后端服务器...
cd /d "%PROJECT_DIR%server"
start "提猫直播助手-后端服务" cmd /k "call "%PROJECT_DIR%.venv\Scripts\activate.bat" && python -m uvicorn app.main:app --host 0.0.0.0 --port 9019 --reload"

:: 等待后端启动
timeout /t 5 /nobreak >nul

:: 启动前端开发服务器
echo [步骤6.2] 启动前端开发服务器...
cd /d "%PROJECT_DIR%electron\renderer"
start "提猫直播助手-前端服务" cmd /k "npm run dev"

:: 等待前端启动
timeout /t 8 /nobreak >nul

:: 启动Electron应用
echo [步骤6.3] 启动Electron桌面应用...
cd /d "%PROJECT_DIR%"
start "提猫直播助手-桌面应用" cmd /k "npm run dev:electron"

echo.
echo ========================================
echo           启动完成！
echo ========================================
echo.
echo [成功] 所有组件已启动：
echo   • 后端服务: http://localhost:9019
echo   • 前端服务: http://127.0.0.1:10030
echo   • 桌面应用: Electron窗口
echo.
echo [提示] 如需停止服务，请关闭对应的命令行窗口
echo [提示] 首次启动可能需要较长时间，请耐心等待
echo.

:: 清理临时文件
if exist "%TEMP_DIR%" (
    echo [信息] 清理临时文件...
    rd /s /q "%TEMP_DIR%" >nul 2>&1
)

echo 按任意键退出...
pause >nul
exit /b 0

:: ========================================
:: 辅助函数：刷新环境变量
:: ========================================
:refresh_env
:: 通过重新读取注册表来刷新PATH环境变量
for /f "skip=2 tokens=3*" %%a in ('reg query HKLM\SYSTEM\CurrentControlSet\Control\Session" Manager\Environment" /v PATH') do set "SYS_PATH=%%a %%b"
for /f "skip=2 tokens=3*" %%a in ('reg query HKCU\Environment /v PATH 2^>nul') do set "USER_PATH=%%a %%b"
set "PATH=%SYS_PATH%;%USER_PATH%"
goto :eof