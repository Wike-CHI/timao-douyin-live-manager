@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo TiMao Live Assistant - Windows Package Script
echo ========================================
echo.

:: Check Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found, please install Node.js first
    pause
    exit /b 1
)

:: Check npm
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm not found, please check Node.js installation
    pause
    exit /b 1
)

echo [INFO] Node.js version:
node --version
echo [INFO] npm version:
npm --version
echo.

:: Enter project root directory
cd /d "%~dp0..\.."

:: Step 1: Clean old build files
echo [1/5] Cleaning old build files...
if exist "dist" (
    echo Removing dist directory...
    rd /s /q "dist"
)
if exist "electron\renderer\dist" (
    echo Removing electron\renderer\dist directory...
    rd /s /q "electron\renderer\dist"
)
echo Cleaning completed
echo.

:: Step 2: Install root dependencies
echo [2/5] Installing root dependencies...
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install root dependencies
    pause
    exit /b 1
)
echo.

:: Step 3: Install renderer dependencies
echo [3/5] Installing renderer dependencies...
cd electron\renderer
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install renderer dependencies
    pause
    exit /b 1
)
cd ..\..
echo.

:: Step 4: Build frontend
echo [4/5] Building frontend application...
cd electron\renderer
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed
    pause
    exit /b 1
)
cd ..\..
echo.

:: Step 5: Package Electron application
echo [5/5] Packaging Electron application...
echo Target platform: Windows x64
echo Package format: Portable + NSIS
echo.

call npx electron-builder --win --x64 --config build-config.json
if %errorlevel% neq 0 (
    echo [ERROR] Package failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Package completed!
echo ========================================
echo Output directory: %cd%\dist
echo.

:: List generated files
if exist "dist" (
    echo Generated files:
    dir /b dist\*.exe
    echo.
)

echo Press any key to exit...
pause >nul

