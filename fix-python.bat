@echo off
echo Fixing embedded Python setup...
echo.

cd /d "%~dp0"

if not exist "python\python.exe" (
    echo ERROR: Embedded Python not found. Run setup.bat first.
    pause
    exit /b 1
)

echo Installing setuptools and wheel...
python\python.exe -m pip install --upgrade pip setuptools wheel --no-warn-script-location

echo.
echo Done! Now try running player\run-player.bat again.
pause