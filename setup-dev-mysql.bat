@echo off
chcp 65001 >nul
REM 开发环境 MySQL 快速启动脚本 (Windows)

echo 🐱 提猫直播助手 - 开发环境 MySQL 初始化
echo ==========================================
echo.

REM 检查 MySQL 是否安装
where mysql >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 未检测到 MySQL，请先安装：
    echo.
    echo   方式1: choco install mysql
    echo   方式2: https://dev.mysql.com/downloads/mysql/
    echo   方式3: docker run -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root mysql:8.0
    pause
    exit /b 1
)

echo ✅ MySQL 已安装

REM 检查 MySQL 服务状态
sc query MySQL80 | find "RUNNING" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ MySQL 服务未运行，正在启动...
    net start MySQL80 >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ 启动失败，请手动启动: net start MySQL80
        pause
        exit /b 1
    )
)

echo ✅ MySQL 服务运行中
echo.

REM 创建数据库和用户
echo 📊 创建数据库和用户...
echo 请输入 MySQL root 密码：
set /p ROOT_PASS=

(
echo CREATE DATABASE IF NOT EXISTS timao_live CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
echo CREATE USER IF NOT EXISTS 'timao'@'localhost' IDENTIFIED BY 'timao123456';
echo GRANT ALL PRIVILEGES ON timao_live.* TO 'timao'@'localhost';
echo FLUSH PRIVILEGES;
echo SELECT 'Database created successfully!' AS status;
) | mysql -u root -p%ROOT_PASS% 2>nul

if %ERRORLEVEL% EQU 0 (
    echo ✅ 数据库创建成功
) else (
    echo ❌ 数据库创建失败，请检查 root 密码
    pause
    exit /b 1
)

echo.

REM 检查 .env 文件
if not exist .env (
    echo 📝 创建 .env 配置文件...
    copy .env.example .env >nul
    
    REM 生成密钥
    python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(48))" >> .env.tmp 2>nul
    python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(24))" >> .env.tmp 2>nul
    
    if exist .env.tmp (
        type .env.tmp >> .env
        del .env.tmp
    )
    
    echo ✅ .env 文件已创建
) else (
    echo ✅ .env 文件已存在
)

echo.

REM 安装 Python MySQL 驱动
echo 📦 安装 MySQL 驱动...
pip install pymysql cryptography >nul 2>nul
echo ✅ MySQL 驱动已安装

echo.

REM 初始化数据库表
echo 🗄️ 初始化数据库表...
python -c "from server.app.database import DatabaseManager; from server.config import config_manager; db = DatabaseManager(config_manager.config.database); db.initialize(); print('✅ 数据库表已创建')"

if %ERRORLEVEL% NEQ 0 (
    echo ❌ 初始化失败
    pause
    exit /b 1
)

echo.
echo ==========================================
echo 🎉 开发环境初始化完成！
echo.
echo 📊 MySQL 连接信息：
echo    Host:     localhost
echo    Port:     3306
echo    User:     timao
echo    Password: timao123456
echo    Database: timao_live
echo.
echo 🚀 启动应用：
echo    npm run dev
echo.
echo 📚 管理界面：
echo    http://localhost:10090/docs
echo ==========================================
echo.
pause
