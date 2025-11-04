@echo off
chcp 65001 > nul
echo ========================================
echo 提猫直播助手 - 本地化打包脚本
echo ========================================

:: 检查Node.js环境
node --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Node.js，请先安装Node.js
    pause
    exit /b 1
)

:: 检查Python环境
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python
    pause
    exit /b 1
)

echo [信息] 开始本地化打包...

:: 1. 安装依赖
echo [步骤1] 安装前端依赖...
call npm install
if %errorlevel% neq 0 (
    echo [错误] 前端依赖安装失败
    pause
    exit /b 1
)

:: 2. 安装Python依赖
echo [步骤2] 安装Python依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] Python依赖安装失败
    pause
    exit /b 1
)

:: 3. 构建前端
echo [步骤3] 构建前端资源...
cd electron\renderer
call npm install
call npm run build
cd ..\..

:: 4. 复制本地化配置
echo [步骤4] 应用本地化配置...
if exist config\local-deployment.json (
    copy config\local-deployment.json server\config\deployment.json
)

:: 5. 打包应用
echo [步骤5] 打包Electron应用...
call npm run build:config
if %errorlevel% neq 0 (
    echo [错误] 应用打包失败
    pause
    exit /b 1
)

echo ========================================
echo 打包完成！
echo 安装包位置: dist\
echo ========================================
pause