@echo off
chcp 65001 > nul
echo ========================================
echo 提猫直播助手 - 便携版打包脚本
echo ========================================

:: 检查环境
node --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Node.js
    pause
    exit /b 1
)

python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python
    pause
    exit /b 1
)

echo [信息] 开始便携版打包...

:: 1. 创建便携版目录
set PORTABLE_DIR=dist\TalkingCat-Portable
if exist "%PORTABLE_DIR%" rmdir /s /q "%PORTABLE_DIR%"
mkdir "%PORTABLE_DIR%"

:: 2. 安装依赖
echo [步骤1] 安装依赖...
call npm install
pip install -r requirements.txt

:: 3. 构建前端
echo [步骤2] 构建前端...
cd electron\renderer
call npm install
call npm run build
cd ..\..

:: 4. 复制核心文件
echo [步骤3] 复制应用文件...
xcopy /E /I /Y electron "%PORTABLE_DIR%\electron"
xcopy /E /I /Y server "%PORTABLE_DIR%\server"
xcopy /E /I /Y DouyinLiveWebFetcher "%PORTABLE_DIR%\DouyinLiveWebFetcher"
xcopy /E /I /Y AST_module "%PORTABLE_DIR%\AST_module"
copy package.json "%PORTABLE_DIR%\"
copy requirements.txt "%PORTABLE_DIR%\"

:: 5. 复制配置文件
echo [步骤4] 配置便携版设置...
mkdir "%PORTABLE_DIR%\config"
copy config\local-deployment.json "%PORTABLE_DIR%\config\"

:: 6. 创建启动脚本
echo [步骤5] 创建启动脚本...
(
echo @echo off
echo chcp 65001 ^> nul
echo echo 启动提猫直播助手...
echo cd /d "%%~dp0"
echo start /b python -m uvicorn server.app.main:app --host 127.0.0.1 --port 10090
echo timeout /t 3 /nobreak ^> nul
echo start electron\main.js
) > "%PORTABLE_DIR%\启动提猫直播助手.bat"

:: 7. 创建说明文件
(
echo 提猫直播助手 - 便携版
echo ========================
echo.
echo 使用说明：
echo 1. 双击"启动提猫直播助手.bat"启动应用
echo 2. 首次使用需要配置AI服务API密钥
echo 3. 数据文件保存在data目录下
echo 4. 日志文件保存在logs目录下
echo.
echo 系统要求：
echo - Windows 10/11
echo - Python 3.8+
echo - Node.js 16+
echo.
echo 注意事项：
echo - 请确保网络连接正常
echo - 杀毒软件可能会误报，请添加信任
echo - 如遇问题请查看logs目录下的日志文件
) > "%PORTABLE_DIR%\使用说明.txt"

echo ========================================
echo 便携版打包完成！
echo 位置: %PORTABLE_DIR%
echo ========================================
pause