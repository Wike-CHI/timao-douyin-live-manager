# 提猫直播助手自动构建脚本
# 自动检查权限并构建 Windows 应用

param(
    [switch]$Force,
    [string]$Target = "win64"
)

# 检查管理员权限
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 主构建函数
function Start-Build {
    Write-Host "=== 提猫直播助手 Windows 构建脚本 ===" -ForegroundColor Cyan
    Write-Host ""

    # 检查 Node.js
    try {
        $nodeVersion = node --version
        Write-Host "✓ Node.js 版本: $nodeVersion" -ForegroundColor Green
    } catch {
        Write-Host "✗ 未找到 Node.js，请先安装 Node.js" -ForegroundColor Red
        exit 1
    }

    # 检查项目目录
    if (-not (Test-Path "package.json")) {
        Write-Host "✗ 未找到 package.json，请在项目根目录运行此脚本" -ForegroundColor Red
        exit 1
    }

    # 设置环境变量
    $env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
    $env:ELECTRON_BUILDER_ALLOW_UNRESOLVED_DEPENDENCIES = "true"
    Write-Host "✓ 已设置环境变量" -ForegroundColor Green

    # 清理构建环境
    if ($Force -or (Read-Host "是否清理构建缓存? (y/N)") -eq 'y') {
        Write-Host "清理构建环境..." -ForegroundColor Yellow
        
        if (Test-Path "dist") {
            Remove-Item -Recurse -Force "dist" -ErrorAction SilentlyContinue
            Write-Host "✓ 已清理 dist 目录" -ForegroundColor Green
        }
        
        $cacheDir = "$env:LOCALAPPDATA\electron-builder\Cache"
        if (Test-Path $cacheDir) {
            Remove-Item -Recurse -Force $cacheDir -ErrorAction SilentlyContinue
            Write-Host "✓ 已清理 electron-builder 缓存" -ForegroundColor Green
        }
    }

    # 检查依赖
    if (-not (Test-Path "node_modules\electron-builder")) {
        Write-Host "安装依赖包..." -ForegroundColor Yellow
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ 依赖安装失败" -ForegroundColor Red
            exit 1
        }
        Write-Host "✓ 依赖安装完成" -ForegroundColor Green
    }

    # 开始构建
    Write-Host ""
    Write-Host "开始构建 Windows 应用..." -ForegroundColor Yellow
    Write-Host "目标: $Target" -ForegroundColor Cyan
    Write-Host ""

    $buildCommand = switch ($Target) {
        "win64" { "npm run build:win64" }
        "win32" { "npm run build:win32" }
        "win" { "npm run build:win" }
        default { "npm run build:win64" }
    }

    # 执行构建
    Invoke-Expression $buildCommand

    # 检查构建结果
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "🎉 构建成功！" -ForegroundColor Green
        Write-Host ""
        Write-Host "输出文件:" -ForegroundColor Cyan
        
        if (Test-Path "dist") {
            Get-ChildItem "dist\*.exe" -ErrorAction SilentlyContinue | ForEach-Object {
                $size = [math]::Round($_.Length / 1MB, 2)
                Write-Host "  📦 $($_.Name) ($size MB)" -ForegroundColor Yellow
            }
            
            if (Test-Path "dist\win-unpacked") {
                Write-Host "  📁 win-unpacked\ (未打包版本)" -ForegroundColor Yellow
            }
        }
        
        Write-Host ""
        Write-Host "构建完成！可以在 dist 目录找到生成的文件。" -ForegroundColor Green
        
    } else {
        Write-Host ""
        Write-Host "❌ 构建失败！" -ForegroundColor Red
        Write-Host ""
        Write-Host "可能的解决方案:" -ForegroundColor Yellow
        Write-Host "1. 以管理员身份运行此脚本" -ForegroundColor White
        Write-Host "2. 启用 Windows 开发者模式" -ForegroundColor White
        Write-Host "3. 清理缓存后重试: .\build-auto.ps1 -Force" -ForegroundColor White
        Write-Host ""
        Write-Host "详细解决方案请查看: docs\Windows打包问题解决方案.md" -ForegroundColor Cyan
    }
}

# 主逻辑
if (-not (Test-Administrator)) {
    Write-Host "检测到需要管理员权限..." -ForegroundColor Yellow
    Write-Host "正在以管理员身份重新启动脚本..." -ForegroundColor Yellow
    
    $arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    if ($Force) { $arguments += " -Force" }
    if ($Target -ne "win64") { $arguments += " -Target $Target" }
    
    try {
        Start-Process PowerShell -Verb RunAs -ArgumentList $arguments -Wait
    } catch {
        Write-Host "无法以管理员身份启动，请手动以管理员身份运行 PowerShell" -ForegroundColor Red
        Write-Host "然后执行: .\build-auto.ps1" -ForegroundColor Cyan
    }
} else {
    Start-Build
    Write-Host ""
    Read-Host "按任意键退出"
}