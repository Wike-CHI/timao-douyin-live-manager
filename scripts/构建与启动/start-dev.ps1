# 提猫直播助手 - 开发环境启动脚本 (PowerShell)
# 按照启动方法.md的要求启动服务

param(
    [switch]$Sequential,  # 顺序启动模式
    [switch]$Check,       # 仅进行健康检查
    [switch]$Help         # 显示帮助
)

function Write-ColorText {
    param(
        [string]$Text,
        [string]$Color = "White"
    )
    Write-Host $Text -ForegroundColor $Color
}

function Show-Help {
    Write-ColorText "🚀 提猫直播助手 - 开发环境启动脚本" "Cyan"
    Write-ColorText "=========================================" "Cyan"
    Write-Host ""
    Write-ColorText "用法:" "Yellow"
    Write-Host "  .\scripts\start-dev.ps1                # 并行启动所有服务"
    Write-Host "  .\scripts\start-dev.ps1 -Sequential    # 顺序启动服务"
    Write-Host "  .\scripts\start-dev.ps1 -Check         # 仅进行健康检查"
    Write-Host "  .\scripts\start-dev.ps1 -Help          # 显示此帮助"
    Write-Host ""
    Write-ColorText "启动顺序:" "Yellow"
    Write-Host "  1. 后端 FastAPI 服务 (端口 9019)"
    Write-Host "  2. 前端 Vite 开发服务器 (端口 10030)"
    Write-Host "  3. Electron 应用"
    Write-Host ""
    Write-ColorText "端口配置:" "Yellow"
    Write-Host "  - 后端: http://127.0.0.1:9019"
    Write-Host "  - 前端: http://127.0.0.1:10030"
    Write-Host "  - 健康检查: http://127.0.0.1:9019/health"
}

function Test-Dependencies {
    Write-ColorText "⚙️  检查依赖..." "Yellow"
    
    if (-not (Test-Path "node_modules")) {
        Write-ColorText "❌ 未找到 node_modules，请先运行 npm install" "Red"
        return $false
    }
    
    if (-not (Test-Path "server\app")) {
        Write-ColorText "❌ 未找到后端代码，请检查项目结构" "Red"
        return $false
    }
    
    if (-not (Test-Path "electron\renderer")) {
        Write-ColorText "❌ 未找到前端代码，请检查项目结构" "Red"
        return $false
    }
    
    Write-ColorText "✅ 依赖检查完成" "Green"
    return $true
}

function Start-HealthCheck {
    Write-ColorText "🔍 执行健康检查..." "Yellow"
    
    try {
        if (Test-Path "scripts\health-check.js") {
            node scripts\health-check.js
        } else {
            npm run health:all
        }
    } catch {
        Write-ColorText "❌ 健康检查失败: $_" "Red"
        return $false
    }
    
    return $true
}

# 主程序
if ($Help) {
    Show-Help
    exit 0
}

Write-ColorText "🚀 提猫直播助手 - 开发环境启动脚本" "Cyan"
Write-ColorText "=====================================" "Cyan"
Write-Host ""

if (-not (Test-Dependencies)) {
    Write-ColorText "❌ 依赖检查失败，请解决上述问题后重试" "Red"
    exit 1
}

if ($Check) {
    Start-HealthCheck
    exit $LASTEXITCODE
}

Write-Host ""
Write-ColorText "🔄 启动开发环境..." "Yellow"
Write-ColorText "提示: 使用 Ctrl+C 可以停止所有服务" "Gray"
Write-Host ""

try {
    if ($Sequential) {
        Write-ColorText "📋 使用顺序启动模式..." "Yellow"
        npm run dev:sequential
    } else {
        Write-ColorText "📋 使用并行启动模式..." "Yellow"
        npm run quick:start
    }
} catch {
    Write-ColorText "❌ 启动失败: $_" "Red"
    exit 1
}

Write-Host ""
Write-ColorText "👋 开发环境已停止" "Yellow"