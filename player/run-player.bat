@echo off
setlocal

echo ============================================
echo   Digital Signage Player
echo ============================================
echo.

:: Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

:: Go up one level to project root to find embedded Python
cd /d "%SCRIPT_DIR%\.."

:: Check if embedded Python exists (from setup.bat)
if exist "python\python.exe" (
    echo Using embedded Python...
    set "PYTHON_EXE=%CD%\python\python.exe"
) else (
    :: Fall back to system Python
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        echo ERROR: Python not found.
        echo.
        echo Either run setup.bat first to install embedded Python,
        echo or install Python from https://python.org
        pause
        exit /b 1
    )
    set "PYTHON_EXE=python"
)

:: Check if pywebview is installed
"%PYTHON_EXE%" -c "import webview" 2>nul
if %errorlevel% neq 0 (
    echo Installing pywebview...
    "%PYTHON_EXE%" -m pip install pywebview --no-warn-script-location
    echo.
)

:: Run the player
echo Starting player...
cd /d "%SCRIPT_DIR%"
"%PYTHON_EXE%" player.py

pause