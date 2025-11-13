#!/bin/bash
# 简单部署脚本 - 部署后端到服务器
# 使用方法: ./scripts/部署与运维/deploy-server.sh

set -e

SERVER_IP="129.211.218.135"
SERVER_USER="root"
SERVER_PATH="/opt/timao-douyin-live-manager"
BACKEND_PORT="10050"

echo "🚀 开始部署后端到服务器..."

# 1. 检查SSH连接
echo "📡 检查SSH连接..."
ssh -o ConnectTimeout=5 ${SERVER_USER}@${SERVER_IP} "echo 'SSH连接成功'" || {
    echo "❌ SSH连接失败，请检查："
    echo "   1. 服务器IP是否正确: ${SERVER_IP}"
    echo "   2. SSH密钥是否配置"
    echo "   3. 服务器是否可访问"
    exit 1
}

# 2. 创建部署目录
echo "📁 创建部署目录..."
ssh ${SERVER_USER}@${SERVER_IP} "mkdir -p ${SERVER_PATH}"

# 3. 上传后端代码（排除前端和Electron）
echo "📤 上传后端代码..."
rsync -avz --progress \
    --exclude 'node_modules' \
    --exclude 'electron' \
    --exclude 'admin-dashboard' \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.venv' \
    --exclude 'dist' \
    --exclude '*.log' \
    ./ ${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/

# 4. 创建启动脚本
echo "📝 创建启动脚本..."
ssh ${SERVER_USER}@${SERVER_IP} "cat > ${SERVER_PATH}/scripts/构建与启动/start-backend.sh << 'EOF'
#!/bin/bash
cd ${SERVER_PATH}/server
export BACKEND_PORT=${BACKEND_PORT}
export DEBUG=false
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

# 激活虚拟环境（如果存在）
if [ -d '../.venv' ]; then
    source ../.venv/bin/activate
fi

# 安装依赖
pip install -r requirements.txt -q

# 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port ${BACKEND_PORT}
EOF
chmod +x ${SERVER_PATH}/scripts/构建与启动/start-backend.sh"

# 5. 创建systemd服务（可选）
echo "⚙️  创建systemd服务..."
ssh ${SERVER_USER}@${SERVER_IP} "cat > /tmp/timao-backend.service << EOF
[Unit]
Description=提猫直播助手后端服务
After=network.target

[Service]
Type=simple
User=${SERVER_USER}
WorkingDirectory=${SERVER_PATH}/server
Environment=\"BACKEND_PORT=${BACKEND_PORT}\"
Environment=\"DEBUG=false\"
Environment=\"PYTHONIOENCODING=utf-8\"
Environment=\"PYTHONUTF8=1\"
ExecStart=${SERVER_PATH}/scripts/构建与启动/start-backend.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
sudo mv /tmp/timao-backend.service /etc/systemd/system/timao-backend.service
sudo systemctl daemon-reload"

# 6. 开放防火墙端口
echo "🔥 配置防火墙..."
ssh ${SERVER_USER}@${SERVER_IP} "sudo ufw allow ${BACKEND_PORT}/tcp || true"

echo ""
echo "✅ 部署完成！"
echo ""
echo "📋 下一步操作："
echo "   1. 启动服务: ssh ${SERVER_USER}@${SERVER_IP} '${SERVER_PATH}/scripts/构建与启动/start-backend.sh'"
echo "   2. 或使用systemd: ssh ${SERVER_USER}@${SERVER_IP} 'sudo systemctl start timao-backend'"
echo "   3. 查看日志: ssh ${SERVER_USER}@${SERVER_IP} 'sudo journalctl -u timao-backend -f'"
echo "   4. 测试服务: curl http://${SERVER_IP}:${BACKEND_PORT}/health"
echo ""

