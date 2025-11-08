# 🚀 快速部署指南

**遵循：奥卡姆剃刀 + 希克定律**

> 最简单的部署方案，最少的配置选择

## 📋 部署前准备

### 必需项（6个配置）

1. ✅ Python 3.8+
2. ✅ MySQL 数据库（已配置）
3. ✅ `.env` 配置文件（只需6个必需项）

### 可选项（稍后配置）

- AI 服务密钥（Gemini/OpenAI）
- Redis（可选，默认使用内存缓存）

---

## 🎯 一键部署（3步）

### Linux / macOS

```bash
# 1. 进入 server 目录
cd server

# 2. 运行部署脚本
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 3. 启动服务
source .venv/bin/activate
python server/app/main.py
```

### Windows

```powershell
# 1. 进入 server 目录
cd server

# 2. 运行部署脚本
.\scripts\deploy.ps1

# 3. 启动服务
.venv\Scripts\Activate.ps1
python server\app\main.py
```

---

## 📝 手动部署（如果脚本失败）

### 1. 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\Activate.ps1  # Windows
```

### 2. 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制模板
cp env.production.template .env

# 编辑 .env，只修改这6个必需项：
# - BACKEND_PORT=11111
# - MYSQL_HOST=你的数据库地址
# - MYSQL_USER=timao
# - MYSQL_PASSWORD=你的密码
# - MYSQL_DATABASE=timao
# - SECRET_KEY=你的密钥（生产环境必须改）
```

### 4. 验证配置

```bash
python -c "from server.app.database import engine; engine.connect()"
```

### 5. 启动服务

```bash
python server/app/main.py
```

---

## 🔧 生产环境部署（systemd）

### 1. 创建服务文件

```bash
sudo nano /etc/systemd/system/timao-backend.service
```

内容：

```ini
[Unit]
Description=提猫直播助手后端服务
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/timao-douyin-live-manager/server
Environment="PATH=/path/to/timao-douyin-live-manager/server/.venv/bin"
ExecStart=/path/to/timao-douyin-live-manager/server/.venv/bin/python -m uvicorn server.app.main:app --host 0.0.0.0 --port 11111
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. 启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable timao-backend
sudo systemctl start timao-backend
sudo systemctl status timao-backend
```

### 3. 查看日志

```bash
sudo journalctl -u timao-backend -f
```

---

## 🌐 Nginx 反向代理（可选）

如果需要通过域名访问：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:11111;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /api/live_audio/ws {
        proxy_pass http://127.0.0.1:11111;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## ✅ 验证部署

### 1. 健康检查

```bash
curl http://localhost:11111/health
```

应该返回：

```json
{"status": "ok"}
```

### 2. API 文档

访问：`http://localhost:11111/docs`

---

## 🔍 故障排查

### 问题1：端口被占用

```bash
# 检查端口
netstat -tulpn | grep 11111  # Linux
# 或
lsof -i :11111  # macOS

# 修改端口（在 .env 中）
BACKEND_PORT=11112
```

### 问题2：数据库连接失败

```bash
# 测试连接
python -c "
from server.app.database import engine
with engine.connect() as conn:
    print('✅ 连接成功')
"
```

### 问题3：依赖安装失败

```bash
# 升级 pip
pip install --upgrade pip setuptools wheel

# 单独安装失败的包
pip install package-name
```

---

## 📊 最小化配置清单

**只需配置这6项**（遵循希克定律）：

1. ✅ `BACKEND_PORT=11111`
2. ✅ `MYSQL_HOST=你的数据库地址`
3. ✅ `MYSQL_USER=timao`
4. ✅ `MYSQL_PASSWORD=你的密码`
5. ✅ `MYSQL_DATABASE=timao`
6. ✅ `SECRET_KEY=你的密钥（生产环境必须改）`

**其他配置都有合理默认值，可稍后调整。**

---

## 🎯 部署原则

1. **奥卡姆剃刀**：最简单的方案，最少的步骤
2. **希克定律**：只配置必需的6项，其他使用默认值
3. **KISS**：一键脚本，自动化流程

---

## 📞 支持

如有问题，检查：

1. `.env` 文件是否正确
2. 数据库是否可访问
3. 端口是否被占用
4. Python 版本是否 >= 3.8

