#!/usr/bin/env python3
"""
Build script to create standalone executables for Windows, macOS, and Linux
"""
import os
import sys
import platform
import subprocess
from pathlib import Path

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def build():
    """Build the executable for the current platform"""
    
    if not check_pyinstaller():
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Determine platform-specific options
    system = platform.system()
    
    # Base PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",           # Single executable
        "--windowed",          # No console window
        "--name", "SignagePlayer",
        "--clean",
    ]
    
    # Platform-specific options
    if system == "Windows":
        # Windows-specific
        cmd.extend([
            "--add-data", "data;data",  # Include data folder
        ])
        # Add icon if exists
        if Path("icon.ico").exists():
            cmd.extend(["--icon", "icon.ico"])
            
    elif system == "Darwin":
        # macOS-specific
        cmd.extend([
            "--add-data", "data:data",
            "--osx-bundle-identifier", "com.signage.player",
        ])
        if Path("icon.icns").exists():
            cmd.extend(["--icon", "icon.icns"])
            
    else:
        # Linux
        cmd.extend([
            "--add-data", "data:data",
        ])
        if Path("icon.png").exists():
            cmd.extend(["--icon", "icon.png"])
    
    # Add the main script
    cmd.append("player.py")
    
    print(f"Building for {system}...")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    # Run PyInstaller
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print()
        print("=" * 50)
        print("Build successful!")
        print("=" * 50)
        
        if system == "Windows":
            print("Executable: dist/SignagePlayer.exe")
        elif system == "Darwin":
            print("Application: dist/SignagePlayer.app")
        else:
            print("Executable: dist/SignagePlayer")
    else:
        print("Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    build()