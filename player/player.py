#!/usr/bin/env python3
"""
Digital Signage Player - Cross-Platform Client
A self-contained player that runs on Windows, macOS, and Linux
"""

import os
import sys
import json
import time
import threading
import hashlib
import urllib.request
import urllib.error
import ssl
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import logging

# Setup paths - use app directory for portable mode, or user directory
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    APP_DIR = Path(sys.executable).parent
else:
    # Running as script
    APP_DIR = Path(__file__).parent

DATA_DIR = APP_DIR / "data"
CONTENT_DIR = DATA_DIR / "content"
CONFIG_FILE = DATA_DIR / "config.json"
LOG_FILE = DATA_DIR / "player.log"

# Create directories
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONTENT_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Config:
    server_url: str = ""
    device_key: str = ""
    sync_interval: int = 60
    fullscreen: bool = True
    window_width: int = 1280
    window_height: int = 720
    
    def save(self):
        CONFIG_FILE.write_text(json.dumps(self.__dict__, indent=2))
        logger.info("Configuration saved")
    
    @classmethod
    def load(cls) -> 'Config':
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                return cls(**data)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        return cls()


@dataclass 
class ContentItem:
    id: int
    name: str
    filename: str
    file_type: str
    url: str
    display_duration: float
    file_size: int
    
    @property
    def local_path(self) -> Path:
        return CONTENT_DIR / self.filename
    
    @property
    def local_url(self) -> str:
        return self.local_path.as_uri()


class SignagePlayer:
    """Main player controller"""
    
    def __init__(self, config: Config):
        self.config = config
        self.playlist: List[ContentItem] = []
        self.current_index: int = 0
        self.default_display: Optional[Dict] = None
        self.running: bool = False
        self.last_sync: float = 0
        self.sync_lock = threading.Lock()
        self.on_content_change = None  # Callback for UI updates
        
    def api_request(self, endpoint: str) -> Optional[Dict]:
        """Make API request to server"""
        if not self.config.server_url:
            return None
            
        url = f"{self.config.server_url.rstrip('/')}/api{endpoint}"
        
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(url)
            req.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP error {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            logger.error(f"URL error: {e.reason}")
        except Exception as e:
            logger.error(f"Request error: {e}")
        
        return None
    
    def download_file(self, url: str, local_path: Path) -> bool:
        """Download a file from the server"""
        if not self.config.server_url:
            return False
            
        full_url = f"{self.config.server_url.rstrip('/')}{url}"
        
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            logger.info(f"Downloading: {url}")
            
            with urllib.request.urlopen(full_url, timeout=300, context=ctx) as response:
                local_path.write_bytes(response.read())
            
            logger.info(f"Downloaded: {local_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False
    
    def sync_content(self) -> bool:
        """Sync content from server"""
        if not self.config.device_key:
            logger.warning("No device key configured")
            return False
            
        with self.sync_lock:
            logger.info("Syncing content...")
            
            # Get playlist
            playlist_data = self.api_request(f"/player/{self.config.device_key}/playlist")
            if not playlist_data:
                logger.error("Failed to get playlist")
                return False
            
            # Get config for default display
            config_data = self.api_request(f"/player/{self.config.device_key}/config")
            if config_data:
                self.default_display = config_data.get('default_display')
            
            # Parse playlist
            new_playlist = []
            for item_data in playlist_data.get('playlist', []):
                item = ContentItem(
                    id=item_data['id'],
                    name=item_data['name'],
                    filename=item_data['filename'],
                    file_type=item_data['file_type'],
                    url=item_data['url'],
                    display_duration=item_data['display_duration'],
                    file_size=item_data['file_size']
                )
                new_playlist.append(item)
            
            # Download missing content
            for item in new_playlist:
                if not item.local_path.exists() or item.local_path.stat().st_size != item.file_size:
                    self.download_file(item.url, item.local_path)
            
            # Download default display assets
            if self.default_display:
                if self.default_display.get('logo_url'):
                    logo_filename = self.default_display.get('logo_filename', 'logo.png')
                    logo_path = CONTENT_DIR / f"_logo_{logo_filename}"
                    if not logo_path.exists():
                        self.download_file(self.default_display['logo_url'], logo_path)
                    self.default_display['_local_logo'] = logo_path.as_uri()
                
                for bg in self.default_display.get('backgrounds', []):
                    bg_path = CONTENT_DIR / f"_bg_{bg['filename']}"
                    if not bg_path.exists():
                        self.download_file(bg['url'], bg_path)
                    bg['_local_url'] = bg_path.as_uri()
            
            # Clean up old files
            current_filenames = {item.filename for item in new_playlist}
            current_filenames.add('_logo_' + self.default_display.get('logo_filename', '')) if self.default_display else None
            for bg in (self.default_display or {}).get('backgrounds', []):
                current_filenames.add(f"_bg_{bg['filename']}")
            
            for file_path in CONTENT_DIR.iterdir():
                if file_path.name not in current_filenames and not file_path.name.startswith('_'):
                    try:
                        file_path.unlink()
                        logger.info(f"Removed old file: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Error removing file: {e}")
            
            self.playlist = new_playlist
            self.last_sync = time.time()
            
            logger.info(f"Sync complete. {len(new_playlist)} items in playlist")
            return True
    
    def get_current_content(self) -> Optional[ContentItem]:
        """Get current content item"""
        if not self.playlist:
            return None
        if self.current_index >= len(self.playlist):
            self.current_index = 0
        return self.playlist[self.current_index]
    
    def advance(self):
        """Move to next content item"""
        if self.playlist:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            if self.on_content_change:
                self.on_content_change()
    
    def get_current_duration(self) -> float:
        """Get duration for current content"""
        item = self.get_current_content()
        return item.display_duration if item else 10.0


# HTML template for the player display
PLAYER_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            background: #000;
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        #content-container {
            width: 100vw;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }
        
        #background {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-size: cover;
            background-position: center;
            z-index: 1;
            transition: opacity 1s ease;
        }
        
        #media {
            position: relative;
            z-index: 2;
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }
        
        #logo {
            position: relative;
            z-index: 2;
            max-width: 80%;
            max-height: 80%;
            object-fit: contain;
        }
        
        /* Setup screen styles */
        #setup-screen {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            z-index: 1000;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
        }
        
        #setup-screen.active { display: flex; }
        
        .setup-container {
            background: rgba(255,255,255,0.1);
            padding: 40px;
            border-radius: 16px;
            width: 90%;
            max-width: 500px;
            backdrop-filter: blur(10px);
        }
        
        .setup-title {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
            text-align: center;
        }
        
        .setup-subtitle {
            color: rgba(255,255,255,0.6);
            margin-bottom: 32px;
            text-align: center;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
        }
        
        .form-group input {
            width: 100%;
            padding: 12px 16px;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            background: rgba(0,0,0,0.3);
            color: white;
            font-size: 16px;
            outline: none;
            transition: border-color 0.2s;
        }
        
        .form-group input:focus {
            border-color: #6366f1;
        }
        
        .form-group input::placeholder {
            color: rgba(255,255,255,0.4);
        }
        
        .btn {
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-primary {
            background: #6366f1;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5558e3;
        }
        
        .btn-secondary {
            background: rgba(255,255,255,0.1);
            color: white;
            margin-top: 12px;
        }
        
        .btn-secondary:hover {
            background: rgba(255,255,255,0.2);
        }
        
        .status {
            margin-top: 20px;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            display: none;
        }
        
        .status.error {
            display: block;
            background: rgba(239, 68, 68, 0.2);
            color: #fca5a5;
        }
        
        .status.success {
            display: block;
            background: rgba(34, 197, 94, 0.2);
            color: #86efac;
        }
        
        /* Loading indicator */
        #loading {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            z-index: 100;
            display: none;
        }
        
        #loading.active { display: block; }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .checkbox-group input[type="checkbox"] {
            width: 20px;
            height: 20px;
        }
    </style>
</head>
<body>
    <div id="content-container">
        <div id="background"></div>
        <img id="media" style="display: none;">
        <video id="video" style="display: none;" muted></video>
        <img id="logo" style="display: none;">
    </div>
    
    <div id="setup-screen" class="active">
        <div class="setup-container">
            <h1 class="setup-title">📺 Signage Player</h1>
            <p class="setup-subtitle">Connect to your signage server</p>
            
            <div class="form-group">
                <label>Server URL</label>
                <input type="text" id="server-url" placeholder="http://192.168.1.100:8000">
            </div>
            
            <div class="form-group">
                <label>Device Key</label>
                <input type="text" id="device-key" placeholder="Enter your device key">
            </div>
            
            <div class="form-group">
                <div class="checkbox-group">
                    <input type="checkbox" id="fullscreen-check" checked>
                    <label for="fullscreen-check">Start in fullscreen</label>
                </div>
            </div>
            
            <button class="btn btn-primary" onclick="connect()">Connect</button>
            <button class="btn btn-secondary" onclick="testConnection()">Test Connection</button>
            
            <div id="status" class="status"></div>
        </div>
    </div>
    
    <div id="loading">Syncing...</div>
    
    <script>
        // State
        let config = {};
        let playlist = [];
        let currentIndex = 0;
        let defaultDisplay = null;
        let syncInterval = null;
        let advanceTimeout = null;
        
        // Initialize
        window.addEventListener('load', () => {
            loadConfig();
        });
        
        function loadConfig() {
            if (window.pywebview) {
                window.pywebview.api.get_config().then(cfg => {
                    config = cfg;
                    document.getElementById('server-url').value = cfg.server_url || '';
                    document.getElementById('device-key').value = cfg.device_key || '';
                    document.getElementById('fullscreen-check').checked = cfg.fullscreen !== false;
                    
                    if (cfg.server_url && cfg.device_key) {
                        connect();
                    }
                });
            }
        }
        
        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status ' + type;
        }
        
        function testConnection() {
            const serverUrl = document.getElementById('server-url').value.trim();
            const deviceKey = document.getElementById('device-key').value.trim();
            
            if (!serverUrl || !deviceKey) {
                showStatus('Please enter server URL and device key', 'error');
                return;
            }
            
            showStatus('Testing connection...', '');
            document.getElementById('status').style.display = 'block';
            document.getElementById('status').style.background = 'rgba(255,255,255,0.1)';
            document.getElementById('status').style.color = 'white';
            
            if (window.pywebview) {
                window.pywebview.api.test_connection(serverUrl, deviceKey).then(result => {
                    if (result.success) {
                        showStatus('✓ Connection successful! Device: ' + result.device_name, 'success');
                    } else {
                        showStatus('✗ ' + result.error, 'error');
                    }
                });
            }
        }
        
        function connect() {
            const serverUrl = document.getElementById('server-url').value.trim();
            const deviceKey = document.getElementById('device-key').value.trim();
            const fullscreen = document.getElementById('fullscreen-check').checked;
            
            if (!serverUrl || !deviceKey) {
                showStatus('Please enter server URL and device key', 'error');
                return;
            }
            
            if (window.pywebview) {
                window.pywebview.api.save_config(serverUrl, deviceKey, fullscreen).then(() => {
                    window.pywebview.api.sync_content().then(result => {
                        if (result.success) {
                            playlist = result.playlist;
                            defaultDisplay = result.default_display;
                            
                            document.getElementById('setup-screen').classList.remove('active');
                            
                            if (fullscreen) {
                                window.pywebview.api.toggle_fullscreen();
                            }
                            
                            startPlayback();
                            startSyncLoop();
                        } else {
                            showStatus('Failed to sync: ' + result.error, 'error');
                        }
                    });
                });
            }
        }
        
        function startSyncLoop() {
            syncInterval = setInterval(() => {
                document.getElementById('loading').classList.add('active');
                
                if (window.pywebview) {
                    window.pywebview.api.sync_content().then(result => {
                        document.getElementById('loading').classList.remove('active');
                        if (result.success) {
                            playlist = result.playlist;
                            defaultDisplay = result.default_display;
                        }
                    });
                }
            }, 60000); // Sync every 60 seconds
        }
        
        function startPlayback() {
            showContent();
        }
        
        function showContent() {
            const media = document.getElementById('media');
            const video = document.getElementById('video');
            const logo = document.getElementById('logo');
            const background = document.getElementById('background');
            
            // Hide all first
            media.style.display = 'none';
            video.style.display = 'none';
            logo.style.display = 'none';
            
            if (playlist.length > 0) {
                const item = playlist[currentIndex];
                const localPath = item._local_url || item.local_url;
                
                if (item.file_type === 'video') {
                    video.src = localPath;
                    video.style.display = 'block';
                    video.play();
                    
                    video.onended = () => {
                        advance();
                    };
                } else {
                    media.src = localPath;
                    media.style.display = 'block';
                    
                    advanceTimeout = setTimeout(() => {
                        advance();
                    }, item.display_duration * 1000);
                }
                
                background.style.backgroundColor = '#000';
                background.style.backgroundImage = 'none';
                
            } else if (defaultDisplay) {
                // Show default display
                if (defaultDisplay.background_mode === 'solid') {
                    background.style.backgroundColor = defaultDisplay.background_color || '#000';
                    background.style.backgroundImage = 'none';
                } else if (defaultDisplay.backgrounds && defaultDisplay.backgrounds.length > 0) {
                    const bgUrl = defaultDisplay.backgrounds[0]._local_url;
                    background.style.backgroundImage = `url('${bgUrl}')`;
                }
                
                if (defaultDisplay._local_logo) {
                    logo.src = defaultDisplay._local_logo;
                    logo.style.display = 'block';
                    logo.style.transform = `scale(${defaultDisplay.logo_scale || 0.5})`;
                }
                
                // Refresh default display periodically
                advanceTimeout = setTimeout(() => {
                    showContent();
                }, 10000);
            } else {
                // Nothing to show
                background.style.backgroundColor = '#000';
                advanceTimeout = setTimeout(() => {
                    showContent();
                }, 5000);
            }
        }
        
        function advance() {
            if (advanceTimeout) {
                clearTimeout(advanceTimeout);
            }
            
            if (playlist.length > 0) {
                currentIndex = (currentIndex + 1) % playlist.length;
            }
            
            showContent();
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (window.pywebview) {
                    window.pywebview.api.toggle_fullscreen();
                }
            } else if (e.key === 's' && e.ctrlKey) {
                // Ctrl+S to show setup
                document.getElementById('setup-screen').classList.add('active');
            }
        });
    </script>
</body>
</html>
'''


class PlayerAPI:
    """API exposed to the webview JavaScript"""
    
    def __init__(self, player: SignagePlayer, window=None):
        self.player = player
        self.window = window
    
    def set_window(self, window):
        self.window = window
    
    def get_config(self) -> Dict:
        return self.player.config.__dict__
    
    def save_config(self, server_url: str, device_key: str, fullscreen: bool):
        self.player.config.server_url = server_url
        self.player.config.device_key = device_key
        self.player.config.fullscreen = fullscreen
        self.player.config.save()
    
    def test_connection(self, server_url: str, device_key: str) -> Dict:
        """Test connection to server"""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            url = f"{server_url.rstrip('/')}/api/player/{device_key}/config"
            req = urllib.request.Request(url)
            
            with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
                data = json.loads(response.read().decode())
                return {
                    'success': True,
                    'device_name': data.get('device', {}).get('name', 'Unknown')
                }
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {'success': False, 'error': 'Device not found. Check your device key.'}
            return {'success': False, 'error': f'HTTP error: {e.code}'}
        except urllib.error.URLError as e:
            return {'success': False, 'error': f'Cannot reach server: {e.reason}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def sync_content(self) -> Dict:
        """Sync content and return playlist"""
        try:
            success = self.player.sync_content()
            if success:
                # Convert playlist to dicts with local URLs
                playlist_data = []
                for item in self.player.playlist:
                    playlist_data.append({
                        'id': item.id,
                        'name': item.name,
                        'file_type': item.file_type,
                        'display_duration': item.display_duration,
                        '_local_url': item.local_url
                    })
                
                return {
                    'success': True,
                    'playlist': playlist_data,
                    'default_display': self.player.default_display
                }
            else:
                return {'success': False, 'error': 'Sync failed'}
        except Exception as e:
            logger.error(f"Sync error: {e}")
            return {'success': False, 'error': str(e)}
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.window:
            self.window.toggle_fullscreen()
    
    def exit_app(self):
        """Exit the application"""
        if self.window:
            self.window.destroy()


def main():
    """Main entry point"""
    try:
        import webview
    except ImportError:
        print("=" * 50)
        print("ERROR: pywebview is not installed")
        print("=" * 50)
        print("\nInstall it with:")
        print("  pip install pywebview")
        print("\nOn Linux, you may also need:")
        print("  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.0")
        print("\nOn macOS:")
        print("  pip install pyobjc")
        sys.exit(1)
    
    # Load config
    config = Config.load()
    
    # Create player
    player = SignagePlayer(config)
    
    # Create API
    api = PlayerAPI(player)
    
    # Create window
    window = webview.create_window(
        'Signage Player',
        html=PLAYER_HTML,
        js_api=api,
        width=config.window_width,
        height=config.window_height,
        resizable=True,
        frameless=False,
        easy_drag=False,
        background_color='#000000'
    )
    
    api.set_window(window)
    
    # Start webview
    webview.start(debug=False)


if __name__ == "__main__":
    main()