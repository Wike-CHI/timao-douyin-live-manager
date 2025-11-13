#!/bin/bash
# 服务器端快速启动脚本
# 使用方法: ./scripts/构建与启动/server-start.sh

set -e

BACKEND_PORT=10050
SERVER_PATH="/opt/timao-douyin-live-manager"

echo "🚀 启动后端服务..."
echo "   端口: ${BACKEND_PORT}"
echo "   路径: ${SERVER_PATH}"
echo ""

cd ${SERVER_PATH}/server

# 设置环境变量
export BACKEND_PORT=${BACKEND_PORT}
export DEBUG=false
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

# 激活虚拟环境（如果存在）
if [ -d "../.venv" ]; then
    echo "📦 激活虚拟环境..."
    source ../.venv/bin/activate
fi

# 检查依赖
if [ ! -d "../.venv" ]; then
    echo "⚠️  未找到虚拟环境，使用全局Python"
fi

# 启动服务
echo "🚀 启动服务..."
python -m uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT}

