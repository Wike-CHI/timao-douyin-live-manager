# 简单部署脚本 - 部署后端到服务器 (PowerShell版本)
# 使用方法: .\scripts/部署与运维/deploy-server.ps1

$ErrorActionPreference = "Stop"

$SERVER_IP = "129.211.218.135"
$SERVER_USER = "root"
$SERVER_PATH = "/opt/timao-douyin-live-manager"
$BACKEND_PORT = "10050"

Write-Host "🚀 开始部署后端到服务器..." -ForegroundColor Green

# 1. 检查SSH连接
Write-Host "📡 检查SSH连接..." -ForegroundColor Cyan
try {
    ssh -o ConnectTimeout=5 "${SERVER_USER}@${SERVER_IP}" "echo 'SSH连接成功'"
} catch {
    Write-Host "❌ SSH连接失败，请检查：" -ForegroundColor Red
    Write-Host "   1. 服务器IP是否正确: ${SERVER_IP}" -ForegroundColor Yellow
    Write-Host "   2. SSH密钥是否配置" -ForegroundColor Yellow
    Write-Host "   3. 服务器是否可访问" -ForegroundColor Yellow
    exit 1
}

# 2. 创建部署目录
Write-Host "📁 创建部署目录..." -ForegroundColor Cyan
ssh "${SERVER_USER}@${SERVER_IP}" "mkdir -p ${SERVER_PATH}"

# 3. 上传后端代码（排除前端和Electron）
Write-Host "📤 上传后端代码..." -ForegroundColor Cyan
# 注意：Windows需要安装rsync或使用scp
# 如果使用scp，需要先打包
$tempZip = "deploy-temp.zip"
Write-Host "   正在打包文件..." -ForegroundColor Gray
# 排除不需要的文件
Get-ChildItem -Path . -Exclude node_modules,electron,admin-dashboard,.git,__pycache__,"*.pyc",.venv,dist,"*.log" | 
    Compress-Archive -DestinationPath $tempZip -Force

Write-Host "   正在上传..." -ForegroundColor Gray
scp $tempZip "${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/deploy-temp.zip"
Remove-Item $tempZip -Force

# 在服务器上解压
ssh "${SERVER_USER}@${SERVER_IP}" "cd ${SERVER_PATH} && unzip -o deploy-temp.zip && rm deploy-temp.zip"

# 4. 创建启动脚本
Write-Host "📝 创建启动脚本..." -ForegroundColor Cyan
$startScript = @"
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
"@

ssh "${SERVER_USER}@${SERVER_IP}" "cat > ${SERVER_PATH}/scripts/构建与启动/start-backend.sh << 'EOFSCRIPT'
${startScript}
EOFSCRIPT
chmod +x ${SERVER_PATH}/scripts/构建与启动/start-backend.sh"

# 5. 创建systemd服务
Write-Host "⚙️  创建systemd服务..." -ForegroundColor Cyan
$serviceContent = @"
[Unit]
Description=提猫直播助手后端服务
After=network.target

[Service]
Type=simple
User=${SERVER_USER}
WorkingDirectory=${SERVER_PATH}/server
Environment=`"BACKEND_PORT=${BACKEND_PORT}`"
Environment=`"DEBUG=false`"
Environment=`"PYTHONIOENCODING=utf-8`"
Environment=`"PYTHONUTF8=1`"
ExecStart=${SERVER_PATH}/scripts/构建与启动/start-backend.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"@

ssh "${SERVER_USER}@${SERVER_IP}" "cat > /tmp/timao-backend.service << 'EOFSERVICE'
${serviceContent}
EOFSERVICE
sudo mv /tmp/timao-backend.service /etc/systemd/system/timao-backend.service
sudo systemctl daemon-reload"

# 6. 开放防火墙端口
Write-Host "🔥 配置防火墙..." -ForegroundColor Cyan
ssh "${SERVER_USER}@${SERVER_IP}" "sudo ufw allow ${BACKEND_PORT}/tcp || true"

Write-Host ""
Write-Host "✅ 部署完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📋 下一步操作：" -ForegroundColor Cyan
Write-Host "   1. 启动服务: ssh ${SERVER_USER}@${SERVER_IP} '${SERVER_PATH}/scripts/构建与启动/start-backend.sh'" -ForegroundColor Yellow
Write-Host "   2. 或使用systemd: ssh ${SERVER_USER}@${SERVER_IP} 'sudo systemctl start timao-backend'" -ForegroundColor Yellow
Write-Host "   3. 查看日志: ssh ${SERVER_USER}@${SERVER_IP} 'sudo journalctl -u timao-backend -f'" -ForegroundColor Yellow
Write-Host "   4. 测试服务: curl http://${SERVER_IP}:${BACKEND_PORT}/health" -ForegroundColor Yellow
Write-Host ""

