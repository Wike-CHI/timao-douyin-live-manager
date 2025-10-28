# 📦 提猫直播助手 - 部署文档

## 🚀 快速部署指南

### 环境要求

- **Python**: 3.10+
- **Node.js**: 18.x+
- **数据库**: MySQL 5.7+ / MariaDB 10.3+ （推荐） 或 SQLite（开发环境）
- **可选**: Redis 4.0+（用于会话管理和限流）

---

## 📋 部署步骤

### 1️⃣ 克隆项目

```bash
git clone https://github.com/Wike-CHI/timao-douyin-live-manager.git
cd timao-douyin-live-manager
```

### 2️⃣ 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置必要的参数
```

**⚠️ 重要配置项：**

```bash
# 必须设置（生产环境）
SECRET_KEY=<生成64位随机字符串>
ENCRYPTION_KEY=<生成32位随机字符串>

# 数据库配置（选择 MySQL 或 SQLite）
DB_TYPE=mysql                            # 或 sqlite

# MySQL 配置（推荐生产环境使用）
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=timao
MYSQL_PASSWORD=<你的MySQL密码>
MYSQL_DATABASE=timao_live

# SQLite 配置（开发环境）
DATABASE_PATH=data/timao.db

# AI 服务商
AI_SERVICE=qwen
AI_API_KEY=sk-your-api-key-here
AI_MODEL=qwen-plus

# 可选：Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

**生成安全密钥：**

```bash
# 生成 SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(48))"

# 生成 ENCRYPTION_KEY
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

### 3️⃣ 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Node.js 依赖
npm install
```

### 4️⃣ 初始化数据库

#### 使用 MySQL（推荐生产环境）

```bash
# 1. 创建数据库
mysql -u root -p
```

```sql
CREATE DATABASE timao_live CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'timao'@'localhost' IDENTIFIED BY '<设置强密码>';
GRANT ALL PRIVILEGES ON timao_live.* TO 'timao'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

```bash
# 2. 配置 .env 文件
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=timao
MYSQL_PASSWORD=<你的密码>
MYSQL_DATABASE=timao_live

# 3. 初始化数据库表
python -c "from server.app.database import DatabaseManager; from server.config import config_manager; db = DatabaseManager(config_manager.config.database); db.initialize()"
```

#### 使用 SQLite（开发环境）

```bash
# 1. 配置 .env 文件
DB_TYPE=sqlite
DATABASE_PATH=data/timao.db

# 2. 自动创建数据库表
python -c "from server.app.database import DatabaseManager; from server.config import config_manager; db = DatabaseManager(config_manager.config.database); db.initialize()"
```

### 5️⃣ 启动服务

#### 开发模式

```bash
npm run dev
```

#### 生产模式

```bash
# 构建前端
npm run build

# 启动后端服务
cd server
uvicorn app.main:app --host 0.0.0.0 --port {PORT} --workers 4

> 默认端口为 9019，可通过环境变量 `BACKEND_PORT` 修改
```

---

## 🐳 Docker 部署

### 使用 Docker Compose（推荐）

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 使用 Dockerfile

```bash
# 构建镜像
docker build -t timao-live-manager .

# 运行容器
docker run -d \
  --name timao-app \
  -p 30013:30013 \
  -p {PORT}:{PORT} \

> 默认端口为 9019，可通过环境变量 `BACKEND_PORT` 修改
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env \
  timao-live-manager
```

---

## 🔐 安全配置

### 1. 密钥管理

**生产环境必须设置：**

```bash
# .env 文件
SECRET_KEY=<64位随机字符串，用于JWT签名>
ENCRYPTION_KEY=<32位随机字符串，用于数据加密>
```

**不要：**
- ❌ 使用默认密钥
- ❌ 将 `.env` 文件提交到 Git
- ❌ 在代码中硬编码密钥

### 2. 数据库备份

```bash
# 定期备份数据库
sqlite3 data/timao.db ".backup data/timao_backup_$(date +%Y%m%d).db"

# 自动备份（Cron）
0 2 * * * sqlite3 /path/to/data/timao.db ".backup /path/to/backups/timao_$(date +\%Y\%m\%d).db"
```

### 3. Redis 配置（可选）

```bash
# 启用 Redis 会话管理
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 如果不配置 Redis，系统将使用内存存储（不推荐生产环境）
```

---

## 📊 服务监控

### 健康检查

```bash
# API 健康检查
curl http://localhost:{PORT}/health

> 默认端口为 9019，可通过环境变量 `BACKEND_PORT` 修改

# 前端服务检查
curl http://localhost:30013
```

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log
```

---

## 🔧 数据库迁移

### 使用 Alembic（推荐）

```bash
# 安装 Alembic
pip install alembic

# 初始化迁移环境
alembic init alembic

# 生成迁移脚本
alembic revision --autogenerate -m "初始化数据库"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

---

## 🌐 反向代理配置

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端服务
    location / {
        proxy_pass http://localhost:30013;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://localhost:{PORT};  # 默认端口为 9019，可通过环境变量 `BACKEND_PORT` 修改
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket 支持
    location /ws/ {
        proxy_pass http://localhost:{PORT};  # 默认端口为 9019，可通过环境变量 `BACKEND_PORT` 修改
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### HTTPS 配置（Let's Encrypt）

```bash
# 安装 Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取 SSL 证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 🐛 常见问题

### 1. 数据库连接失败

**问题**：`Database not initialized`

**解决**：
```bash
# 检查数据库路径
echo $DATABASE_PATH

# 手动初始化
python -c "from server.app.database import DatabaseManager; from server.config import config_manager; db = DatabaseManager(config_manager.config.database); db.initialize()"
```

### 2. 导入路径错误

**问题**：`ImportError: No module named 'server'`

**解决**：
```bash
# 设置 PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 或在 .env 中添加
echo "PYTHONPATH=$(pwd)" >> .env
```

### 3. JWT 签名失败

**问题**：`SECRET_KEY 未设置`

**解决**：
```bash
# 在 .env 中设置
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))")
echo "SECRET_KEY=$SECRET_KEY" >> .env
```

### 4. Redis 连接失败

**问题**：Redis 不可用，使用内存存储

**解决**：
```bash
# 启动 Redis
sudo systemctl start redis

# 或在 Docker 中启动
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

---

## 📈 性能优化

### 1. 数据库优化

```sql
-- 启用 WAL 模式（已默认启用）
PRAGMA journal_mode=WAL;

-- 优化查询
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_subscription_user_id ON subscriptions(user_id);
```

### 2. 应用优化

```python
# 使用连接池
pool_size=20  # 根据并发量调整
pool_timeout=30

# 启用缓存
REDIS_CACHE_ENABLED=true
REDIS_CACHE_TTL=3600
```

### 3. Nginx 优化

```nginx
# 启用 gzip 压缩
gzip on;
gzip_types text/plain text/css application/json application/javascript;

# 设置缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

---

## 🔄 更新部署

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade
npm install

# 运行数据库迁移
alembic upgrade head

# 重启服务
docker-compose restart
# 或
pm2 restart timao-app
```

---

## 📞 技术支持

- **GitHub Issues**: https://github.com/Wike-CHI/timao-douyin-live-manager/issues
- **文档**: 查看项目 [README.md](README.md) 和 [QUICK_START.md](QUICK_START.md)
- **监控界面**: 
  - AI 网关: http://localhost:{PORT}/static/ai_gateway_manager.html
  - 成本监控: http://localhost:{PORT}/static/ai_usage_monitor.html
  - API 文档: http://localhost:{PORT}/docs

> 默认端口为 9019，可通过环境变量 `BACKEND_PORT` 修改

---

## ✅ 部署检查清单

- [ ] 设置 `SECRET_KEY` 环境变量
- [ ] 设置 `ENCRYPTION_KEY` 环境变量
- [ ] 配置 AI 服务商 API Key
- [ ] 初始化数据库
- [ ] 配置 Redis（可选）
- [ ] 设置反向代理（生产环境）
- [ ] 配置 HTTPS 证书（生产环境）
- [ ] 配置数据库备份
- [ ] 配置日志轮转
- [ ] 设置监控告警

---

**部署完成后，访问：**
- 前端界面: http://localhost:30013
- API 文档: http://localhost:{PORT}/docs
- 健康检查: http://localhost:{PORT}/health

> 默认端口为 9019，可通过环境变量 `BACKEND_PORT` 修改
