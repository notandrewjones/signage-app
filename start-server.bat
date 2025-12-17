@echo off
setlocal

echo ============================================
echo   Digital Signage Server
echo ============================================
echo.

:: Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Check if setup has been run
if not exist "python\python.exe" (
    echo ERROR: Python not found. Please run setup.bat first.
    pause
    exit /b 1
)

:: Create uploads directories if they don't exist
if not exist "server\uploads\content" mkdir "server\uploads\content"
if not exist "server\uploads\logos" mkdir "server\uploads\logos"
if not exist "server\uploads\backgrounds" mkdir "server\uploads\backgrounds"

echo Starting server on http://localhost:8000
echo.
echo API Documentation: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo ============================================
echo.

python\python.exe server\main.py

pause