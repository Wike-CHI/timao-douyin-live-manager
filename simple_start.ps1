# Simple Start Script for Timao Live Assistant
param(
    [switch]$Help
)

if ($Help) {
    Write-Host "Timao Live Assistant - Simple Launcher" -ForegroundColor Cyan
    Write-Host "Usage: .\simple_start.ps1" -ForegroundColor White
    exit 0
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Timao Live Assistant - Simple Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $null = python --version
    Write-Host "[OK] Python is installed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Node.js
try {
    $null = node --version
    Write-Host "[OK] Node.js is installed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Node.js not found" -ForegroundColor Red
    Write-Host "Please install Node.js from https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "[INFO] Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "[OK] Virtual environment exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"
Write-Host "[OK] Virtual environment activated" -ForegroundColor Green

# Install Python dependencies
if (Test-Path "requirements.txt") {
    Write-Host "[INFO] Installing Python dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARNING] Some Python dependencies failed to install" -ForegroundColor Yellow
    } else {
        Write-Host "[OK] Python dependencies installed" -ForegroundColor Green
    }
}

# Install Node.js dependencies
if (Test-Path "package.json") {
    Write-Host "[INFO] Installing Node.js dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARNING] Some Node.js dependencies failed to install" -ForegroundColor Yellow
    } else {
        Write-Host "[OK] Node.js dependencies installed" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Application..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backend Service: http://127.0.0.1:9019" -ForegroundColor White
Write-Host "Frontend Server: http://127.0.0.1:10030" -ForegroundColor White
Write-Host "Health Check: http://127.0.0.1:9019/health" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the application" -ForegroundColor Yellow
Write-Host ""

# Start the application
npm run dev