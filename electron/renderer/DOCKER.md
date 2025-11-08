# 🐳 前端 Docker 部署指南

**遵循：奥卡姆剃刀 + 希克定律**

> 最简单的 Docker 部署方案，自动构建和配置

---

## 🎯 一键部署（3步）

### 第1步：配置环境变量（只需1项）

```bash
cd electron/renderer
cp env.production.template .env
# 编辑 .env，只配置后端地址：
```

**必需配置（1项）**：

```env
BACKEND_URL=http://backend:11111
# 如果前后端分离部署，使用实际地址：
# BACKEND_URL=http://your-backend-server.com:11111
```

### 第2步：一键部署

```bash
chmod +x scripts/docker_deploy.sh
./scripts/docker_deploy.sh
```

### 第3步：验证部署

```bash
# 健康检查
curl http://localhost/health

# 访问前端
# 浏览器打开: http://localhost
```

---

## 📋 手动部署

### 1. 构建镜像

```bash
docker build \
  --build-arg VITE_FASTAPI_URL=http://backend:11111 \
  --build-arg VITE_STREAMCAP_URL=http://backend:11111 \
  --build-arg VITE_DOUYIN_URL=http://backend:11111 \
  -t timao-frontend:latest .
```

### 2. 启动服务

```bash
docker-compose up -d
```

---

## 🔧 前后端通信配置

### 方式1：Docker 网络内通信（推荐）

如果前后端在同一 Docker 网络中：

```yaml
# docker-compose.yml
services:
  frontend:
    build:
      args:
        VITE_FASTAPI_URL: http://backend:11111
    networks:
      - timao-network
```

### 方式2：外部地址通信

如果前后端分离部署：

```yaml
# docker-compose.yml
services:
  frontend:
    build:
      args:
        VITE_FASTAPI_URL: http://your-backend-server.com:11111
```

### 方式3：Nginx 代理

前端 Nginx 可以代理 API 请求到后端：

```nginx
location /api/ {
    proxy_pass ${BACKEND_URL}/api/;
}
```

---

## 📊 构建过程

1. ✅ 安装 Node.js 18
2. ✅ 安装依赖（npm ci）
3. ✅ 构建前端（npm run build）
4. ✅ 使用 Nginx 服务静态文件

---

## 🛠️ 常用命令

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker logs -f timao-frontend

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 重建镜像
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔍 故障排查

### 问题1：无法连接后端

**检查**：
1. 后端地址是否正确
2. 后端服务是否运行
3. 网络是否可达

**解决**：
```bash
# 检查后端连接
curl http://your-backend-url:11111/health

# 查看前端日志
docker logs timao-frontend
```

### 问题2：构建失败

**解决**：
```bash
# 清理缓存重建
docker-compose build --no-cache
```

---

## ✅ 部署检查清单

- [ ] Docker 已安装
- [ ] `.env` 文件已配置（后端地址）
- [ ] 镜像构建成功
- [ ] 服务启动成功
- [ ] 健康检查通过
- [ ] 可以访问前端

---

## 🎯 部署原则

1. **奥卡姆剃刀**：最简单的 Dockerfile，最少的步骤
2. **希克定律**：只配置1个必需项（后端地址）
3. **自动化**：构建时自动注入配置

---

**记住：只需配置后端地址，其他自动完成！**

