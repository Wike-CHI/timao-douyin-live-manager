# 提猫直播助手开发环境启动脚本
# PowerShell版本

Write-Host "正在启动提猫直播助手开发环境..." -ForegroundColor Green
Write-Host ""

# 检查虚拟环境是否存在
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "错误：虚拟环境不存在，请先创建虚拟环境" -ForegroundColor Red
    Write-Host "运行命令：python -m venv .venv" -ForegroundColor Yellow
    Read-Host "按任意键退出"
    exit 1
}

# 激活虚拟环境
Write-Host "激活Python虚拟环境..." -ForegroundColor Cyan
try {
    & ".venv\Scripts\Activate.ps1"
    Write-Host "虚拟环境激活成功" -ForegroundColor Green
} catch {
    Write-Host "错误：无法激活虚拟环境" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 检查npm是否可用
Write-Host "检查npm..." -ForegroundColor Cyan
try {
    $npmVersion = npm --version
    Write-Host "npm版本：$npmVersion" -ForegroundColor Green
} catch {
    Write-Host "错误：npm未找到，请确保Node.js已安装" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 检查package.json是否存在
if (-not (Test-Path "package.json")) {
    Write-Host "错误：package.json文件不存在" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}

# 运行npm dev
Write-Host ""
Write-Host "启动开发服务器..." -ForegroundColor Green
Write-Host "运行命令：npm run dev" -ForegroundColor Yellow
Write-Host ""

try {
    npm run dev
} catch {
    Write-Host ""
    Write-Host "启动失败，请检查错误信息" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}