#!/bin/bash
# 安装CPU版本依赖（适用于云服务器）
# 解决 libcudart.so.11.0 依赖问题

set -e

echo "📦 安装CPU版本依赖..."
echo "   Python版本: $(python --version)"
echo ""

cd /www/wwwroot/wwwroot/timao-douyin-live-manager/server

# 激活虚拟环境
if [ -d "../.venv" ]; then
    source ../.venv/bin/activate
    echo "✅ 虚拟环境已激活"
else
    echo "⚠️  虚拟环境不存在，创建虚拟环境..."
    cd ..
    python -m venv .venv
    source .venv/bin/activate
    cd server
fi

echo ""
echo "🔄 卸载现有的torch（如果有）..."
pip uninstall -y torch torchaudio torchvision 2>/dev/null || true

echo ""
echo "📥 安装CPU版本的torch..."
pip install torch==2.5.1+cpu torchaudio==2.5.1+cpu torchvision==0.20.1+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

echo ""
echo "📥 安装其他依赖..."
pip install -r requirements.simple.txt

echo ""
echo "✅ 安装完成！"
echo ""
echo "🧪 验证安装..."
python -c "import torch; print(f'PyTorch版本: {torch.__version__}'); print(f'CUDA可用: {torch.cuda.is_available()}')"

echo ""
echo "📋 下一步："
echo "   重启后端服务"
echo "   export BACKEND_PORT=10050"
echo "   python -m uvicorn app.main:app --host 0.0.0.0 --port 10050"

