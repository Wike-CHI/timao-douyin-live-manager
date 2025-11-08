# Electron构建脚本 - 云服务器版本
# 用于构建连接到云服务器的Windows安装包

Write-Host "=== 提猫直播助手 Electron 构建（云服务器版本）===" -ForegroundColor Green
Write-Host ""

# 设置环境变量 - 指向云服务器
$env:VITE_FASTAPI_URL = "http://129.211.218.135"
$env:VITE_STREAMCAP_URL = "http://129.211.218.135"
$env:VITE_DOUYIN_URL = "http://129.211.218.135"
$env:VITE_WS_URL = "ws://129.211.218.135"
$env:VITE_BACKEND_PORT = "8181"
$env:ELECTRON_START_API = "false"  # 不启动本地后端
$env:NODE_ENV = "production"

Write-Host "✓ 环境变量已设置:" -ForegroundColor Cyan
Write-Host "  VITE_FASTAPI_URL: $env:VITE_FASTAPI_URL"
Write-Host "  VITE_BACKEND_PORT: $env:VITE_BACKEND_PORT"
Write-Host "  ELECTRON_START_API: $env:ELECTRON_START_API"
Write-Host ""

# 1. 构建前端
Write-Host "[1/3] 构建前端..." -ForegroundColor Yellow
Set-Location -Path "electron\renderer"
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 前端构建失败" -ForegroundColor Red
    exit 1
}
Write-Host "✓ 前端构建完成" -ForegroundColor Green
Set-Location -Path "..\..\"
Write-Host ""

# 2. 打包 Electron
Write-Host "[2/3] 打包 Electron 应用..." -ForegroundColor Yellow
npm run electron:build:win
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Electron 打包失败" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Electron 打包完成" -ForegroundColor Green
Write-Host ""

# 3. 显示构建结果
Write-Host "[3/3] 构建结果:" -ForegroundColor Yellow
$distPath = "electron-dist"
if (Test-Path $distPath) {
    Get-ChildItem -Path $distPath -File | ForEach-Object {
        $size = [math]::Round($_.Length / 1MB, 2)
        Write-Host "  $($_.Name) ($size MB)" -ForegroundColor Cyan
    }
    Write-Host ""
    Write-Host "✓ 安装包位置: $distPath\" -ForegroundColor Green
} else {
    Write-Host "✗ 找不到构建输出目录" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== 构建完成！===" -ForegroundColor Green
Write-Host "现在可以安装并运行 Electron 应用，它将连接到云服务器：" -ForegroundColor Cyan
Write-Host "  后端地址: http://129.211.218.135:8181" -ForegroundColor Cyan
Write-Host ""

