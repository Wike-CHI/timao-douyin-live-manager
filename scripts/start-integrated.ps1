# 提猫直播助手 - 一体化启动器 (PowerShell版本)
param(
    [string]$Command = "start",
    [switch]$Help
)

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 颜色定义
$Colors = @{
    Success = "Green"
    Error = "Red"
    Warning = "Yellow"
    Info = "Cyan"
    Header = "Magenta"
}

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

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-ColorText "========================================" $Colors.Header
    Write-ColorText $Text $Colors.Header
    Write-ColorText "========================================" $Colors.Header
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-ColorText "✅ $Text" $Colors.Success
}

function Write-Error {
    param([string]$Text)
    Write-ColorText "❌ $Text" $Colors.Error
}

function Write-Warning {
    param([string]$Text)
    Write-ColorText "⚠️  $Text" $Colors.Warning
}

function Write-Info {
    param([string]$Text)
    Write-ColorText "💡 $Text" $Colors.Info
}

function Test-Command {
    param([string]$CommandName)
    
    try {
        Get-Command $CommandName -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Show-Help {
    Write-Header "提猫直播助手 - 一体化启动器帮助"
    
    Write-ColorText "用法:" $Colors.Info
    Write-Host "  .\start-integrated.ps1 [命令] [选项]"
    Write-Host ""
    
    Write-ColorText "命令:" $Colors.Info
    Write-Host "  start   - 启动所有服务 (默认)"
    Write-Host "  check   - 检查环境和端口状态"
    Write-Host "  clean   - 清理端口占用"
    Write-Host "  help    - 显示此帮助信息"
    Write-Host ""
    
    Write-ColorText "选项:" $Colors.Info
    Write-Host "  -Help   - 显示帮助信息"
    Write-Host ""
    
    Write-ColorText "示例:" $Colors.Info
    Write-Host "  .\start-integrated.ps1              # 启动所有服务"
    Write-Host "  .\start-integrated.ps1 check        # 检查环境"
    Write-Host "  .\start-integrated.ps1 clean        # 清理端口"
    Write-Host ""
    
    Write-ColorText "NPM 脚本:" $Colors.Info
    Write-Host "  npm run start:integrated    # 启动所有服务"
    Write-Host "  npm run port:check          # 检查端口状态"
    Write-Host "  npm run port:clean          # 清理端口占用"
    Write-Host "  npm run env:check           # 检查环境配置"
    Write-Host ""
}

function Test-Prerequisites {
    Write-Info "检查运行环境..."
    
    # 检查Node.js
    if (-not (Test-Command "node")) {
        Write-Error "未找到 Node.js"
        Write-Host "请先安装 Node.js: https://nodejs.org/"
        return $false
    }
    
    $nodeVersion = node --version
    Write-Success "Node.js 版本: $nodeVersion"
    
    # 检查Python
    if (-not (Test-Command "python")) {
        Write-Error "未找到 Python"
        Write-Host "请先安装 Python: https://python.org/"
        return $false
    }
    
    $pythonVersion = python --version
    Write-Success "Python 版本: $pythonVersion"
    
    # 检查必要文件
    $requiredFiles = @(
        "package.json",
        "scripts\integrated-launcher.js",
        "scripts\port-manager.js"
    )
    
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            Write-Error "未找到必要文件: $file"
            return $false
        }
    }
    
    Write-Success "所有必要文件检查通过"
    return $true
}

function Main {
    # 显示帮助
    if ($Help) {
        Show-Help
        return
    }
    
    Write-Header "提猫直播助手 - 一体化启动器"
    
    # 切换到脚本所在目录的上级目录（项目根目录）
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $projectRoot = Split-Path -Parent $scriptDir
    Set-Location $projectRoot
    
    Write-Info "项目根目录: $projectRoot"
    
    # 检查环境
    if (-not (Test-Prerequisites)) {
        Write-Host ""
        Write-Error "环境检查失败，无法继续"
        Write-Host ""
        Write-Info "故障排除建议:"
        Write-Host "   1. 安装 Node.js: https://nodejs.org/"
        Write-Host "   2. 安装 Python: https://python.org/"
        Write-Host "   3. 确保在项目根目录运行脚本"
        Write-Host ""
        Read-Host "按回车键退出"
        exit 1
    }
    
    Write-Host ""
    Write-Info "执行命令: $Command"
    Write-Host ""
    
    # 执行启动器
    try {
        $process = Start-Process -FilePath "node" -ArgumentList "scripts/integrated-launcher.js", $Command -Wait -PassThru -NoNewWindow
        
        if ($process.ExitCode -eq 0) {
            Write-Host ""
            Write-Success "启动器执行完成"
        } else {
            Write-Host ""
            Write-Error "启动器执行失败 (退出代码: $($process.ExitCode))"
            Write-Host ""
            Write-Info "故障排除建议:"
            Write-Host "   1. 检查端口占用: npm run port:check"
            Write-Host "   2. 清理端口占用: npm run port:clean"
            Write-Host "   3. 检查环境配置: npm run env:check"
            Write-Host "   4. 查看帮助信息: npm run launcher:help"
            Write-Host ""
        }
    } catch {
        Write-Error "启动器执行异常: $($_.Exception.Message)"
        Write-Host ""
        Write-Info "请检查 Node.js 是否正确安装并在 PATH 中"
        Write-Host ""
    }
    
    if ($Command -eq "start") {
        Write-Host ""
        Write-Info "按回车键退出"
        Read-Host
    }
}

# 执行主函数
Main