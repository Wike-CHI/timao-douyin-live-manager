# 提猫直播助手 - 完整构建脚本 (PowerShell版本)
param(
    [switch]$SkipDeps,
    [switch]$CleanOnly,
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "提猫直播助手 - 完整构建脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 错误处理
$ErrorActionPreference = "Stop"

try {
    # 检查Python环境
    Write-Host "[1/6] 检查Python环境..." -ForegroundColor Yellow
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "未找到Python环境，请先安装Python"
    }
    Write-Host "Python版本: $pythonVersion" -ForegroundColor Green

    # 检查Node.js环境
    Write-Host "[2/6] 检查Node.js环境..." -ForegroundColor Yellow
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "未找到Node.js环境，请先安装Node.js"
    }
    Write-Host "Node.js版本: $nodeVersion" -ForegroundColor Green

    # 安装依赖
    if (-not $SkipDeps) {
        Write-Host "[3/6] 安装项目依赖..." -ForegroundColor Yellow
        npm run setup:dev
        if ($LASTEXITCODE -ne 0) {
            throw "依赖安装失败"
        }
        Write-Host "依赖安装完成" -ForegroundColor Green
    } else {
        Write-Host "[3/6] 跳过依赖安装..." -ForegroundColor Gray
    }

    # 清理旧构建
    Write-Host "[4/6] 清理旧构建文件..." -ForegroundColor Yellow
    npm run clean
    if ($LASTEXITCODE -ne 0) {
        Write-Host "警告: 清理过程中出现错误，继续构建..." -ForegroundColor Yellow
    } else {
        Write-Host "清理完成" -ForegroundColor Green
    }

    if ($CleanOnly) {
        Write-Host "仅清理模式，构建完成" -ForegroundColor Green
        return
    }

    # 构建后端服务
    if (-not $FrontendOnly) {
        Write-Host "[5/6] 构建后端服务..." -ForegroundColor Yellow
        npm run build:backend
        if ($LASTEXITCODE -ne 0) {
            throw "后端构建失败"
        }
        Write-Host "后端构建完成" -ForegroundColor Green
    }

    if ($BackendOnly) {
        Write-Host "仅后端构建模式，构建完成" -ForegroundColor Green
        return
    }

    # 构建前端和打包
    Write-Host "[6/6] 构建前端并打包应用..." -ForegroundColor Yellow
    npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "应用打包失败"
    }

    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "构建完成！" -ForegroundColor Green
    Write-Host "输出目录: dist/" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan

    # 显示构建结果
    if (Test-Path "dist") {
        Write-Host "构建产物:" -ForegroundColor Yellow
        Get-ChildItem "dist" | ForEach-Object {
            $size = if ($_.PSIsContainer) { "文件夹" } else { "{0:N2} MB" -f ($_.Length / 1MB) }
            Write-Host "  $($_.Name) - $size" -ForegroundColor White
        }
    }

} catch {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "构建失败: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}

Write-Host "按任意键继续..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")