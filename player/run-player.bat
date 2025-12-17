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
    set "PYTHON_CMD=python\python.exe"
    set "PIP_CMD=python\python.exe -m pip"
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
    set "PYTHON_CMD=python"
    set "PIP_CMD=python -m pip"
)

:: Check if pywebview is installed
%PYTHON_CMD% -c "import webview" 2>nul
if %errorlevel% neq 0 (
    echo Installing pywebview...
    %PIP_CMD% install pywebview --no-warn-script-location
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Failed to install pywebview
        echo.
        echo If using system Python 3.14, it may not be supported yet.
        echo Run setup.bat first to install embedded Python 3.12.
        pause
        exit /b 1
    )
)

:: Run the player
echo Starting player...
cd /d "%SCRIPT_DIR%"
%SCRIPT_DIR%\..\python\python.exe player.py 2>nul || python player.py

pause