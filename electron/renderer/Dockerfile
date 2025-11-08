# ============================================
# 提猫直播助手 - 前端 Docker 镜像
# 遵循：奥卡姆剃刀 + 希克定律
# ============================================
# 构建前端静态文件，使用 Nginx 服务

# 构建阶段
FROM node:18-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm ci --only=production=false

# 复制源代码
COPY . .

# 构建前端（环境变量在构建时注入）
ARG VITE_FASTAPI_URL=http://127.0.0.1:11111
ARG VITE_STREAMCAP_URL=http://127.0.0.1:11111
ARG VITE_DOUYIN_URL=http://127.0.0.1:11111

ENV VITE_FASTAPI_URL=$VITE_FASTAPI_URL
ENV VITE_STREAMCAP_URL=$VITE_STREAMCAP_URL
ENV VITE_DOUYIN_URL=$VITE_DOUYIN_URL

# 构建
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]

