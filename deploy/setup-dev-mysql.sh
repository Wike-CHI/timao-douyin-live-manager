#!/bin/bash
# 开发环境 MySQL 快速启动脚本

echo "🐱 提猫直播助手 - 开发环境 MySQL 初始化"
echo "=========================================="

# 检查 MySQL 是否安装
if ! command -v mysql &> /dev/null; then
    echo "❌ 未检测到 MySQL，请先安装："
    echo ""
    echo "Windows: choco install mysql"
    echo "Linux:   sudo apt install mysql-server"
    echo "macOS:   brew install mysql"
    echo "Docker:  docker run -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root mysql:8.0"
    exit 1
fi

echo "✅ MySQL 已安装"

# 检查 MySQL 服务是否运行
if ! mysqladmin ping -h localhost --silent 2>/dev/null; then
    echo "❌ MySQL 服务未运行，请先启动："
    echo ""
    echo "Windows: net start mysql"
    echo "Linux:   sudo systemctl start mysql"
    echo "macOS:   brew services start mysql"
    exit 1
fi

echo "✅ MySQL 服务运行中"

# 创建数据库和用户
echo ""
echo "📊 创建数据库和用户..."
mysql -u root -p <<EOF
CREATE DATABASE IF NOT EXISTS timao_live CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'timao'@'localhost' IDENTIFIED BY 'timao123456';
GRANT ALL PRIVILEGES ON timao_live.* TO 'timao'@'localhost';
FLUSH PRIVILEGES;
SELECT 'Database created successfully!' AS status;
EOF

if [ $? -eq 0 ]; then
    echo "✅ 数据库创建成功"
else
    echo "❌ 数据库创建失败，请检查 MySQL root 密码"
    exit 1
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo ""
    echo "📝 创建 .env 配置文件..."
    cp .env.example .env
    
    # 生成密钥
    SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))" 2>/dev/null || openssl rand -base64 48)
    ENCRYPTION_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(24))" 2>/dev/null || openssl rand -base64 24)
    
    # 更新 .env
    sed -i.bak "s/SECRET_KEY=/SECRET_KEY=$SECRET_KEY/" .env
    sed -i.bak "s/ENCRYPTION_KEY=/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
    rm -f .env.bak
    
    echo "✅ .env 文件已创建"
else
    echo "✅ .env 文件已存在"
fi

# 安装 Python MySQL 驱动
echo ""
echo "📦 安装 MySQL 驱动..."
pip install pymysql cryptography >/dev/null 2>&1
echo "✅ MySQL 驱动已安装"

# 初始化数据库表
echo ""
echo "🗄️ 初始化数据库表..."
python -c "
from server.app.database import DatabaseManager
from server.config import config_manager

try:
    db = DatabaseManager(config_manager.config.database)
    db.initialize()
    print('✅ 数据库表已创建')
except Exception as e:
    print(f'❌ 初始化失败: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

echo ""
echo "=========================================="
echo "🎉 开发环境初始化完成！"
echo ""
echo "📊 MySQL 连接信息："
echo "   Host:     localhost"
echo "   Port:     3306"
echo "   User:     timao"
echo "   Password: timao123456"
echo "   Database: timao_live"
echo ""
echo "🚀 启动应用："
echo "   npm run dev"
echo ""
echo "📚 管理界面："
echo "   http://localhost:{PORT}/docs"  # 默认端口为 9019，可通过环境变量 BACKEND_PORT 修改
echo "=========================================="
