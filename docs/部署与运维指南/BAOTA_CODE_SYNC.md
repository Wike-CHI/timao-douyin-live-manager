# 🔄 宝塔 Python 项目代码同步说明

**遵循：奥卡姆剃刀 + KISS 原则**

> 简单说明：宝塔部署后代码改动如何同步

---

## ❓ 核心问题

**宝塔 Python 项目部署后，代码改动不会自动同步！**

需要手动同步代码，然后重启服务。

---

## 📋 宝塔 Python 项目部署机制

### 工作原理

1. **首次部署**：宝塔会：
   - 复制代码到项目目录（如：`/www/wwwroot/timao-backend`）
   - 创建虚拟环境
   - 安装依赖
   - 启动服务

2. **代码改动后**：
   - ❌ **不会自动同步**
   - ❌ **不会自动重启**
   - ✅ **需要手动操作**

---

## 🔄 代码同步方法

### 方法1：宝塔文件管理器（最简单）

1. 登录宝塔面板
2. 进入 **文件** → 找到项目目录
3. 上传修改后的文件（覆盖）
4. 重启 Python 项目

**优点**：简单直接，适合小改动  
**缺点**：手动操作，容易遗漏文件

### 方法2：Git 拉取（推荐）

如果项目使用 Git 管理：

```bash
# SSH 登录服务器
ssh root@129.211.218.135

# 进入项目目录
cd /www/wwwroot/timao-backend/server

# 拉取最新代码
git pull origin main

# 重启服务（在宝塔面板中操作，或使用命令）
```

**优点**：自动化，不会遗漏  
**缺点**：需要先提交到 Git

### 方法3：rsync 同步（适合频繁更新）

```bash
# 在本地执行（同步到服务器）
rsync -avz --exclude '.git' --exclude '__pycache__' \
  ./server/ root@129.211.218.135:/www/wwwroot/timao-backend/server/
```

**优点**：快速同步，可排除文件  
**缺点**：需要配置 SSH 密钥

---

## 🔄 重启服务

### 方法1：宝塔面板（推荐）

1. 进入 **网站** → **Python项目**
2. 找到你的项目
3. 点击 **重启** 按钮

### 方法2：命令行

```bash
# SSH 登录服务器
ssh root@129.211.218.135

# 查找进程
ps aux | grep uvicorn

# 重启（方法A：kill 后宝塔会自动重启）
kill -HUP <进程ID>

# 重启（方法B：使用 systemctl，如果配置了）
systemctl restart timao-backend
```

---

## ⚙️ 自动同步方案（可选）

### 方案1：Git Webhook（推荐）

在服务器上配置 Git Webhook，代码推送后自动拉取：

```bash
# 1. 创建 webhook 脚本
cat > /www/wwwroot/timao-backend/webhook.sh << 'EOF'
#!/bin/bash
cd /www/wwwroot/timao-backend/server
git pull origin main
# 重启服务（根据你的配置调整）
systemctl restart timao-backend
EOF

chmod +x /www/wwwroot/timao-backend/webhook.sh

# 2. 在 Git 仓库（GitHub/Gitee）配置 Webhook
# URL: http://129.211.218.135:8888/webhook（需要配置）
# 触发事件：push
```

### 方案2：定时拉取（简单但不够实时）

```bash
# 添加定时任务（每5分钟检查一次）
crontab -e

# 添加：
*/5 * * * * cd /www/wwwroot/timao-backend/server && git pull origin main
```

### 方案3：开发模式（自动重载）

如果使用开发模式，修改代码后会自动重载：

```bash
# 在 .env 中设置
DEBUG=true

# 或在启动命令中添加 --reload
uvicorn server.app.main:app --host 0.0.0.0 --port 11111 --reload
```

**注意**：生产环境不建议使用 `--reload`，性能较差。

---

## 📝 推荐工作流程

### 开发 → 部署流程

```bash
# 1. 本地开发
# 修改代码...

# 2. 提交到 Git
git add .
git commit -m "更新功能"
git push origin main

# 3. 服务器拉取（SSH 或 Webhook）
ssh root@129.211.218.135
cd /www/wwwroot/timao-backend/server
git pull origin main

# 4. 重启服务（宝塔面板或命令）
# 在宝塔面板点击"重启"
```

---

## 🎯 快速同步脚本

创建 `scripts/sync_to_baota.sh`：

```bash
#!/bin/bash
# 同步代码到宝塔服务器

SERVER="root@129.211.218.135"
REMOTE_PATH="/www/wwwroot/timao-backend/server"

echo "🔄 同步代码到服务器..."

# 同步代码
rsync -avz --exclude '.git' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.venv' \
  ./server/ $SERVER:$REMOTE_PATH/

echo "✅ 代码同步完成"
echo "💡 请在宝塔面板重启 Python 项目"
```

使用：

```bash
chmod +x scripts/sync_to_baota.sh
./scripts/sync_to_baota.sh
```

---

## ⚠️ 注意事项

### 1. 配置文件

`.env` 文件通常不会同步，需要单独配置：

```bash
# 在服务器上手动编辑
nano /www/wwwroot/timao-backend/server/.env
```

### 2. 依赖更新

如果添加了新依赖，需要重新安装：

```bash
cd /www/wwwroot/timao-backend/server
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. 数据库迁移

如果修改了数据库模型，需要运行迁移：

```bash
# 根据你的迁移工具调整
alembic upgrade head
# 或
python scripts/migrate.py
```

---

## 🔍 验证同步

### 检查代码是否更新

```bash
# SSH 登录服务器
ssh root@129.211.218.135

# 检查文件修改时间
ls -lh /www/wwwroot/timao-backend/server/app/main.py

# 或检查 Git 状态
cd /www/wwwroot/timao-backend/server
git log -1
```

### 检查服务是否重启

```bash
# 查看进程启动时间
ps aux | grep uvicorn

# 或查看日志
tail -f /www/wwwroot/timao-backend/server/logs/app.log
```

---

## 📊 总结

| 操作 | 是否自动 | 说明 |
|------|---------|------|
| 代码同步 | ❌ 否 | 需要手动上传或 Git pull |
| 服务重启 | ❌ 否 | 需要手动重启 |
| 依赖安装 | ❌ 否 | 需要手动安装 |
| 配置更新 | ❌ 否 | 需要手动修改 |

**推荐方案：**
1. ✅ 使用 Git 管理代码
2. ✅ 配置 Webhook 自动拉取
3. ✅ 手动重启服务（或配置自动重启）

---

## 💡 最佳实践

1. **开发环境**：使用 `--reload` 自动重载
2. **生产环境**：使用 Git + Webhook 自动同步
3. **紧急修复**：直接上传文件 + 手动重启
4. **定期备份**：代码和数据库都要备份

---

## 🎯 原则

- **奥卡姆剃刀**：最简单的方案（Git + 手动重启）
- **KISS**：不追求完全自动化，保持可控
- **YAGNI**：不需要复杂的 CI/CD，够用就行

