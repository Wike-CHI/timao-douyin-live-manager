# scripts/部署与运维/connect-server.ps1
# 一键连接到云服务器

Write-Host "🚀 正在连接到云服务器..." -ForegroundColor Green
Write-Host "提示：如果需要输入密码，请输入SSH私钥密码" -ForegroundColor Yellow
Write-Host ""

# 连接到服务器
ssh timao-server

# 如果连接断开
Write-Host ""
Write-Host "✅ 已断开与服务器的连接" -ForegroundColor Cyan

