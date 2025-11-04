# 提猫直播助手 - Docker 部署指南

## 📦 快速启动

### 方式一：使用 Docker Compose（推荐）

```bash
# 构建并启动服务
docker-compose up --build

# 后台运行
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方式二：使用 Docker 命令

```bash
# 构建镜像
docker build -t timao-live-manager:latest .

# 运行容器
docker run -d \
  --name timao-douyin-live-manager \
  -p 30013:30013 \
  -p {PORT}:{PORT} \

> 默认端口为 9019，可通过环境变量 `BACKEND_PORT` 修改
  -p 5000:5000 \
  -v $(pwd):/app \
  -v /app/node_modules \
  -v /app/electron/renderer/node_modules \
  timao-live-manager:latest

# 查看日志
docker logs -f timao-douyin-live-manager

# 停止容器
docker stop timao-douyin-live-manager

# 删除容器
docker rm timao-douyin-live-manager
```

## 🌐 访问服务

启动成功后，可以通过以下地址访问：

- **前端界面**: http://localhost:30013
- **FastAPI 后端**: http://localhost:{PORT}
- **FastAPI 文档**: http://localhost:{PORT}/docs

> 默认端口为 9019，可通过环境变量 `BACKEND_PORT` 修改
- **Flask 服务** (如使用): http://localhost:5000

## 🔧 环境变量配置

创建 `.env` 文件来配置环境变量：

```env
# AI 服务密钥
OPENAI_API_KEY=your_openai_key
DASHSCOPE_API_KEY=your_dashscope_key
BAIDU_APP_ID=your_baidu_app_id
BAIDU_API_KEY=your_baidu_api_key
BAIDU_SECRET_KEY=your_baidu_secret_key

# ACRCloud 配置
ACRCLOUD_ACCESS_KEY=your_acrcloud_key
ACRCLOUD_ACCESS_SECRET=your_acrcloud_secret
ACRCLOUD_HOST=your_acrcloud_host

# 其他配置
NODE_ENV=development
PYTHONUNBUFFERED=1
```

然后在 `docker-compose.yml` 中引用：

```yaml
environment:
  - OPENAI_API_KEY=${OPENAI_API_KEY}
  - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
```

## 📝 技术栈

- **Python**: 3.10.9
- **Node.js**: 18.20.2
- **前端框架**: React + Vite + TypeScript
- **后端框架**: FastAPI + Flask
- **桌面框架**: Electron
- **AI模型**: SenseVoice, LangChain
- **音频处理**: FFmpeg, PyAudio

## 🔍 常见问题

### 1. 端口冲突

如果端口已被占用，修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "8013:30013"  # 将主机端口改为 8013
  - "{PORT}:{PORT}"  # 默认端口为 9019，可通过环境变量 `BACKEND_PORT` 修改
```

### 2. 音频设备访问（Linux）

如需访问音频设备，在 `docker-compose.yml` 中启用设备映射：

```yaml
devices:
  - /dev/snd:/dev/snd
privileged: true
```

### 3. 内存不足

如果构建失败，可能是内存不足。建议分配至少 4GB 内存给 Docker。

### 4. 依赖安装慢

可以使用国内镜像源加速：

在 Dockerfile 中添加：

```dockerfile
# Python 镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# npm 镜像源
RUN npm config set registry https://registry.npmmirror.com
```

### 5. 开发模式热更新

当前配置已启用代码卷挂载，修改代码后会自动热更新。

## 🚀 生产环境部署

生产环境建议：

1. 使用多阶段构建优化镜像大小
2. 移除开发依赖
3. 使用环境变量管理敏感信息
4. 启用 HTTPS
5. 配置日志收集
6. 设置资源限制

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

## 📊 监控和日志

```bash
# 实时查看日志
docker-compose logs -f

# 查看资源使用
docker stats timao-douyin-live-manager

# 进入容器调试
docker exec -it timao-douyin-live-manager bash
```

## 🛠️ 故障排查

```bash
# 检查容器状态
docker ps -a

# 查看详细日志
docker logs --tail 100 timao-douyin-live-manager

# 重新构建（不使用缓存）
docker-compose build --no-cache

# 清理并重新启动
docker-compose down -v
docker-compose up --build
```

## 📌 注意事项

1. 首次构建可能需要 10-20 分钟，主要是安装 PyTorch 等大型依赖
2. 确保 Docker Desktop 有足够的磁盘空间（建议至少 10GB）
3. Windows/Mac 用户需在 Docker Desktop 中配置文件共享
4. 音频设备访问在 Windows/Mac 的 Docker 中可能受限
5. GPU 支持需要使用 NVIDIA Container Toolkit（另需配置）

## 🔗 相关资源

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [项目主 README](./README.md)
