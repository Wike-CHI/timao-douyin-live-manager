# 🐳 Docker 快速部署指南

**遵循：奥卡姆剃刀 + 希克定律**

> 最简单的 Docker 部署方案，自动安装所有依赖和模型

---

## 🎯 一键部署（3步）

### 第1步：配置环境变量（只需6项）

```bash
cd server
cp env.production.template .env
# 编辑 .env，只修改这6项：
```

**必需配置（6项）**：

```env
BACKEND_PORT=11111
MYSQL_HOST=你的数据库地址
MYSQL_USER=timao
MYSQL_PASSWORD=你的密码
MYSQL_DATABASE=timao
SECRET_KEY=你的密钥（生产环境必须改）
```

### 第2步：一键部署

```bash
chmod +x scripts/docker_deploy.sh
./scripts/docker_deploy.sh
```

**脚本会自动**：
- ✅ 检查 Docker 环境
- ✅ 创建必要目录
- ✅ 构建镜像（包含模型下载）
- ✅ 启动服务
- ✅ 健康检查

### 第3步：验证部署

```bash
# 健康检查
curl http://localhost:11111/health

# 查看日志
docker logs -f timao-backend
```

---

## 📋 手动部署

### 1. 构建镜像

```bash
docker build -t timao-backend:latest .
```

**构建过程会自动**：
- ✅ 安装 Python 3.11.9
- ✅ 安装所有依赖（requirements.txt）
- ✅ 安装 ffmpeg
- ✅ 下载 SenseVoice 模型
- ✅ 下载 VAD 模型

### 2. 启动服务

```bash
# 使用 docker-compose（推荐）
docker-compose up -d

# 或直接运行
docker run -d \
  --name timao-backend \
  -p 11111:11111 \
  --env-file .env \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/records:/app/records \
  timao-backend:latest
```

---

## 🔧 Docker Compose 配置

`docker-compose.yml` 已配置：

- ✅ 自动重启（`restart: unless-stopped`）
- ✅ 健康检查
- ✅ 数据持久化（模型、日志、录制文件）
- ✅ 环境变量自动加载（`.env` 文件）

---

## 📊 数据持久化

以下目录会自动挂载到宿主机：

- `./models` → 模型文件（避免重复下载）
- `./logs` → 日志文件
- `./records` → 录制文件

---

## 🛠️ 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker logs -f timao-backend

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps

# 进入容器
docker exec -it timao-backend bash

# 重建镜像（更新代码后）
docker-compose build --no-cache
docker-compose up -d

# 仅构建镜像（不启动）
./scripts/docker_build.sh

# 生产环境部署
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔍 故障排查

### 问题1：模型下载失败

**原因**：构建时网络问题

**解决**：
```bash
# 模型会在运行时自动下载
# 或手动进入容器下载
docker exec -it timao-backend bash
python tools/download_sensevoice.py
python tools/download_vad_model.py
```

### 问题2：端口被占用

**解决**：修改 `.env` 中的 `BACKEND_PORT`

### 问题3：数据库连接失败

**解决**：检查 `.env` 中的数据库配置

### 问题4：查看详细日志

```bash
docker logs timao-backend
docker-compose logs -f backend
```

---

## 📦 镜像信息

当前镜像包含：
- ✅ Python 3.11.9
- ✅ 所有 Python 依赖（requirements.txt）
- ✅ ffmpeg（系统级安装）
- ✅ SenseVoice 模型（自动下载）
- ✅ VAD 模型（自动下载）

**总大小约 3-4GB**（包含模型文件）

**注意**：模型文件会持久化到 `./models` 目录，避免重复下载。

---

## ✅ 部署检查清单

- [ ] Docker 和 Docker Compose 已安装
- [ ] `.env` 文件已配置（6个必需项）
- [ ] 镜像构建成功
- [ ] 服务启动成功
- [ ] 健康检查通过
- [ ] 模型文件已下载（检查 `models/models/iic/`）

---

## 🎯 部署原则

1. **奥卡姆剃刀**：最简单的 Dockerfile，最少的步骤
2. **希克定律**：只配置6个必需项，其他使用默认值
3. **自动化**：构建时自动下载模型，无需手动操作

---

## 📞 支持

如有问题，检查：

1. Docker 版本 >= 20.10
2. `.env` 文件是否正确
3. 数据库是否可访问
4. 端口是否被占用

**记住：只需配置6项，其他自动完成！**

