# Electron Build Script - Cloud Server Version
# Builds Windows installer that connects to cloud server

Write-Host "=== TalkingCat Live Assistant - Electron Build (Cloud Version) ===" -ForegroundColor Green
Write-Host ""

# Set environment variables - pointing to cloud server
$env:VITE_FASTAPI_URL = "http://129.211.218.135"
$env:VITE_STREAMCAP_URL = "http://129.211.218.135"
$env:VITE_DOUYIN_URL = "http://129.211.218.135"
$env:VITE_WS_URL = "ws://129.211.218.135"
$env:VITE_BACKEND_PORT = "8181"
$env:ELECTRON_START_API = "false"  # Do not start local backend
$env:NODE_ENV = "production"

Write-Host "Environment variables configured:" -ForegroundColor Cyan
Write-Host "  VITE_FASTAPI_URL: $env:VITE_FASTAPI_URL"
Write-Host "  VITE_BACKEND_PORT: $env:VITE_BACKEND_PORT"
Write-Host "  ELECTRON_START_API: $env:ELECTRON_START_API"
Write-Host ""

# Step 1: Build frontend
Write-Host "[1/3] Building frontend..." -ForegroundColor Yellow
Set-Location -Path "electron\renderer"
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend build failed" -ForegroundColor Red
    exit 1
}
Write-Host "Frontend build completed" -ForegroundColor Green
Set-Location -Path "..\..\"
Write-Host ""

# Step 2: Package Electron app
Write-Host "[2/3] Packaging Electron application..." -ForegroundColor Yellow
npm run electron:build:win
if ($LASTEXITCODE -ne 0) {
    Write-Host "Electron packaging failed" -ForegroundColor Red
    exit 1
}
Write-Host "Electron packaging completed" -ForegroundColor Green
Write-Host ""

# Step 3: Show build results
Write-Host "[3/3] Build results:" -ForegroundColor Yellow
$distPath = "electron-dist"
if (Test-Path $distPath) {
    Get-ChildItem -Path $distPath -File | ForEach-Object {
        $size = [math]::Round($_.Length / 1MB, 2)
        Write-Host "  $($_.Name) ($size MB)" -ForegroundColor Cyan
    }
    Write-Host ""
    Write-Host "Installer location: $distPath\" -ForegroundColor Green
} else {
    Write-Host "Build output directory not found" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Build completed successfully! ===" -ForegroundColor Green
Write-Host "You can now install and run the Electron app" -ForegroundColor Cyan
Write-Host "Backend server: http://129.211.218.135:8181" -ForegroundColor Cyan
Write-Host ""
