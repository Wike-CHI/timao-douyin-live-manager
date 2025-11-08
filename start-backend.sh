#!/bin/bash
# 启动后端服务 - 端口 11111
# 设置环境变量以修复 UMAP/numba 兼容性问题

cd /www/wwwroot/wwwroot/timao-douyin-live-manager/server

# 激活虚拟环境
source ../.venv/bin/activate

# 设置环境变量（修复 Python 3.11 + numba 兼容性问题）
export UMAP_DONT_USE_NUMBA=1
export NUMBA_DISABLE_JIT=1

echo "🚀 启动后端服务..."
echo "   - 端口: 11111"
echo "   - 环境变量已设置: UMAP_DONT_USE_NUMBA=1, NUMBA_DISABLE_JIT=1"
echo ""

# 启动后端
python -m uvicorn app.main:app --host 127.0.0.1 --port 11111 --reload

