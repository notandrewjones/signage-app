@echo off
setlocal

echo ============================================
echo   Digital Signage Web UI
echo ============================================
echo.

:: Check if Node.js is installed
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed.
    echo.
    echo Please install Node.js from https://nodejs.org/
    echo Then run this script again.
    echo.
    pause
    exit /b 1
)

cd web-ui

:: Check if dependencies are installed
if not exist "node_modules" (
    echo Installing UI dependencies...
    call npm install
)

echo.
echo Starting Web UI on http://localhost:5173
echo.
echo Make sure the server is running first!
echo Press Ctrl+C to stop
echo ============================================
echo.

call npm run dev

pause
