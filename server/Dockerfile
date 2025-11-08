# ============================================
# 提猫直播助手 - Docker 镜像
# 遵循：奥卡姆剃刀 + 希克定律
# ============================================
# 自动安装 Python 3.11.9、依赖、ffmpeg、模型文件

FROM python:3.11.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（ffmpeg 和其他必需工具）
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 安装 ModelScope（用于下载模型）
RUN pip install --no-cache-dir modelscope

# 复制项目文件
COPY . .

# 创建模型目录
RUN mkdir -p models/models/iic models/.cache

# 设置 ModelScope 缓存目录（用于模型下载）
ENV MODELSCOPE_CACHE=/app/models/.cache
ENV MS_CACHE_HOME=/app/models/.cache

# 下载 SenseVoice 模型（在构建时下载，避免运行时延迟）
# 注意：如果下载失败，会在运行时自动下载
RUN cd /app && python tools/download_sensevoice.py || echo "⚠️ SenseVoice 模型下载失败，将在运行时下载"

# 下载 VAD 模型（在构建时下载，避免运行时延迟）
RUN cd /app && python tools/download_vad_model.py || echo "⚠️ VAD 模型下载失败，将在运行时下载"

# 设置环境变量默认值
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV BACKEND_PORT=11111
ENV DEBUG=false

# 暴露端口
EXPOSE 11111

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:11111/health || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "11111"]

