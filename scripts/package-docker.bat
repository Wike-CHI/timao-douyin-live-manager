@echo off
chcp 65001 > nul
echo ========================================
echo 提猫直播助手 - Docker容器化打包
echo ========================================

:: 检查Docker环境
docker --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Docker，请先安装Docker Desktop
    pause
    exit /b 1
)

echo [信息] 开始Docker容器化打包...

:: 1. 创建Dockerfile
echo [步骤1] 创建Dockerfile...
(
echo # 提猫直播助手 Docker镜像
echo FROM node:18-alpine AS frontend-builder
echo WORKDIR /app/frontend
echo COPY electron/renderer/package*.json ./
echo RUN npm install
echo COPY electron/renderer/ ./
echo RUN npm run build
echo.
echo FROM python:3.9-slim
echo WORKDIR /app
echo.
echo # 安装系统依赖
echo RUN apt-get update ^&^& apt-get install -y \
echo     curl \
echo     nodejs \
echo     npm \
echo     ^&^& rm -rf /var/lib/apt/lists/*
echo.
echo # 复制应用文件
echo COPY server/ ./server/
echo COPY DouyinLiveWebFetcher/ ./DouyinLiveWebFetcher/
echo COPY AST_module/ ./AST_module/
echo COPY requirements.txt ./
echo COPY package.json ./
echo.
echo # 复制前端构建文件
echo COPY --from=frontend-builder /app/frontend/dist ./frontend/
echo.
echo # 安装Python依赖
echo RUN pip install --no-cache-dir -r requirements.txt
echo.
echo # 安装Node.js依赖
echo RUN npm install --production
echo.
echo # 创建数据目录
echo RUN mkdir -p /app/data /app/logs
echo.
echo # 暴露端口
echo EXPOSE 10090
echo.
echo # 启动命令
echo CMD ["python", "-m", "uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "10090"]
) > Dockerfile

:: 2. 创建docker-compose.yml
echo [步骤2] 创建docker-compose.yml...
(
echo version: '3.8'
echo services:
echo   talkingcat:
echo     build: .
echo     ports:
echo       - "10090:10090"
echo     volumes:
echo       - ./data:/app/data
echo       - ./logs:/app/logs
echo       - ./config:/app/config
echo     environment:
echo       - AI_SERVICE=qwen
echo       - AI_API_KEY=sk-92045f0a33984350925ce3ccffb3489e
echo       - AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
echo       - AI_MODEL=qwen3-max
echo       - DATABASE_TYPE=sqlite
echo       - DATABASE_PATH=/app/data/local.db
echo     restart: unless-stopped
echo     healthcheck:
echo       test: ["CMD", "curl", "-f", "http://localhost:10090/api/health"]
echo       interval: 30s
echo       timeout: 10s
echo       retries: 3
echo.
echo   nginx:
echo     image: nginx:alpine
echo     ports:
echo       - "80:80"
echo     volumes:
echo       - ./nginx.conf:/etc/nginx/nginx.conf
echo       - ./frontend:/usr/share/nginx/html
echo     depends_on:
echo       - talkingcat
echo     restart: unless-stopped
) > docker-compose.yml

:: 3. 创建nginx配置
echo [步骤3] 创建nginx配置...
mkdir nginx 2>nul
(
echo events {
echo     worker_connections 1024;
echo }
echo.
echo http {
echo     upstream backend {
echo         server talkingcat:10090;
echo     }
echo.
echo     server {
echo         listen 80;
echo         server_name localhost;
echo.
echo         location / {
echo             root /usr/share/nginx/html;
echo             index index.html;
echo             try_files $uri $uri/ /index.html;
echo         }
echo.
echo         location /api/ {
echo             proxy_pass http://backend;
echo             proxy_set_header Host $host;
echo             proxy_set_header X-Real-IP $remote_addr;
echo             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
echo         }
echo.
echo         location /ws/ {
echo             proxy_pass http://backend;
echo             proxy_http_version 1.1;
echo             proxy_set_header Upgrade $http_upgrade;
echo             proxy_set_header Connection "upgrade";
echo             proxy_set_header Host $host;
echo         }
echo     }
echo }
) > nginx.conf

:: 4. 构建Docker镜像
echo [步骤4] 构建Docker镜像...
docker build -t talkingcat:latest .
if %errorlevel% neq 0 (
    echo [错误] Docker镜像构建失败
    pause
    exit /b 1
)

:: 5. 创建启动脚本
echo [步骤5] 创建启动脚本...
(
echo @echo off
echo echo 启动提猫直播助手Docker容器...
echo docker-compose up -d
echo echo.
echo echo 服务已启动！
echo echo 前端访问地址: http://localhost
echo echo API访问地址: http://localhost/api
echo echo.
echo echo 查看日志: docker-compose logs -f
echo echo 停止服务: docker-compose down
) > start-docker.bat

echo ========================================
echo Docker容器化打包完成！
echo 使用方法：
echo 1. 运行 start-docker.bat 启动服务
echo 2. 访问 http://localhost 使用应用
echo ========================================
pause