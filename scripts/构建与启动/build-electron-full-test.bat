@echo off
chcp 437 >nul
setlocal

echo ========================================
echo TiMao Live Assistant - 完整打包脚本
echo ========================================

set "PROJECT_ROOT=%~dp0..\.."
echo Project Root: %PROJECT_ROOT%

REM 使用 8.3 短路径格式处理中文路径问题
for %%i in ("%PROJECT_ROOT%") do set "SHORT_PROJECT_ROOT=%%~fsi"

echo Short Path: %SHORT_PROJECT_ROOT%

REM 切换到项目目录
cd /d "%PROJECT_ROOT%"

echo.
echo [1/5] 构建前端...

cd "%SHORT_PROJECT_ROOT%\electron\renderer"
if exist "dist" rd /s /q "dist"
call npm run build

if errorlevel 1 (
    echo [ERROR] 前端构建失败
    pause
    exit /b 1
)
echo [OK] 前端构建完成

echo.
echo [2/5] 打包转写服务...

cd "%SHORT_PROJECT_ROOT%\electron\python-transcriber"
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    pip install pyinstaller>=5.0
)

if exist "dist" rd /s /q "dist"
if exist "build" rd /s /q "build"

python build_spec.py

if errorlevel 1 (
    echo [ERROR] 转写服务打包失败
    pause
    exit /b 1
)
echo [OK] 转写服务打包完成

echo.
echo [3/5] 打包后端服务...

cd "%SHORT_PROJECT_ROOT%"

REM 使用 Python 直接调用完整路径的脚本
"%SHORT_PROJECT_ROOT%\.venv\Scripts\python.exe" "%SHORT_PROJECT_ROOT%\scripts\构建与启动\build_backend.py"

if errorlevel 1 (
    echo [ERROR] 后端打包失败
    pause
    exit /b 1
)
echo [OK] 后端打包完成

echo.
echo [4/5] 准备资源...

mkdir "%SHORT_PROJECT_ROOT%\electron\resources" 2>nul
mkdir "%SHORT_PROJECT_ROOT%\electron\resources\backend" 2>nul
mkdir "%SHORT_PROJECT_ROOT%\electron\resources\python-transcriber" 2>nul

if exist "%SHORT_PROJECT_ROOT%\electron\python-transcriber\dist\transcriber_service.exe" (
    copy /Y "%SHORT_PROJECT_ROOT%\electron\python-transcriber\dist\transcriber_service.exe" "%SHORT_PROJECT_ROOT%\electron\resources\python-transcriber\" >nul
)

if exist "%SHORT_PROJECT_ROOT%\backend_dist\timao_backend_service.exe" (
    copy /Y "%SHORT_PROJECT_ROOT%\backend_dist\timao_backend_service.exe" "%SHORT_PROJECT_ROOT%\electron\resources\backend\" >nul
)

echo [OK] 资源准备完成

echo.
echo [5/5] 构建 Electron...

if exist "%SHORT_PROJECT_ROOT%\dist" rd /s /q "%SHORT_PROJECT_ROOT%\dist"

npx electron-builder --win --x64 --config build-config.json

if errorlevel 1 (
    echo [ERROR] Electron 打包失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成!
echo 输出: %PROJECT_ROOT%\dist
echo ========================================

pause
