# 提猫直播助手 - Docker 镜像
# Timao Douyin Live Manager - Docker Image

# 使用官方 Python 3.10.9 基础镜像
FROM python:3.10.9-slim-bullseye

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NODE_VERSION=18.20.2 \
    NPM_CONFIG_LOGLEVEL=warn \
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 基础工具
    curl \
    wget \
    git \
    build-essential \
    cmake \
    pkg-config \
    # 音频处理依赖
    ffmpeg \
    portaudio19-dev \
    libsndfile1 \
    libasound2-dev \
    # 图像处理依赖
    libjpeg-dev \
    libpng-dev \
    # 其他系统库
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 安装 Node.js 和 npm
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.all.txt ./
COPY package*.json ./
COPY acrcloud_sdk_python/ ./acrcloud_sdk_python/

# 安装 Python 依赖
RUN pip install --upgrade pip setuptools wheel && \
    # 先安装 torch（可能需要较长时间）
    pip install torch==2.0.0 torchaudio==2.0.0 --index-url https://download.pytorch.org/whl/cpu && \
    # 安装其他依赖
    pip install -r requirements.all.txt && \
    # 清理缓存
    pip cache purge

# 复制 electron/renderer 的 package.json
COPY electron/renderer/package*.json ./electron/renderer/

# 安装 Node.js 依赖（根目录）
RUN npm install

# 安装 renderer 子项目依赖
RUN cd electron/renderer && npm install

# 复制项目文件
COPY . .

# 暴露端口
# 30013: Vite 前端开发服务器
# 10090: FastAPI 后端服务
# 5000: Flask 服务（如果使用）
EXPOSE 30013 10090 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:30013/ || exit 1

# 启动命令
CMD ["npm", "run", "dev"]
