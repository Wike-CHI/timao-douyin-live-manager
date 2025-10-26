# 📊 MySQL 数据库配置指南

## 🎯 为什么使用 MySQL？

相比 SQLite，MySQL 在生产环境中具有以下优势：

| 特性 | SQLite | MySQL |
|------|--------|-------|
| 并发写入 | ❌ 单线程写入 | ✅ 高并发支持 |
| 数据量 | 适合小型应用 | ✅ 支持大规模数据 |
| 性能 | 中等 | ✅ 高性能优化 |
| 网络访问 | ❌ 仅本地 | ✅ 支持远程连接 |
| 备份恢复 | 简单但有限 | ✅ 完善的备份方案 |
| 用户权限 | ❌ 文件级别 | ✅ 细粒度权限控制 |

**推荐**：
- **开发环境**：SQLite（快速启动，无需安装）
- **生产环境**：MySQL（稳定可靠，高性能）

---

## 📋 安装 MySQL

### Windows

```bash
# 下载 MySQL 安装包
https://dev.mysql.com/downloads/mysql/

# 或使用 Chocolatey
choco install mysql

# 启动服务
net start mysql
```

### Linux (Ubuntu/Debian)

```bash
# 安装 MySQL
sudo apt update
sudo apt install mysql-server

# 启动服务
sudo systemctl start mysql
sudo systemctl enable mysql

# 安全配置
sudo mysql_secure_installation
```

### macOS

```bash
# 使用 Homebrew 安装
brew install mysql

# 启动服务
brew services start mysql
```

### Docker（推荐）

```bash
# 拉取镜像
docker pull mysql:8.0

# 启动容器
docker run -d \
  --name timao-mysql \
  -e MYSQL_ROOT_PASSWORD=rootpassword \
  -e MYSQL_DATABASE=timao_live \
  -e MYSQL_USER=timao \
  -e MYSQL_PASSWORD=timao123456 \
  -p 3306:3306 \
  -v timao-mysql-data:/var/lib/mysql \
  mysql:8.0 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_unicode_ci

# 查看日志
docker logs -f timao-mysql
```

---

## 🔧 创建数据库和用户

### 方式一：命令行

```bash
# 登录 MySQL
mysql -u root -p

# 或使用 Docker
docker exec -it timao-mysql mysql -u root -p
```

```sql
-- 创建数据库
CREATE DATABASE timao_live 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

-- 创建用户
CREATE USER 'timao'@'localhost' IDENTIFIED BY 'your-strong-password';

-- 授予权限
GRANT ALL PRIVILEGES ON timao_live.* TO 'timao'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 验证
SHOW DATABASES;
SELECT User, Host FROM mysql.user WHERE User = 'timao';

-- 退出
EXIT;
```

### 方式二：使用脚本

创建文件 `setup_mysql.sql`：

```sql
-- setup_mysql.sql
CREATE DATABASE IF NOT EXISTS timao_live 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'timao'@'localhost' IDENTIFIED BY 'timao123456';
CREATE USER IF NOT EXISTS 'timao'@'%' IDENTIFIED BY 'timao123456';

GRANT ALL PRIVILEGES ON timao_live.* TO 'timao'@'localhost';
GRANT ALL PRIVILEGES ON timao_live.* TO 'timao'@'%';

FLUSH PRIVILEGES;

-- 显示创建的数据库
SHOW DATABASES LIKE 'timao%';

-- 显示用户权限
SHOW GRANTS FOR 'timao'@'localhost';
```

执行脚本：

```bash
mysql -u root -p < setup_mysql.sql
```

---

## ⚙️ 配置应用

### 1. 安装 Python 依赖

```bash
pip install pymysql cryptography
```

### 2. 配置环境变量

编辑 `.env` 文件：

```bash
# 数据库类型
DB_TYPE=mysql

# MySQL 配置
MYSQL_HOST=localhost          # 或 Docker 容器 IP
MYSQL_PORT=3306
MYSQL_USER=timao
MYSQL_PASSWORD=your-strong-password
MYSQL_DATABASE=timao_live
```

### 3. 测试连接

```bash
python -c "
from server.app.database import DatabaseManager
from server.config import config_manager

try:
    db = DatabaseManager(config_manager.config.database)
    db.initialize()
    print('✅ MySQL 连接成功！')
except Exception as e:
    print(f'❌ 连接失败: {e}')
"
```

### 4. 初始化表结构

```bash
python -c "
from server.app.database import DatabaseManager
from server.config import config_manager

db = DatabaseManager(config_manager.config.database)
db.initialize()
print('✅ 数据库表已创建')
"
```

---

## 🔄 从 SQLite 迁移到 MySQL

### 方式一：使用 Alembic（推荐）

```bash
# 1. 安装 Alembic
pip install alembic

# 2. 初始化
alembic init alembic

# 3. 配置 alembic.ini
# 修改 sqlalchemy.url 为你的 MySQL 连接字符串

# 4. 生成迁移脚本
alembic revision --autogenerate -m "Initial migration"

# 5. 执行迁移
alembic upgrade head
```

### 方式二：导出导入

```bash
# 1. 从 SQLite 导出数据
sqlite3 data/timao.db .dump > data_backup.sql

# 2. 转换为 MySQL 格式（需要手动调整）
# 主要修改：
# - AUTOINCREMENT -> AUTO_INCREMENT
# - 日期时间格式
# - 布尔值 (0/1 -> false/true)

# 3. 导入到 MySQL
mysql -u timao -p timao_live < data_backup.sql
```

### 方式三：使用 Python 脚本

创建 `migrate_sqlite_to_mysql.py`：

```python
"""SQLite 迁移到 MySQL 脚本"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.app.models import Base
from server.app.models.user import User
from server.app.models.payment import Plan, Subscription, Payment

# SQLite 连接
sqlite_engine = create_engine('sqlite:///data/timao.db')
SQLiteSession = sessionmaker(bind=sqlite_engine)

# MySQL 连接
mysql_engine = create_engine(
    'mysql+pymysql://timao:password@localhost:3306/timao_live?charset=utf8mb4'
)
MySQLSession = sessionmaker(bind=mysql_engine)

# 创建 MySQL 表
Base.metadata.create_all(mysql_engine)

# 迁移数据
def migrate_data():
    sqlite_session = SQLiteSession()
    mysql_session = MySQLSession()
    
    try:
        # 迁移用户
        users = sqlite_session.query(User).all()
        for user in users:
            mysql_session.merge(user)
        
        # 迁移其他表...
        # plans = sqlite_session.query(Plan).all()
        # ...
        
        mysql_session.commit()
        print(f"✅ 成功迁移 {len(users)} 个用户")
        
    except Exception as e:
        mysql_session.rollback()
        print(f"❌ 迁移失败: {e}")
    finally:
        sqlite_session.close()
        mysql_session.close()

if __name__ == '__main__':
    migrate_data()
```

运行迁移：

```bash
python migrate_sqlite_to_mysql.py
```

---

## 🔐 安全配置

### 1. 设置强密码

```sql
-- 修改密码
ALTER USER 'timao'@'localhost' IDENTIFIED BY 'new-strong-password';
FLUSH PRIVILEGES;
```

### 2. 限制远程访问

```sql
-- 仅允许本地访问
REVOKE ALL PRIVILEGES ON *.* FROM 'timao'@'%';
GRANT ALL PRIVILEGES ON timao_live.* TO 'timao'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 配置 SSL 连接

```bash
# 修改 MySQL 配置
sudo vim /etc/mysql/mysql.conf.d/mysqld.cnf

# 添加：
[mysqld]
require_secure_transport=ON
ssl-ca=/path/to/ca.pem
ssl-cert=/path/to/server-cert.pem
ssl-key=/path/to/server-key.pem
```

### 4. 定期备份

```bash
# 手动备份
mysqldump -u timao -p timao_live > backup_$(date +%Y%m%d).sql

# 自动备份（Cron）
0 2 * * * mysqldump -u timao -p<password> timao_live > /backup/timao_$(date +\%Y\%m\%d).sql
```

---

## 🚀 性能优化

### 1. 优化配置

编辑 `/etc/mysql/mysql.conf.d/mysqld.cnf`：

```ini
[mysqld]
# 基础配置
max_connections=200
thread_cache_size=8
query_cache_size=32M
query_cache_limit=2M

# InnoDB 配置
innodb_buffer_pool_size=1G
innodb_log_file_size=256M
innodb_flush_log_at_trx_commit=2
innodb_flush_method=O_DIRECT

# 字符集
character-set-server=utf8mb4
collation-server=utf8mb4_unicode_ci
```

### 2. 创建索引

```sql
USE timao_live;

-- 用户表索引
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_username ON users(username);
CREATE INDEX idx_user_status ON users(status);

-- 订阅表索引
CREATE INDEX idx_subscription_user ON subscriptions(user_id);
CREATE INDEX idx_subscription_status ON subscriptions(status);
CREATE INDEX idx_subscription_end_date ON subscriptions(end_date);

-- 支付表索引
CREATE INDEX idx_payment_user ON payments(user_id);
CREATE INDEX idx_payment_status ON payments(status);
CREATE INDEX idx_payment_created ON payments(created_at);
```

### 3. 查询优化

```sql
-- 分析慢查询
SHOW VARIABLES LIKE 'slow_query_log%';
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;

-- 查看执行计划
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';

-- 优化表
OPTIMIZE TABLE users;
ANALYZE TABLE users;
```

---

## 🐛 故障排查

### 连接失败

```bash
# 检查 MySQL 服务状态
sudo systemctl status mysql

# 检查端口监听
netstat -tuln | grep 3306

# 检查防火墙
sudo ufw allow 3306

# 测试连接
mysql -h localhost -u timao -p
```

### 权限问题

```sql
-- 查看用户权限
SHOW GRANTS FOR 'timao'@'localhost';

-- 重新授权
GRANT ALL PRIVILEGES ON timao_live.* TO 'timao'@'localhost';
FLUSH PRIVILEGES;
```

### 编码问题

```sql
-- 检查数据库编码
SHOW VARIABLES LIKE 'character%';
SHOW VARIABLES LIKE 'collation%';

-- 修改数据库编码
ALTER DATABASE timao_live CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 修改表编码
ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 📊 监控和维护

### 1. 监控工具

```bash
# 安装 MySQL Workbench（GUI 工具）
# 下载：https://dev.mysql.com/downloads/workbench/

# 或使用命令行监控
mysql -u root -p -e "SHOW PROCESSLIST;"
mysql -u root -p -e "SHOW STATUS;"
```

### 2. 定期维护

```bash
# 每周执行
mysqlcheck -u root -p --auto-repair --optimize timao_live

# 清理日志
mysql -u root -p -e "PURGE BINARY LOGS BEFORE DATE_SUB(NOW(), INTERVAL 7 DAY);"
```

### 3. 备份策略

```bash
# 完整备份（每天）
mysqldump -u timao -p timao_live > full_backup_$(date +%Y%m%d).sql

# 增量备份（配置二进制日志）
# 在 my.cnf 中启用：
[mysqld]
log-bin=/var/log/mysql/mysql-bin.log
expire_logs_days=7
```

---

## ✅ 检查清单

部署 MySQL 前请确认：

- [ ] MySQL 服务已安装并运行
- [ ] 数据库 `timao_live` 已创建
- [ ] 用户 `timao` 已创建并授权
- [ ] `.env` 文件已配置 MySQL 连接信息
- [ ] Python 依赖 `pymysql` 已安装
- [ ] 数据库连接测试成功
- [ ] 表结构已初始化
- [ ] 备份策略已配置
- [ ] 监控工具已设置

---

## 📞 技术支持

如遇到问题，请查看：
- [DEPLOYMENT.md](DEPLOYMENT.md) - 完整部署文档
- [FIX_REPORT.md](FIX_REPORT.md) - 常见问题修复
- MySQL 官方文档：https://dev.mysql.com/doc/

**常用命令速查**：

```bash
# 启动/停止/重启 MySQL
sudo systemctl start mysql
sudo systemctl stop mysql
sudo systemctl restart mysql

# 查看状态
sudo systemctl status mysql

# 登录 MySQL
mysql -u timao -p

# 查看数据库
SHOW DATABASES;

# 查看表
USE timao_live;
SHOW TABLES;

# 查看表结构
DESC users;
```
