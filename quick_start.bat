@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo Timao Live Assistant - Quick Launcher
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python is installed

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js is installed

REM Create virtual environment if not exists
if not exist ".venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment exists
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo [OK] Virtual environment activated

REM Install Python dependencies
if exist "requirements.txt" (
    echo [INFO] Installing Python dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [WARNING] Some Python dependencies failed to install
    ) else (
        echo [OK] Python dependencies installed
    )
)

REM Install Node.js dependencies
if exist "package.json" (
    echo [INFO] Installing Node.js dependencies...
    npm install
    if %errorlevel% neq 0 (
        echo [WARNING] Some Node.js dependencies failed to install
    ) else (
        echo [OK] Node.js dependencies installed
    )
)

echo.
echo ========================================
echo Starting Application...
echo ========================================
echo Backend Service: http://127.0.0.1:9019
echo Frontend Server: http://127.0.0.1:10030
echo Health Check: http://127.0.0.1:9019/health
echo.
echo Press Ctrl+C to stop the application
echo.

REM Start the application
npm run dev

pause