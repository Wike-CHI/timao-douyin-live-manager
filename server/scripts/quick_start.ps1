# ============================================
# 提猫直播助手 - 快速启动脚本（Windows）
# 最简单的启动方式
# ============================================

$ErrorActionPreference = "Stop"

# 激活虚拟环境
if (Test-Path ".venv") {
    & ".venv\Scripts\Activate.ps1"
} else {
    Write-Host "❌ 虚拟环境不存在，请先运行 deploy.ps1" -ForegroundColor Red
    exit 1
}

# 检查 .env 文件
if (-not (Test-Path ".env")) {
    Write-Host "❌ .env 文件不存在，请先创建" -ForegroundColor Red
    exit 1
}

# 启动服务
Write-Host "🚀 启动提猫直播助手后端服务..." -ForegroundColor Green
python server\app\main.py

