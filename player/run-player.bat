@echo off
setlocal

echo ============================================
echo   Digital Signage Player
echo ============================================
echo.

:: Check if Python is available
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

:: Check if pywebview is installed
python -c "import webview" 2>nul
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install pywebview
)

:: Run the player
python player.py

pause