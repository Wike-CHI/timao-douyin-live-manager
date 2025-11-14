@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: Quick package script - skip dependency installation
echo ========================================
echo TiMao Live Assistant - Windows Quick Package
echo (Skip dependency installation)
echo ========================================
echo.

cd /d "%~dp0..\.."

:: Clean old build
echo [1/3] Cleaning old build files...
if exist "dist" rd /s /q "dist"
if exist "electron\renderer\dist" rd /s /q "electron\renderer\dist"
echo.

:: Build frontend
echo [2/3] Building frontend application...
cd electron\renderer
call npm run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed
    pause
    exit /b 1
)
cd ..\..
echo.

:: Package
echo [3/3] Packaging Electron application...
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

if exist "dist" (
    echo Generated files:
    dir /b dist\*.exe
    echo.
)

pause

