# 🐳 前后端完整 Docker 部署指南

**遵循：奥卡姆剃刀 + 希克定律**

> 最简单的完整部署方案，一键启动前后端

---

## 🎯 一键部署（3步）

### 第1步：配置环境变量（只需6项）

```bash
# 后端配置
cd server
cp env.production.template .env
# 编辑 server/.env，配置6个必需项

# 返回项目根目录
cd ../..
```

**后端必需配置（6项）**：

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
# 在项目根目录
docker-compose -f docker-compose.full.yml up -d --build
```

### 第3步：验证部署

```bash
# 后端健康检查
curl http://localhost:11111/health

# 前端健康检查
curl http://localhost/health

# 访问前端
# 浏览器打开: http://localhost
```

---

## 📋 配置说明

### 必需配置（6项）

**后端** (`server/.env`):
1. ✅ `BACKEND_PORT=11111`
2. ✅ `MYSQL_HOST=数据库地址`
3. ✅ `MYSQL_USER=timao`
4. ✅ `MYSQL_PASSWORD=密码`
5. ✅ `MYSQL_DATABASE=timao`
6. ✅ `SECRET_KEY=密钥（生产环境必须改）`

**前端**（自动配置）:
- ✅ 后端地址自动设置为 `http://backend:11111`（Docker 网络内）
- ✅ 前端端口默认 `80`（可通过 `FRONTEND_PORT` 环境变量修改）

---

## 🔧 前后端通信

### Docker 网络内通信

前后端在同一 Docker 网络中，通过服务名通信：

- 前端 → 后端: `http://backend:11111`
- 后端端口映射: `11111:11111`（宿主机访问）
- 前端端口映射: `80:80`（宿主机访问）

### 环境变量配置

前端构建时会注入后端地址：

```yaml
build:
  args:
    VITE_FASTAPI_URL: http://backend:11111
    VITE_STREAMCAP_URL: http://backend:11111
    VITE_DOUYIN_URL: http://backend:11111
```

### Nginx 代理（可选）

如果需要在 Nginx 中代理 API 请求：

```nginx
location /api/ {
    proxy_pass http://backend:11111/api/;
}
```

---

## 🛠️ 常用命令

```bash
# 启动所有服务
docker-compose -f docker-compose.full.yml up -d

# 停止所有服务
docker-compose -f docker-compose.full.yml down

# 查看日志
docker-compose -f docker-compose.full.yml logs -f

# 查看后端日志
docker logs -f timao-backend

# 查看前端日志
docker logs -f timao-frontend

# 重启服务
docker-compose -f docker-compose.full.yml restart

# 重建镜像
docker-compose -f docker-compose.full.yml build --no-cache
docker-compose -f docker-compose.full.yml up -d
```

---

## 🔍 故障排查

### 问题1：前端无法连接后端

**检查**：
1. 后端服务是否启动：`docker ps | grep backend`
2. 后端健康检查：`curl http://localhost:11111/health`
3. 前端日志：`docker logs timao-frontend`

**解决**：
```bash
# 检查网络连接
docker network inspect timao-douyin-live-manager_timao-network

# 测试后端连接（从前端容器）
docker exec -it timao-frontend wget -O- http://backend:11111/health
```

### 问题2：CORS 错误

**原因**：后端 CORS 配置不允许前端域名

**解决**：确保后端 `.env` 中配置：

```env
CORS_ORIGINS=*
# 或具体域名
CORS_ORIGINS=http://localhost,http://your-domain.com
```

### 问题3：端口冲突

**解决**：修改端口映射

```bash
# 修改 docker-compose.full.yml
ports:
  - "8080:80"  # 前端改为 8080
  - "11112:11111"  # 后端改为 11112
```

---

## 📊 架构说明

```
┌─────────────────┐
│   浏览器/客户端   │
│  http://localhost│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  前端 (Nginx)    │
│  端口: 80       │
│  容器: frontend │
└────────┬────────┘
         │
         │ Docker 网络
         │ http://backend:11111
         ▼
┌─────────────────┐
│  后端 (FastAPI)  │
│  端口: 11111    │
│  容器: backend  │
└─────────────────┘
```

---

## ✅ 部署检查清单

- [ ] Docker 和 Docker Compose 已安装
- [ ] `server/.env` 已配置（6个必需项）
- [ ] 后端镜像构建成功
- [ ] 前端镜像构建成功
- [ ] 所有服务启动成功
- [ ] 后端健康检查通过
- [ ] 前端健康检查通过
- [ ] 前后端可以通信

---

## 🎯 部署原则

1. **奥卡姆剃刀**：最简单的 Docker Compose 配置
2. **希克定律**：只配置6个必需项，其他自动处理
3. **自动化**：前后端自动连接，无需手动配置

---

## 📞 支持

如有问题，检查：

1. Docker 版本 >= 20.10
2. `server/.env` 文件是否正确
3. 数据库是否可访问
4. 端口是否被占用
5. Docker 网络是否正常

**记住：只需配置6项，其他自动完成！**

