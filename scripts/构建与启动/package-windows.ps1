# 提猫直播助手 - Windows打包脚本 (PowerShell)
# 编码: UTF-8

# 设置错误时停止
$ErrorActionPreference = "Stop"

# 函数: 打印带颜色的消息
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    
    switch ($Type) {
        "Success" { Write-Host $Message -ForegroundColor Green }
        "Error" { Write-Host $Message -ForegroundColor Red }
        "Warning" { Write-Host $Message -ForegroundColor Yellow }
        "Info" { Write-Host $Message -ForegroundColor Cyan }
        default { Write-Host $Message }
    }
}

# 函数: 检查命令是否存在
function Test-Command {
    param([string]$Command)
    
    $exists = $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
    return $exists
}

# 打印标题
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "提猫直播助手 - Windows打包脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Node.js
Write-ColorOutput "检查环境..." "Info"
if (-not (Test-Command "node")) {
    Write-ColorOutput "[错误] 未找到Node.js，请先安装Node.js" "Error"
    Read-Host "按回车键退出"
    exit 1
}

if (-not (Test-Command "npm")) {
    Write-ColorOutput "[错误] 未找到npm，请检查Node.js安装" "Error"
    Read-Host "按回车键退出"
    exit 1
}

$nodeVersion = node --version
$npmVersion = npm --version
Write-ColorOutput "[信息] Node.js版本: $nodeVersion" "Info"
Write-ColorOutput "[信息] npm版本: $npmVersion" "Info"
Write-Host ""

# 进入项目根目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Join-Path $scriptPath "..\.." | Resolve-Path
Set-Location $projectRoot

Write-ColorOutput "项目目录: $projectRoot" "Info"
Write-Host ""

# 步骤1: 清理旧的构建文件
Write-ColorOutput "[1/5] 清理旧的构建文件..." "Info"
try {
    if (Test-Path "dist") {
        Write-Host "正在删除 dist 目录..."
        Remove-Item -Path "dist" -Recurse -Force
    }
    if (Test-Path "electron\renderer\dist") {
        Write-Host "正在删除 electron\renderer\dist 目录..."
        Remove-Item -Path "electron\renderer\dist" -Recurse -Force
    }
    Write-ColorOutput "清理完成" "Success"
} catch {
    Write-ColorOutput "清理失败: $_" "Warning"
}
Write-Host ""

# 步骤2: 安装根目录依赖
Write-ColorOutput "[2/5] 安装根目录依赖..." "Info"
try {
    npm install
    if ($LASTEXITCODE -ne 0) { throw "npm install失败" }
    Write-ColorOutput "根目录依赖安装完成" "Success"
} catch {
    Write-ColorOutput "[错误] 安装根目录依赖失败: $_" "Error"
    Read-Host "按回车键退出"
    exit 1
}
Write-Host ""

# 步骤3: 安装渲染进程依赖
Write-ColorOutput "[3/5] 安装渲染进程依赖..." "Info"
try {
    Set-Location "electron\renderer"
    npm install
    if ($LASTEXITCODE -ne 0) { throw "npm install失败" }
    Set-Location $projectRoot
    Write-ColorOutput "渲染进程依赖安装完成" "Success"
} catch {
    Set-Location $projectRoot
    Write-ColorOutput "[错误] 安装渲染进程依赖失败: $_" "Error"
    Read-Host "按回车键退出"
    exit 1
}
Write-Host ""

# 步骤4: 构建前端
Write-ColorOutput "[4/5] 构建前端应用..." "Info"
try {
    Set-Location "electron\renderer"
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "npm run build失败" }
    Set-Location $projectRoot
    Write-ColorOutput "前端构建完成" "Success"
} catch {
    Set-Location $projectRoot
    Write-ColorOutput "[错误] 构建前端失败: $_" "Error"
    Read-Host "按回车键退出"
    exit 1
}
Write-Host ""

# 步骤5: 打包Electron应用
Write-ColorOutput "[5/5] 打包Electron应用..." "Info"
Write-Host "目标平台: Windows x64"
Write-Host "打包格式: Portable + NSIS"
Write-Host ""

try {
    npx electron-builder --win --x64 --config build-config.json
    if ($LASTEXITCODE -ne 0) { throw "electron-builder失败" }
    Write-ColorOutput "打包完成" "Success"
} catch {
    Write-ColorOutput "[错误] 打包失败: $_" "Error"
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "打包完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-ColorOutput "输出目录: $(Join-Path $projectRoot 'dist')" "Success"
Write-Host ""

# 列出生成的文件
if (Test-Path "dist") {
    Write-ColorOutput "生成的文件:" "Info"
    Get-ChildItem "dist\*.exe" | ForEach-Object {
        $sizeMB = [math]::Round($_.Length / 1MB, 2)
        Write-Host "  - $($_.Name) ($sizeMB MB)"
    }
    Write-Host ""
}

Write-Host "按回车键退出..."
Read-Host

