# 打包Electron应用脚本 (PowerShell版本)
# 使用方法: .\scripts/构建与启动/build-electron.ps1

# 设置PowerShell输出编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$ErrorActionPreference = "Stop"

Write-Host "[1/4] 开始打包Electron应用..." -ForegroundColor Green

# 设置环境变量（通过Nginx反向代理，使用80端口）
$env:VITE_FASTAPI_URL = "http://129.211.218.135"
$env:VITE_STREAMCAP_URL = "http://129.211.218.135"
$env:VITE_DOUYIN_URL = "http://129.211.218.135"
$env:ELECTRON_START_API = "false"

# 1. 安装依赖
Write-Host "[2/4] 安装依赖..." -ForegroundColor Cyan
npm install

# 2. 构建前端
Write-Host "[3/4] 构建前端..." -ForegroundColor Cyan
Set-Location electron/renderer
npm install
npm run build
Set-Location ../..

# 3. 打包Electron
Write-Host "[4/4] 打包Electron应用..." -ForegroundColor Cyan
npm run build:win

Write-Host ""
Write-Host "SUCCESS: 打包完成!" -ForegroundColor Green
Write-Host "OUTPUT: 安装包位置 -> dist/TalkingCat-Portable-*.exe" -ForegroundColor Cyan
Write-Host ""

