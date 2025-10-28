# 提猫直播助手 - 一站式安装启动器
# PowerShell版本

param(
    [switch]$SkipDependencies,
    [switch]$ProductionMode,
    [switch]$QuickStart,
    [switch]$Help
)

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 显示帮助信息
if ($Help) {
    Write-Host "提猫直播助手 - 一站式安装启动器" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "用法: .\install_and_start.ps1 [选项]" -ForegroundColor White
    Write-Host ""
    Write-Host "选项:" -ForegroundColor Yellow
    Write-Host "  -SkipDependencies    跳过依赖安装，直接启动" -ForegroundColor White
    Write-Host "  -ProductionMode      以生产模式启动" -ForegroundColor White
    Write-Host "  -QuickStart          快速启动，跳过环境检查" -ForegroundColor White
    Write-Host "  -Help                显示此帮助信息" -ForegroundColor White
    Write-Host ""
    Write-Host "示例:" -ForegroundColor Yellow
    Write-Host "  .\install_and_start.ps1                    # 完整安装和启动" -ForegroundColor Gray
    Write-Host "  .\install_and_start.ps1 -SkipDependencies  # 跳过依赖安装" -ForegroundColor Gray
    Write-Host "  .\install_and_start.ps1 -QuickStart        # 快速启动" -ForegroundColor Gray
    exit 0
}

# 错误处理
$ErrorActionPreference = "Stop"

# 颜色定义
$Colors = @{
    Success = "Green"
    Error = "Red"
    Warning = "Yellow"
    Info = "Cyan"
    Highlight = "Magenta"
}

# 辅助函数
function Write-ColorText {
    param(
        [string]$Text,
        [string]$Color = "White",
        [switch]$NoNewline
    )
    if ($NoNewline) {
        Write-Host $Text -ForegroundColor $Color -NoNewline
    } else {
        Write-Host $Text -ForegroundColor $Color
    }
}

function Write-Success {
    param([string]$Message)
    Write-ColorText "✅ $Message" $Colors.Success
}

function Write-Error {
    param([string]$Message)
    Write-ColorText "❌ $Message" $Colors.Error
}

function Write-Warning {
    param([string]$Message)
    Write-ColorText "⚠️ $Message" $Colors.Warning
}

function Write-Info {
    param([string]$Message)
    Write-ColorText "ℹ️ $Message" $Colors.Info
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Test-Port {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("127.0.0.1", $Port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

function Get-PythonVersion {
    try {
        $version = python --version 2>&1
        if ($version -match "Python (\d+\.\d+)") {
            return [version]$matches[1]
        }
        return $null
    } catch {
        return $null
    }
}

function Get-NodeVersion {
    try {
        $version = node --version 2>&1
        if ($version -match "v(\d+\.\d+)") {
            return [version]$matches[1]
        }
        return $null
    } catch {
        return $null
    }
}

try {
    Write-Host ""
    Write-ColorText "🎯 提猫直播助手 - 一站式安装启动器" $Colors.Highlight
    Write-Host "=" * 50
    Write-Host ""

    # 环境检查
    if (-not $QuickStart) {
        Write-Info "正在检查系统环境..."
        
        # 检查Python
        $pythonVersion = Get-PythonVersion
        if ($pythonVersion -and $pythonVersion -ge [version]"3.8") {
            Write-Success "Python $pythonVersion 已安装"
        } else {
            Write-Error "需要Python 3.8或更高版本"
            Write-Info "请从 https://www.python.org/downloads/ 下载安装Python"
            Read-Host "按任意键退出"
            exit 1
        }
        
        # 检查Node.js
        $nodeVersion = Get-NodeVersion
        if ($nodeVersion -and $nodeVersion -ge [version]"16.0") {
            Write-Success "Node.js $nodeVersion 已安装"
        } else {
            Write-Error "需要Node.js 16.0或更高版本"
            Write-Info "请从 https://nodejs.org/ 下载安装Node.js"
            Read-Host "按任意键退出"
            exit 1
        }
        
        # 检查npm
        if (Test-Command "npm") {
            Write-Success "npm 已安装"
        } else {
            Write-Error "npm 未找到，请检查Node.js安装"
            Read-Host "按任意键退出"
            exit 1
        }
    }

    # 创建和激活虚拟环境
    if (-not $SkipDependencies) {
        Write-Info "正在设置Python虚拟环境..."
        
        if (-not (Test-Path ".venv")) {
            Write-Info "创建虚拟环境..."
            python -m venv .venv
            if ($LASTEXITCODE -ne 0) {
                Write-Error "创建虚拟环境失败"
                exit 1
            }
            Write-Success "虚拟环境创建成功"
        } else {
            Write-Success "虚拟环境已存在"
        }
        
        # 激活虚拟环境
        Write-Info "激活虚拟环境..."
        & ".\.venv\Scripts\Activate.ps1"
        if ($LASTEXITCODE -ne 0) {
            Write-Error "激活虚拟环境失败"
            exit 1
        }
        Write-Success "虚拟环境已激活"
        
        # 安装Python依赖
        if (Test-Path "requirements.txt") {
            Write-Info "正在安装Python依赖..."
            pip install -r requirements.txt
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "部分Python依赖安装失败，但将继续执行"
            } else {
                Write-Success "Python依赖安装完成"
            }
        }
        
        # 安装Node.js依赖
        if (Test-Path "package.json") {
            Write-Info "正在安装Node.js依赖..."
            npm install
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "部分Node.js依赖安装失败，但将继续执行"
            } else {
                Write-Success "Node.js依赖安装完成"
            }
        }
    }
    
    # 检查端口占用
    $ports = @(9019, 9020, 9021, 10030)
    $occupiedPorts = @()
    
    foreach ($port in $ports) {
        if (Test-Port $port) {
            $occupiedPorts += $port
        }
    }
    
    if ($occupiedPorts.Count -gt 0) {
        Write-Warning "以下端口已被占用: $($occupiedPorts -join ', ')"
        Write-ColorText "是否继续启动？某些服务可能无法正常工作。(Y/N): " $Colors.Info -NoNewline
        $response = Read-Host
        if ($response -notmatch '^[Yy]') {
            Write-ColorText "启动已取消" $Colors.Warning
            exit 0
        }
    }
    
    Write-Success "环境配置完成！正在启动应用..."
    Write-Host ""
    Write-Info "启动信息:"
    Write-Info "   - 后端服务: http://127.0.0.1:9019"
    Write-Info "   - 前端开发服务器: http://127.0.0.1:10030"
    Write-Info "   - 健康检查: http://127.0.0.1:9019/health"
    Write-Host ""
    Write-Info "启动中，请稍候..."
    Write-Host ""
    
    # 启动应用
    if ($ProductionMode) {
        npm run services:prod
    } else {
        npm run dev
    }
    
} catch {
    Write-Host ""
    Write-Error "安装或启动过程中发生错误: $($_.Exception.Message)"
    Write-Host ""
    Write-Info "故障排除建议:"
    Write-Info "1. 检查网络连接"
    Write-Info "2. 检查端口是否被占用 (9019, 9020, 9021, 10030)"
    Write-Info "3. 检查防火墙设置"
    Write-Info "4. 查看详细错误信息"
    Write-Info "5. 尝试以管理员权限运行"
    Write-Host ""
    Write-Info "获取帮助: .\install_and_start.ps1 -Help"
    
    Read-Host "按任意键退出"
    exit 1
}

Write-Host ""
Write-Success "应用启动成功！"
Write-Info "按 Ctrl+C 停止应用"