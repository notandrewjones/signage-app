@echo off
setlocal

echo ============================================
echo   Digital Signage System
echo ============================================
echo.

:: Check if setup has been run
if not exist "python\python.exe" (
    echo Python not found. Running setup first...
    call setup.bat
    if %errorlevel% neq 0 exit /b 1
)

:: Check if Node.js is installed
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Node.js not installed. 
    echo Web UI will not be available.
    echo Install from https://nodejs.org/ for the full experience.
    echo.
    echo Starting server only...
    call start-server.bat
    exit /b
)

echo Starting both server and UI...
echo.

:: Start server in new window
start "Signage Server" cmd /k start-server.bat

:: Wait a moment for server to start
timeout /t 3 /nobreak >nul

:: Start UI in new window
start "Signage UI" cmd /k start-ui.bat

echo.
echo ============================================
echo Both services starting in new windows!
echo.
echo Server: http://localhost:8000
echo Web UI: http://localhost:5173
echo ============================================
echo.
echo Opening Web UI in browser...
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo Close this window when done.
pause
