# 🛠️ 开发环境 MySQL 配置说明

## 📌 为什么开发环境使用 MySQL？

为了确保**开发环境与生产环境一致**，避免因数据库差异导致的问题：

| 场景 | SQLite | MySQL |
|------|--------|-------|
| 并发测试 | ❌ 单线程限制 | ✅ 真实并发 |
| 数据类型 | 有差异 | 完全一致 |
| 索引优化 | 简化 | 真实性能 |
| 锁机制 | 表锁 | 行锁 |
| 事务隔离 | 简单 | 完整支持 |

**统一数据库**可以：
- ✅ 避免 SQL 兼容性问题
- ✅ 真实模拟生产环境性能
- ✅ 提前发现数据库相关 Bug
- ✅ 简化部署流程

---

## 🚀 快速开始

### 自动化安装（推荐）

#### Windows:
```bash
setup-dev-mysql.bat
```

#### macOS/Linux:
```bash
bash setup-dev-mysql.sh
```

脚本会自动完成：
1. ✅ 检查 MySQL 安装
2. ✅ 创建数据库和用户
3. ✅ 生成 .env 配置
4. ✅ 安装 Python 驱动
5. ✅ 初始化表结构

---

## 📦 MySQL 安装方式

### 方式 1: Docker（最简单）

```bash
# 启动 MySQL 容器
docker run -d \
  --name timao-mysql \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=timao_live \
  -e MYSQL_USER=timao \
  -e MYSQL_PASSWORD=timao123456 \
  -p 3306:3306 \
  mysql:8.0

# 验证启动
docker logs timao-mysql
```

**优点**：
- ✅ 无需安装 MySQL
- ✅ 一键启动/停止
- ✅ 环境隔离
- ✅ 易于清理

### 方式 2: 包管理器

#### Windows (Chocolatey):
```bash
choco install mysql
net start MySQL80
```

#### macOS (Homebrew):
```bash
brew install mysql
brew services start mysql
```

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
```

### 方式 3: 官方安装包

下载地址：https://dev.mysql.com/downloads/mysql/

---

## ⚙️ 配置说明

### .env 配置

```bash
# 数据库类型（默认 MySQL）
DB_TYPE=mysql

# MySQL 连接配置
MYSQL_HOST=localhost      # 本地开发用 localhost
MYSQL_PORT=3306           # 默认端口
MYSQL_USER=timao          # 用户名
MYSQL_PASSWORD=timao123456  # 密码（开发环境）
MYSQL_DATABASE=timao_live # 数据库名
```

### 生产环境配置

```bash
# 使用环境变量覆盖
MYSQL_HOST=production-db.example.com
MYSQL_USER=prod_user
MYSQL_PASSWORD=<强密码>
```

---

## 🔧 手动配置步骤

### 1. 创建数据库

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
CREATE USER 'timao'@'localhost' IDENTIFIED BY 'timao123456';

-- 授予权限
GRANT ALL PRIVILEGES ON timao_live.* TO 'timao'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 验证
SHOW DATABASES;
SELECT User, Host FROM mysql.user WHERE User = 'timao';
```

### 2. 配置 .env

```bash
# 复制模板
cp .env.example .env

# 生成密钥
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(48))" >> .env
python -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(24))" >> .env
```

### 3. 安装驱动

```bash
pip install pymysql cryptography
```

### 4. 初始化表

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

## 🧪 测试连接

### Python 测试

```python
from server.app.database import DatabaseManager
from server.config import config_manager

try:
    db = DatabaseManager(config_manager.config.database)
    db.initialize()
    print("✅ MySQL 连接成功！")
except Exception as e:
    print(f"❌ 连接失败: {e}")
```

### 命令行测试

```bash
mysql -h localhost -u timao -ptimao123456 timao_live -e "SHOW TABLES;"
```

---

## 🔄 切换数据库

### 临时切换到 SQLite

```bash
# 修改 .env
DB_TYPE=sqlite
DATABASE_PATH=data/timao_dev.db

# 重启应用
npm run dev
```

### 恢复 MySQL

```bash
# 修改 .env
DB_TYPE=mysql

# 重启应用
npm run dev
```

---

## 🐛 常见问题

### Q1: MySQL 服务未启动

**Windows:**
```bash
net start MySQL80
```

**macOS:**
```bash
brew services start mysql
```

**Linux:**
```bash
sudo systemctl start mysql
```

**Docker:**
```bash
docker start timao-mysql
```

### Q2: 连接被拒绝

检查：
1. MySQL 服务是否运行
2. 端口 3306 是否开放
3. 防火墙规则

```bash
# 检查端口监听
netstat -tuln | grep 3306

# 测试连接
telnet localhost 3306
```

### Q3: 权限错误

```sql
-- 重新授权
GRANT ALL PRIVILEGES ON timao_live.* TO 'timao'@'localhost';
FLUSH PRIVILEGES;
```

### Q4: 字符集问题

```sql
-- 检查字符集
SHOW VARIABLES LIKE 'character%';

-- 修改数据库字符集
ALTER DATABASE timao_live 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;
```

---

## 📊 开发工具

### 推荐的 MySQL 客户端

1. **MySQL Workbench**（官方）
   - 下载：https://dev.mysql.com/downloads/workbench/

2. **DBeaver**（免费开源）
   - 下载：https://dbeaver.io/

3. **TablePlus**（macOS/Windows）
   - 下载：https://tableplus.com/

4. **phpMyAdmin**（Web）
   ```bash
   docker run -d \
     --name phpmyadmin \
     -e PMA_HOST=host.docker.internal \
     -p 8080:80 \
     phpmyadmin
   ```

---

## 🔐 安全建议

### 开发环境

- ✅ 使用简单密码（如 timao123456）
- ✅ 仅允许本地连接
- ✅ 定期备份数据

### 生产环境

- ❌ 不要使用默认密码
- ✅ 使用强密码（至少 16 位）
- ✅ 限制远程访问
- ✅ 启用 SSL 连接
- ✅ 配置自动备份

---

## 📝 数据备份

### 手动备份

```bash
# 备份数据库
mysqldump -u timao -p timao_live > backup_$(date +%Y%m%d).sql

# 恢复数据库
mysql -u timao -p timao_live < backup_20250126.sql
```

### 自动备份（Cron）

```bash
# 每天凌晨 2 点备份
0 2 * * * mysqldump -u timao -ptimao123456 timao_live > /backup/timao_$(date +\%Y\%m\%d).sql
```

---

## 🚀 性能优化

### 开发环境配置

```ini
# my.cnf 或 my.ini
[mysqld]
# 适度的缓冲区
innodb_buffer_pool_size=256M
innodb_log_file_size=64M

# 加快开发速度
innodb_flush_log_at_trx_commit=2
```

### 创建索引

```sql
-- 常用查询优化
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_subscription_user ON subscriptions(user_id);
CREATE INDEX idx_payment_status ON payments(status);
```

---

## ✅ 检查清单

开始开发前：

- [ ] MySQL 已安装并运行
- [ ] 数据库 `timao_live` 已创建
- [ ] 用户 `timao` 已授权
- [ ] `.env` 文件已配置
- [ ] Python MySQL 驱动已安装
- [ ] 数据库连接测试成功
- [ ] 表结构已初始化

---

## 📞 获取帮助

- 📘 [MYSQL_SETUP.md](MYSQL_SETUP.md) - 完整 MySQL 配置指南
- 📗 [DEPLOYMENT.md](DEPLOYMENT.md) - 生产环境部署
- 📕 [QUICK_START.md](QUICK_START.md) - 快速开始

---

**现在开始开发吧！** 🚀

```bash
npm run dev
```
