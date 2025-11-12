@echo off
:: 设置UTF-8代码页，确保中文显示正常
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

:: 设置控制台属性以优化中文显示
mode con cols=120 lines=50
:: 设置脚本标题和颜色
title 提猫直播助手 - 自动化安装与启动脚本
color 0A

:: 添加错误处理
set "DEBUG_MODE=0"
if "%DEBUG_MODE%"=="1" (
    echo [调试] 启用调试模式，将显示详细执行信息
)

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

:: 调试信息
if "%DEBUG_MODE%"=="1" (
    echo [调试] 项目目录: %PROJECT_DIR%
    echo [调试] 临时目录: %TEMP_DIR%
    echo [调试] Python版本: %PYTHON_VERSION%
    echo [调试] Node.js版本: %NODE_VERSION%
    echo.
)

:: 验证项目目录结构
echo [验证] 检查项目目录结构...
if not exist "%PROJECT_DIR%package.json" (
    echo [错误] 未找到package.json文件，请确认脚本在项目根目录中运行
    echo [错误] 当前目录: %PROJECT_DIR%
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)

if not exist "%PROJECT_DIR%server" (
    echo [错误] 未找到server目录，请确认项目结构完整
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)

if not exist "%PROJECT_DIR%electron" (
    echo [错误] 未找到electron目录，请确认项目结构完整
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)

if not exist "%PROJECT_DIR%electron\renderer" (
    echo [错误] 未找到electron\renderer目录，请确认项目结构完整
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)

echo [成功] 项目目录结构验证通过
echo.

:: 创建临时目录
if not exist "%TEMP_DIR%" (
    mkdir "%TEMP_DIR%"
    if !errorlevel! neq 0 (
        echo [错误] 无法创建临时目录: %TEMP_DIR%
        echo [提示] 按任意键退出...
        pause >nul
        exit /b 1
    )
)

echo [信息] 开始环境检测和安装流程...
if "%DEBUG_MODE%"=="1" (
    echo [调试] 按任意键继续...
    pause >nul
)
echo.

:: ========================================
:: 第一步：检测和安装Python 3.11.9
:: ========================================
echo [步骤1] 检测Python环境...

:: 检测Python是否已安装
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "CURRENT_PYTHON=%%v"
    echo [信息] 检测到Python版本: !CURRENT_PYTHON!
    
    :: 检查是否为目标版本
    echo !CURRENT_PYTHON! | findstr /C:"%PYTHON_VERSION%" >nul
    if !errorlevel! equ 0 (
        echo [成功] Python %PYTHON_VERSION% 已安装
        goto :check_node
    ) else (
        echo [警告] Python版本不匹配，需要安装 %PYTHON_VERSION%
    )
) else (
    echo [信息] 未检测到Python，需要安装
)

:: 下载并安装Python
echo [步骤1.1] 下载Python %PYTHON_VERSION%...
if not exist "%TEMP_DIR%\python-installer.exe" (
    echo [信息] 正在下载Python安装包...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%TEMP_DIR%\python-installer.exe'}"
    
    if !errorlevel! neq 0 (
        echo [错误] Python下载失败，请检查网络连接
        echo [提示] 按任意键退出...
        pause >nul
        exit /b 1
    )
    echo [成功] Python下载完成
) else (
    echo [信息] Python安装包已存在，跳过下载
)

echo [步骤1.2] 安装Python %PYTHON_VERSION%...
echo [信息] 正在静默安装Python，请稍候...
"%TEMP_DIR%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

:: 等待安装完成
timeout /t 30 /nobreak >nul

:: 刷新环境变量
call :refresh_env

:: 验证安装
echo [验证] 检查Python安装结果...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "INSTALLED_PYTHON=%%v"
    echo [成功] Python安装完成，版本: !INSTALLED_PYTHON!
) else (
    echo [错误] Python安装失败，请手动安装
    echo [提示] 请检查网络连接或手动下载安装包
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)

if "%DEBUG_MODE%"=="1" (
    echo [调试] Python安装步骤完成，按任意键继续...
    pause >nul
)

:check_node
:: ========================================
:: 第二步：检测和安装Node.js 22.17.0
:: ========================================
echo.
echo [步骤2] 检测Node.js环境...

:: 检测Node.js是否已安装
node --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=1" %%v in ('node --version 2^>^&1') do set "CURRENT_NODE=%%v"
    echo [信息] 检测到Node.js版本: !CURRENT_NODE!
    
    :: 检查是否为目标版本
    echo !CURRENT_NODE! | findstr /C:"v%NODE_VERSION%" >nul
    if !errorlevel! equ 0 (
        echo [成功] Node.js v%NODE_VERSION% 已安装
        goto :setup_venv
    ) else (
        echo [警告] Node.js版本不匹配，需要安装 v%NODE_VERSION%
    )
) else (
    echo [信息] 未检测到Node.js，需要安装
)

:: 下载并安装Node.js
echo [步骤2.1] 下载Node.js v%NODE_VERSION%...
if not exist "%TEMP_DIR%\node-installer.msi" (
    echo [信息] 正在下载Node.js安装包...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%NODE_URL%' -OutFile '%TEMP_DIR%\node-installer.msi'}"
    
    if !errorlevel! neq 0 (
        echo [错误] Node.js下载失败，请检查网络连接
        echo [提示] 按任意键退出...
        pause >nul
        exit /b 1
    )
    echo [成功] Node.js下载完成
) else (
    echo [信息] Node.js安装包已存在，跳过下载
)

echo [步骤2.2] 安装Node.js v%NODE_VERSION%...
echo [信息] 正在静默安装Node.js，请稍候...
msiexec /i "%TEMP_DIR%\node-installer.msi" /quiet /norestart

:: 等待安装完成
timeout /t 45 /nobreak >nul

:: 刷新环境变量
call :refresh_env

:: 验证安装
echo [验证] 检查Node.js安装结果...
node --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=1" %%v in ('node --version 2^>^&1') do set "INSTALLED_NODE=%%v"
    echo [成功] Node.js安装完成，版本: !INSTALLED_NODE!
) else (
    echo [错误] Node.js安装失败，请手动安装
    echo [提示] 请检查网络连接或手动下载安装包
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)

if "%DEBUG_MODE%"=="1" (
    echo [调试] Node.js安装步骤完成，按任意键继续...
    pause >nul
)

:setup_venv
:: ========================================
:: 第三步：创建和管理Python虚拟环境
:: ========================================
echo.
echo [步骤 3/6] 创建和管理Python虚拟环境...

cd /d "%PROJECT_DIR%"

:: 检查虚拟环境是否存在
if exist "%PROJECT_DIR%.venv" (
    echo [信息] 发现现有虚拟环境，正在激活...
) else (
    echo [信息] 创建新的Python虚拟环境...
    python -m venv "%PROJECT_DIR%.venv"
    if !errorlevel! neq 0 (
        echo [错误] 创建虚拟环境失败
        echo [提示] 请确认Python安装正确且支持venv模块
        echo [提示] 按任意键退出...
        pause >nul
        exit /b 1
    )
    echo [成功] 虚拟环境创建完成
)

:: 激活虚拟环境
echo [信息] 激活虚拟环境...
call "%PROJECT_DIR%.venv\Scripts\activate.bat"
if !errorlevel! neq 0 (
    echo [错误] 虚拟环境激活失败
    echo [提示] 虚拟环境路径: %PROJECT_DIR%.venv\Scripts\activate.bat
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)

:: 验证虚拟环境
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [错误] 虚拟环境中Python不可用
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)

echo [成功] 虚拟环境激活成功
if "%DEBUG_MODE%"=="1" (
    echo [调试] 虚拟环境设置完成，按任意键继续...
    pause >nul
)
echo.

:: ========================================
:: 第四步：在虚拟环境中安装Python依赖
:: ========================================
echo [步骤4] 在虚拟环境中安装Python依赖包...

:: 首先安装根目录的主要依赖
echo [步骤4.1] 安装根目录主要依赖...
cd /d "%PROJECT_DIR%"
if exist "%PROJECT_DIR%requirements.txt" (
    call "%PROJECT_DIR%.venv\Scripts\activate.bat"
    echo [信息] 正在安装根目录依赖^(这可能需要几分钟^)...
    pip install -r requirements.txt --upgrade
    
    if !errorlevel! equ 0 (
        echo [成功] 根目录依赖安装完成
    ) else (
        echo [错误] 根目录依赖安装失败，这可能影响整个项目运行
        echo [提示] 请检查网络连接或手动运行: pip install -r requirements.txt
        if "%DEBUG_MODE%"=="1" pause >nul
    )
) else (
    echo [警告] 根目录未找到requirements.txt文件
)

:: 然后安装各模块的特定依赖
for %%d in (server AST_module StreamCap DouyinLiveWebFetcher) do (
    if exist "%PROJECT_DIR%%%d\requirements.txt" (
        echo [步骤4.%%d] 安装 %%d 模块的Python依赖...
        cd /d "%PROJECT_DIR%%%d"
        
        :: 在虚拟环境中安装依赖
        call "%PROJECT_DIR%.venv\Scripts\activate.bat"
        echo [信息] 正在安装 %%d 模块依赖...
        pip install -r requirements.txt --upgrade
        
        if !errorlevel! equ 0 (
            echo [成功] %%d 模块依赖安装完成
        ) else (
            echo [警告] %%d 模块依赖安装可能存在问题，但继续执行
            echo [提示] 可手动运行: cd %%d && pip install -r requirements.txt
            if "%DEBUG_MODE%"=="1" pause >nul
        )
        
        cd /d "%PROJECT_DIR%"
    ) else (
        echo [信息] %%d 目录不存在requirements.txt，跳过
    )
)

:: 提示测试依赖
if exist "%PROJECT_DIR%server\requirements-test.txt" (
    echo [信息] 发现测试依赖文件 server\requirements-test.txt
    echo [提示] 如需运行测试，请手动安装: pip install -r server\requirements-test.txt
)

echo [成功] 所有Python依赖安装完成！
if "%DEBUG_MODE%"=="1" (
    echo [调试] Python依赖安装完成，按任意键继续...
    pause >nul
)
echo.

:: ========================================
:: 第五步：安装Node.js依赖
:: ========================================
echo [步骤 5/6] 安装Node.js依赖...

:: 安装根目录Node.js依赖
echo [步骤5.1] 安装根目录Node.js依赖...
cd /d "%PROJECT_DIR%"
if not exist "%PROJECT_DIR%package.json" (
    echo [错误] 根目录未找到package.json文件
    echo [提示] 请确认脚本在正确的项目目录中运行
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)

echo [信息] 正在安装根目录Node.js依赖^(这可能需要几分钟^)...
npm install
if !errorlevel! neq 0 (
    echo [错误] 根目录Node.js依赖安装失败
    echo [提示] 请检查网络连接和npm配置
    echo [提示] 可尝试手动运行: npm install
    if "%DEBUG_MODE%"=="1" pause >nul
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)
echo [成功] 根目录Node.js依赖安装完成

:: 安装electron目录依赖（如果存在）
echo [步骤5.2] 检查并安装electron目录依赖...
if exist "%PROJECT_DIR%electron\package.json" (
    echo [信息] 安装electron目录Node.js依赖...
    cd /d "%PROJECT_DIR%electron"
    
    npm install
    if !errorlevel! neq 0 (
        echo [错误] electron目录Node.js依赖安装失败
        echo [提示] 可尝试手动运行: cd electron && npm install
        if "%DEBUG_MODE%"=="1" pause >nul
        echo [提示] 按任意键退出...
        pause >nul
        exit /b 1
    )
    echo [成功] electron目录Node.js依赖安装完成
) else (
    echo [信息] electron目录未找到package.json文件，跳过
)

:: 安装electron/renderer目录依赖
echo [步骤5.3] 安装electron/renderer目录依赖...
cd /d "%PROJECT_DIR%electron\renderer"
if not exist "%PROJECT_DIR%electron\renderer\package.json" (
    echo [错误] electron\renderer目录未找到package.json文件
    echo [提示] 请确认项目结构是否完整
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)

echo [信息] 正在安装electron/renderer依赖^(这可能需要几分钟^)...
npm install
if !errorlevel! neq 0 (
    echo [错误] electron\renderer目录Node.js依赖安装失败
    echo [提示] 可尝试手动运行: cd electron\renderer && npm install
    if "%DEBUG_MODE%"=="1" pause >nul
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)
echo [成功] electron\renderer目录Node.js依赖安装完成

echo [成功] 所有Node.js依赖安装完成！
if "%DEBUG_MODE%"=="1" (
    echo [调试] Node.js依赖安装完成，按任意键继续...
    pause >nul
)
echo.

:: ========================================
:: 第六步：启动应用程序
:: ========================================
echo [步骤 6/6] 启动应用程序...

echo [信息] 准备启动提猫直播助手...
if "%DEBUG_MODE%"=="1" (
    echo [调试] 应用启动前暂停，按任意键继续...
    pause >nul
)

:: 检查必要文件
echo [验证] 检查应用程序文件...
if not exist "%PROJECT_DIR%server\app.py" (
    echo [错误] 未找到后端服务器文件: server\app.py
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)

echo [信息] 在虚拟环境中启动后端服务器...
start "后端服务器" cmd /k "call "%PROJECT_DIR%.venv\Scripts\activate.bat" && cd /d "%PROJECT_DIR%server" && python app.py"
if !errorlevel! neq 0 (
    echo [错误] 后端服务器启动失败
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)
echo [成功] 后端服务器启动命令已执行

:: 等待后端服务器启动
echo [信息] 等待后端服务器启动...
timeout /t 5 /nobreak >nul

:: 启动前端开发服务器
echo [信息] 启动前端开发服务器...
cd /d "%PROJECT_DIR%electron\renderer"
if not exist "%PROJECT_DIR%electron\renderer\package.json" (
    echo [错误] 未找到electron\renderer\package.json文件
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)

start "前端开发服务器" cmd /k "cd /d "%PROJECT_DIR%electron\renderer" && npm run dev"
if !errorlevel! neq 0 (
    echo [错误] 前端开发服务器启动失败
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)
echo [成功] 前端开发服务器启动命令已执行

:: 等待前端服务器启动
echo [信息] 等待前端开发服务器启动...
timeout /t 8 /nobreak >nul

:: 启动Electron桌面应用
echo [信息] 启动Electron桌面应用...
cd /d "%PROJECT_DIR%electron"
if not exist "%PROJECT_DIR%electron\package.json" (
    echo [错误] 未找到electron\package.json文件
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)

start "Electron应用" cmd /k "cd /d "%PROJECT_DIR%electron" && npm start"
if !errorlevel! neq 0 (
    echo [错误] Electron应用启动失败
    echo [提示] 按任意键退出...
    pause >nul
    exit /b 1
)
echo [成功] Electron应用启动命令已执行

echo.
echo ========================================
echo           启动完成！
echo ========================================
echo [成功] 提猫直播助手已启动！
echo.
echo [服务状态]
echo - 后端服务器: 已启动 ^(Python FastAPI^)
echo - 前端开发服务器: 已启动 ^(React + Vite^)
echo - Electron桌面应用: 已启动
echo.
echo [注意事项]
echo 1. 请等待所有服务完全启动后再使用应用
echo 2. 如遇到问题，请检查各个终端窗口的错误信息
echo 3. 要停止应用，请关闭所有相关的终端窗口
echo.
echo [提示] 按任意键退出安装脚本...
if "%DEBUG_MODE%"=="1" (
    echo [调试] 脚本执行完成，按任意键退出...
    pause >nul
)
pause >nul
exit /b 0

:: ========================================
:: 辅助函数
:: ========================================

:refresh_env
:: 刷新环境变量的函数
echo [信息] 刷新环境变量...
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYS_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%b"
set "PATH=%SYS_PATH%;%USER_PATH%"
goto :eof