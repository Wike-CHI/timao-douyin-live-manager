# 打包Electron应用脚本 (PowerShell版本)
# 使用方法: .\build-electron.ps1

$ErrorActionPreference = "Stop"

Write-Host "📦 开始打包Electron应用..." -ForegroundColor Green

# 设置环境变量
$env:VITE_FASTAPI_URL = "http://129.211.218.135:10050"
$env:VITE_STREAMCAP_URL = "http://129.211.218.135:10050"
$env:VITE_DOUYIN_URL = "http://129.211.218.135:10050"
$env:ELECTRON_START_API = "false"

# 1. 安装依赖
Write-Host "📥 安装依赖..." -ForegroundColor Cyan
npm install

# 2. 构建前端
Write-Host "🔨 构建前端..." -ForegroundColor Cyan
Set-Location electron/renderer
npm install
npm run build
Set-Location ../..

# 3. 打包Electron
Write-Host "📦 打包Electron应用..." -ForegroundColor Cyan
npm run build:win

Write-Host ""
Write-Host "✅ 打包完成！" -ForegroundColor Green
Write-Host "📁 安装包位置: dist/TalkingCat-Portable-*.exe" -ForegroundColor Cyan
Write-Host ""

