#!/bin/bash
# ============================================
# Docker 镜像构建脚本（单独构建，不启动）
# 遵循：奥卡姆剃刀 - 最简单的构建
# ============================================

set -e

echo "🐳 构建 Docker 镜像..."
echo "这可能需要几分钟（下载模型文件）..."

docker build -t timao-backend:latest .

if [ $? -eq 0 ]; then
    echo "✅ 镜像构建成功"
    echo ""
    echo "启动服务："
    echo "  docker-compose up -d"
else
    echo "❌ 镜像构建失败"
    exit 1
fi

