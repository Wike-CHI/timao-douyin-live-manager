#!/bin/bash
# ============================================
# 提猫直播助手 - 快速启动脚本
# 最简单的启动方式
# ============================================

set -e

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "❌ 虚拟环境不存在，请先运行 deploy.sh"
    exit 1
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "❌ .env 文件不存在，请先创建"
    exit 1
fi

# 启动服务
echo "🚀 启动提猫直播助手后端服务..."
python server/app/main.py

