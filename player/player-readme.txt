# Digital Signage Player

Cross-platform player client for the Digital Signage System.

## Quick Start

### Windows
1. Double-click `run-player.bat`
2. Enter your server URL and device key
3. Click Connect

### macOS / Linux
```bash
chmod +x run-player.sh
./run-player.sh
```

## Installation

### Requirements
- Python 3.8 or higher
- pywebview (`pip install pywebview`)

### Platform-Specific Dependencies

**Windows:** No additional dependencies (uses Edge WebView2)

**macOS:** 
```bash
pip install pyobjc
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.0
pip install pywebview
```

**Linux (Fedora):**
```bash
sudo dnf install python3-gobject gtk3 webkit2gtk3
pip install pywebview
```

## Building Standalone Executables

To create a single executable file that doesn't require Python:

```bash
pip install pyinstaller
python build_player.py
```

This creates:
- Windows: `dist/SignagePlayer.exe`
- macOS: `dist/SignagePlayer.app`
- Linux: `dist/SignagePlayer`

## Usage

1. **Get your device key** from the server web UI:
   - Go to Devices → Add Device
   - Copy the device key

2. **Configure the player:**
   - Enter the server URL (e.g., `http://192.168.1.100:8000`)
   - Enter your device key
   - Click "Test Connection" to verify
   - Click "Connect" to start

3. **Keyboard shortcuts:**
   - `Escape` - Toggle fullscreen
   - `Ctrl+S` - Show setup screen

## Files

- `player.py` - Main player application
- `player-requirements.txt` - Python dependencies
- `build_player.py` - Build script for executables
- `run-player.bat` - Windows launcher
- `run-player.sh` - macOS/Linux launcher
- `data/` - Local data directory (created automatically)
  - `config.json` - Player configuration
  - `content/` - Downloaded content cache

## Troubleshooting

### "Cannot reach server"
- Check that the server is running
- Verify the URL includes `http://` or `https://`
- Check firewall settings

### "Device not found"
- Verify your device key is correct
- Make sure the device exists in the server UI

### Black screen after connecting
- Check if content is assigned to the device
- Verify schedules are active for the current time
- Check the default display settings on the server

### Linux: WebKit errors
Make sure GTK and WebKit2 are installed:
```bash
sudo apt install gir1.2-webkit2-4.0
```