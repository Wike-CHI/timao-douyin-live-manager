@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo TiMao Live Assistant - 完整打包脚本
echo ========================================
echo.

set "PROJECT_ROOT=%~dp0..\.."
cd /d "%PROJECT_ROOT%"

echo [INFO] 项目目录: %PROJECT_ROOT%
echo.

REM ========================================
REM 第1步：构建前端
REM ========================================
echo [1/5] 构建前端应用...
echo ------------------------------------------------

cd "%PROJECT_ROOT%\electron\renderer"
if exist "dist" (
    echo 清理旧的构建文件...
    rd /s /q "dist" 2>nul
)

echo 运行 npm run build...
call npm run build

if %errorlevel% neq 0 (
    echo [ERROR] 前端构建失败
    pause
    exit /b 1
)

echo.
echo [OK] 前端构建完成
echo.

REM ========================================
REM 第2步：打包 Python 转写服务
REM ========================================
echo [2/5] 打包 Python 转写服务 (PyInstaller)...
echo ------------------------------------------------

cd "%PROJECT_ROOT%\electron\python-transcriber"

REM 检查 PyInstaller 是否安装
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo 安装 PyInstaller...
    pip install pyinstaller>=5.0
    if %errorlevel% neq 0 (
        echo [ERROR] PyInstaller 安装失败
        pause
        exit /b 1
    )
)

REM 清理旧的构建文件
if exist "dist" (
    echo 清理旧的转写服务构建文件...
    rd /s /q "dist" 2>nul
)
if exist "build" (
    rd /s /q "build" 2>nul
)

echo 运行 PyInstaller...
python build_spec.py

if %errorlevel% neq 0 (
    echo [ERROR] 转写服务打包失败
    pause
    exit /b 1
)

echo.
echo [OK] 转写服务打包完成
echo.

REM ========================================
REM 第3步：打包后端服务
REM ========================================
echo [3/5] 打包后端服务 (PyInstaller)...
echo ------------------------------------------------

cd "%PROJECT_ROOT%"

REM 使用正确的 Python 路径和脚本路径
set "PYTHON_EXE="
set "BACKEND_SCRIPT="

REM 检测虚拟环境中的Python
if exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%PROJECT_ROOT%\.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

REM 设置后端脚本路径（使用引号避免中文路径问题）
set "BACKEND_SCRIPT=%PROJECT_ROOT%\scripts\构建与启动\build_backend.py"

echo 使用 Python: %PYTHON_EXE%
echo 后端脚本: %BACKEND_SCRIPT%

REM 检查脚本是否存在
if not exist "%BACKEND_SCRIPT%" (
    echo [ERROR] 后端打包脚本不存在: %BACKEND_SCRIPT%
    pause
    exit /b 1
)

REM 运行后端打包脚本
echo 运行后端打包...
"%PYTHON_EXE%" "%BACKEND_SCRIPT%"

if %errorlevel% neq 0 (
    echo [ERROR] 后端服务打包失败
    pause
    exit /b 1
)

echo.
echo [OK] 后端服务打包完成
echo.

REM ========================================
REM 第4步：复制资源文件
REM ========================================
echo [4/5] 准备资源文件...
echo ------------------------------------------------

REM 确保目标目录存在
mkdir "%PROJECT_ROOT%\electron\resources" 2>nul
mkdir "%PROJECT_ROOT%\electron\resources\backend" 2>nul
mkdir "%PROJECT_ROOT%\electron\resources\python-transcriber" 2>nul

REM 复制转写服务可执行文件
echo 复制转写服务...
if exist "%PROJECT_ROOT%\electron\python-transcriber\dist\transcriber_service.exe" (
    copy /Y "%PROJECT_ROOT%\electron\python-transcriber\dist\transcriber_service.exe" "%PROJECT_ROOT%\electron\resources\python-transcriber\" >nul
    echo   - transcriber_service.exe
) else (
    echo [WARNING] 转写服务可执行文件不存在
)

REM 复制后端服务可执行文件
echo 复制后端服务...
if exist "%PROJECT_ROOT%\backend_dist\timao_backend_service.exe" (
    copy /Y "%PROJECT_ROOT%\backend_dist\timao_backend_service.exe" "%PROJECT_ROOT%\electron\resources\backend\" >nul
    echo   - timao_backend_service.exe
) else (
    echo [WARNING] 后端服务可执行文件不存在
)

echo.
echo [OK] 资源文件准备完成
echo.

REM ========================================
REM 第5步：构建 Electron 便携版
REM ========================================
echo [5/5] 构建 Electron 便携版...
echo ------------------------------------------------

REM 清理旧的打包文件
if exist "%PROJECT_ROOT%\dist" (
    echo 清理旧的打包文件...
    rd /s /q "%PROJECT_ROOT%\dist" 2>nul
)

REM 确保 extraResources 目录存在
mkdir "%PROJECT_ROOT%\backend_dist" 2>nul
mkdir "%PROJECT_ROOT%\electron\python-transcriber\dist" 2>nul

REM 复制资源到 extraResources 位置（供 electron-builder 使用）
echo 准备 extraResources...
if exist "%PROJECT_ROOT%\electron\resources\backend\*" (
    copy /Y "%PROJECT_ROOT%\electron\resources\backend\*" "%PROJECT_ROOT%\backend_dist\" >nul
)

REM 运行 electron-builder
echo 运行 electron-builder...
call npx electron-builder --win --x64 --config build-config.json

if %errorlevel% neq 0 (
    echo [ERROR] Electron 打包失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成!
echo ========================================
echo.
echo 输出目录: %PROJECT_ROOT%\dist
echo.

REM 列出生成的文件
if exist "%PROJECT_ROOT%\dist" (
    echo 生成的文件:
    dir /b "%PROJECT_ROOT%\dist\*.exe" 2>nul
    echo.
)

echo 资源文件位置:
echo   - 后端服务: %PROJECT_ROOT%\electron\resources\backend\
echo   - 转写服务: %PROJECT_ROOT%\electron\resources\python-transcriber\
echo.

echo 使用说明:
echo   1. 运行 dist\ 下的便携版 exe 文件
echo   2. 首次启动会自动下载 SenseVoice 模型（约1.5GB）
echo   3. 模型下载完成后即可离线使用
echo.

echo 按任意键退出...
pause >nul
