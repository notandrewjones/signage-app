@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   Digital Signage System - Setup
echo ============================================
echo.

:: Check if already set up
if exist "python\python.exe" (
    echo Python already installed locally.
    goto :install_deps
)

echo Downloading Python 3.12 embedded...
echo.

:: Create directories
if not exist "python" mkdir python

:: Download Python 3.12 embedded
curl -L -o python312.zip https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip

if %errorlevel% neq 0 (
    echo Failed to download Python. Please check your internet connection.
    pause
    exit /b 1
)

:: Extract Python
echo Extracting Python...
powershell -command "Expand-Archive -Force 'python312.zip' 'python'"

:: Download get-pip.py
echo Downloading pip...
curl -L -o python\get-pip.py https://bootstrap.pypa.io/get-pip.py

:: Enable site-packages in embedded Python
:: Remove the "import site" line restriction
echo Configuring Python...
powershell -command "(Get-Content 'python\python312._pth') -replace '#import site', 'import site' | Set-Content 'python\python312._pth'"

:: Add Lib\site-packages to path file
echo Lib\site-packages>> python\python312._pth

:: Install pip
echo Installing pip...
python\python.exe python\get-pip.py --no-warn-script-location

:: Clean up
del python312.zip
del python\get-pip.py

:install_deps
echo.
echo Installing dependencies...
python\python.exe -m pip install --no-warn-script-location -r server\requirements.txt

if %errorlevel% neq 0 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo Run 'start-server.bat' to start the server
echo Run 'start-ui.bat' to start the web interface
echo.
pause
