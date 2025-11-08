# ============================================
# 提猫直播助手 - 快速部署脚本（Windows）
# 遵循：奥卡姆剃刀 + 希克定律
# ============================================

$ErrorActionPreference = "Stop"

Write-Host "🚀 提猫直播助手 - 快速部署" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# 1. 检查 Python 环境
Write-Host "`n1. 检查 Python 环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python 未安装或未添加到 PATH" -ForegroundColor Red
    exit 1
}

# 2. 检查虚拟环境
Write-Host "`n2. 检查虚拟环境..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    Write-Host "创建虚拟环境..." -ForegroundColor Yellow
    python -m venv .venv
}
& ".venv\Scripts\Activate.ps1"
Write-Host "✅ 虚拟环境已激活" -ForegroundColor Green

# 3. 安装依赖
Write-Host "`n3. 安装依赖..." -ForegroundColor Yellow
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
Write-Host "✅ 依赖安装完成" -ForegroundColor Green

# 4. 检查 .env 文件
Write-Host "`n4. 检查配置文件..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    if (Test-Path "env.production.template") {
        Copy-Item "env.production.template" ".env"
        Write-Host "⚠️  请编辑 .env 文件，设置数据库密码和密钥" -ForegroundColor Yellow
    } else {
        Write-Host "❌ .env 文件不存在，请先创建" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✅ .env 文件已存在" -ForegroundColor Green
}

# 5. 验证配置
Write-Host "`n5. 验证配置..." -ForegroundColor Yellow
python -c @"
import os
from dotenv import load_dotenv
load_dotenv()

required = ['BACKEND_PORT', 'DB_TYPE', 'MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
missing = [k for k in required if not os.getenv(k)]
if missing:
    print(f'❌ 缺少必需配置: {missing}')
    exit(1)
print('✅ 配置验证通过')
"@

if ($LASTEXITCODE -ne 0) {
    exit 1
}

# 6. 测试数据库连接
Write-Host "`n6. 测试数据库连接..." -ForegroundColor Yellow
python -c @"
import sys
sys.path.insert(0, '.')
from server.app.database import engine
try:
    with engine.connect() as conn:
        print('✅ 数据库连接成功')
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
    exit(1)
"@

if ($LASTEXITCODE -ne 0) {
    exit 1
}

# 7. 完成
Write-Host "`n==================================" -ForegroundColor Green
Write-Host "✅ 部署准备完成！" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""
Write-Host "启动服务：" -ForegroundColor Yellow
Write-Host "  .venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "  python server\app\main.py" -ForegroundColor Cyan
Write-Host ""

