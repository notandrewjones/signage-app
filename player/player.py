#!/usr/bin/env python3
# player/player.py
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
    access_code: str = ""
    sync_interval: int = 60
    fullscreen: bool = True
    window_width: int = 1280
    window_height: int = 720
    
    def save(self):
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(self.__dict__, indent=2))
        logger.info(f"Configuration saved to {CONFIG_FILE}")
        logger.info(f"Config contents: server_url={self.server_url}, access_code={self.access_code}")
    
    @classmethod
    def load(cls) -> 'Config':
        logger.info(f"Looking for config at: {CONFIG_FILE}")
        logger.info(f"Config file exists: {CONFIG_FILE.exists()}")
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                logger.info(f"Loaded config data: {data}")
                # Handle migration from old device_key to access_code
                if 'device_key' in data and 'access_code' not in data:
                    data['access_code'] = data.pop('device_key')
                config = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
                logger.info(f"Config object: server_url={config.server_url}, access_code={config.access_code}")
                return config
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        else:
            logger.info("No config file found, using defaults")
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
        if not self.config.server_url or not url:
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
        if not self.config.access_code or not self.config.server_url:
            logger.warning("No access code or server URL configured")
            return False
            
        with self.sync_lock:
            logger.info("Syncing content...")
            
            # Get playlist
            playlist_data = self.api_request(f"/player/{self.config.access_code}/playlist")
            if not playlist_data:
                logger.error("Failed to get playlist")
                return False
            
            # Get config for default display
            config_data = self.api_request(f"/player/{self.config.access_code}/config")
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
                logo_url = self.default_display.get('logo_url')
                if logo_url:
                    logo_filename = self.default_display.get('logo_filename', 'logo.png')
                    logo_path = CONTENT_DIR / f"_logo_{logo_filename}"
                    if not logo_path.exists():
                        self.download_file(logo_url, logo_path)
                    self.default_display['_local_logo'] = logo_path.as_uri()
                
                for bg in self.default_display.get('backgrounds') or []:
                    bg_url = bg.get('url')
                    if bg_url:
                        bg_path = CONTENT_DIR / f"_bg_{bg['filename']}"
                        if not bg_path.exists():
                            self.download_file(bg_url, bg_path)
                        bg['_local_url'] = bg_path.as_uri()
            
            # Clean up old files
            current_filenames = {item.filename for item in new_playlist}
            if self.default_display:
                logo_filename = self.default_display.get('logo_filename')
                if logo_filename:
                    current_filenames.add(f'_logo_{logo_filename}')
                for bg in self.default_display.get('backgrounds') or []:
                    bg_filename = bg.get('filename')
                    if bg_filename:
                        current_filenames.add(f"_bg_{bg_filename}")
            
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
        
        html, body {
            width: 100%;
            height: 100%;
            background: #000;
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        #content-container {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
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
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #0f0f1a 100%);
            z-index: 1000;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
        }
        
        #setup-screen.active { display: flex; }
        
        .setup-container {
            text-align: center;
            width: 90%;
            max-width: 480px;
        }
        
        .setup-icon {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            border-radius: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 24px;
            font-size: 40px;
        }
        
        .setup-title {
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }
        
        .setup-subtitle {
            color: rgba(255,255,255,0.5);
            margin-bottom: 48px;
            font-size: 16px;
        }
        
        /* Step indicator */
        .steps {
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-bottom: 32px;
        }
        
        .step-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: rgba(255,255,255,0.2);
            transition: all 0.3s;
        }
        
        .step-dot.active {
            background: #6366f1;
            width: 24px;
            border-radius: 4px;
        }
        
        .step-dot.complete {
            background: #22c55e;
        }
        
        /* Form styles */
        .form-section {
            display: none;
            animation: fadeIn 0.3s ease;
        }
        
        .form-section.active { display: block; }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .form-label {
            display: block;
            text-align: left;
            margin-bottom: 8px;
            font-weight: 500;
            color: rgba(255,255,255,0.7);
            font-size: 14px;
        }
        
        .form-input {
            width: 100%;
            padding: 16px 20px;
            border: 2px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            background: rgba(255,255,255,0.05);
            color: white;
            font-size: 18px;
            outline: none;
            transition: all 0.2s;
            margin-bottom: 16px;
        }
        
        .form-input:focus {
            border-color: #6366f1;
            background: rgba(99, 102, 241, 0.1);
        }
        
        .form-input::placeholder {
            color: rgba(255,255,255,0.3);
        }
        
        /* Access code input - large and prominent */
        .access-code-input {
            font-size: 32px;
            font-weight: 700;
            text-align: center;
            letter-spacing: 8px;
            font-family: 'SF Mono', Monaco, monospace;
            padding: 24px;
        }
        
        .access-code-hint {
            color: rgba(255,255,255,0.4);
            font-size: 14px;
            margin-top: -8px;
            margin-bottom: 24px;
        }
        
        /* Buttons */
        .btn {
            width: 100%;
            padding: 16px 24px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            margin-top: 8px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
        }
        
        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .btn-secondary {
            background: rgba(255,255,255,0.1);
            color: white;
        }
        
        .btn-secondary:hover {
            background: rgba(255,255,255,0.15);
        }
        
        .btn-text {
            background: none;
            color: rgba(255,255,255,0.5);
            padding: 12px;
        }
        
        .btn-text:hover {
            color: white;
        }
        
        /* Status messages */
        .status {
            margin-top: 24px;
            padding: 16px;
            border-radius: 12px;
            text-align: center;
            display: none;
            animation: fadeIn 0.3s ease;
        }
        
        .status.error {
            display: block;
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #fca5a5;
        }
        
        .status.success {
            display: block;
            background: rgba(34, 197, 94, 0.15);
            border: 1px solid rgba(34, 197, 94, 0.3);
            color: #86efac;
        }
        
        .status.loading {
            display: block;
            background: rgba(99, 102, 241, 0.15);
            border: 1px solid rgba(99, 102, 241, 0.3);
            color: #a5b4fc;
        }
        
        /* Server discovery */
        .server-list {
            margin: 16px 0;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .server-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 16px;
            background: rgba(255,255,255,0.05);
            border: 2px solid transparent;
            border-radius: 12px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.2s;
            text-align: left;
        }
        
        .server-item:hover {
            background: rgba(255,255,255,0.1);
        }
        
        .server-item.selected {
            border-color: #6366f1;
            background: rgba(99, 102, 241, 0.1);
        }
        
        .server-icon {
            width: 40px;
            height: 40px;
            background: rgba(99, 102, 241, 0.2);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .server-info {
            flex: 1;
        }
        
        .server-name {
            font-weight: 600;
            margin-bottom: 2px;
        }
        
        .server-ip {
            font-size: 13px;
            color: rgba(255,255,255,0.5);
            font-family: 'SF Mono', Monaco, monospace;
        }
        
        .divider {
            display: flex;
            align-items: center;
            margin: 24px 0;
            color: rgba(255,255,255,0.3);
            font-size: 13px;
        }
        
        .divider::before, .divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: rgba(255,255,255,0.1);
        }
        
        .divider::before { margin-right: 16px; }
        .divider::after { margin-left: 16px; }
        
        /* Success state */
        .success-icon {
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 24px;
            font-size: 40px;
        }
        
        .device-name {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
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
    
    <div id="setup-screen">
        <div class="setup-container">
            <div class="setup-icon">📺</div>
            <h1 class="setup-title">Signage Player</h1>
            <p class="setup-subtitle">Connect to your signage server</p>
            
            <div class="steps">
                <div class="step-dot active" id="step1"></div>
                <div class="step-dot" id="step2"></div>
            </div>
            
            <!-- Step 1: Server Connection -->
            <div class="form-section active" id="section-server">
                <div id="discovered-servers"></div>
                
                <div class="divider">or enter manually</div>
                
                <label class="form-label">Server Address</label>
                <input type="text" id="server-url" class="form-input" placeholder="http://192.168.1.100:8000">
                
                <button class="btn btn-primary" onclick="connectToServer()">Continue</button>
                <button class="btn btn-text" onclick="scanForServers()">🔍 Scan for servers</button>
                
                <div id="server-status" class="status"></div>
            </div>
            
            <!-- Step 2: Access Code -->
            <div class="form-section" id="section-code">
                <label class="form-label">Enter your 6-digit access code</label>
                <input type="text" id="access-code" class="form-input access-code-input" 
                       placeholder="000000" maxlength="6" inputmode="numeric" pattern="[0-9]*">
                <p class="access-code-hint">Find this code in your server's device settings</p>
                
                <button class="btn btn-primary" onclick="registerDevice()" id="btn-register">Connect</button>
                <button class="btn btn-text" onclick="goToStep(1)">← Back</button>
                
                <div id="code-status" class="status"></div>
            </div>
            
            <!-- Success State -->
            <div class="form-section" id="section-success">
                <div class="success-icon">✓</div>
                <p class="device-name" id="connected-device-name">Device Connected</p>
                <p class="setup-subtitle">Starting playback...</p>
            </div>
        </div>
    </div>
    
    <script>
        // State
        let config = {};
        let serverUrl = '';
        let accessCode = '';
        let playlist = [];
        let currentIndex = 0;
        let defaultDisplay = null;
        let syncInterval = null;
        let advanceTimeout = null;
        
        // Initialize
        console.log('=== SCRIPT LOADED ===');
        window.addEventListener('load', () => {
            console.log('=== WINDOW LOAD EVENT ===');
            console.log('Window loaded, waiting for pywebview...');
            // Wait for pywebview API to be ready
            waitForPywebview().then(() => {
                console.log('=== PYWEBVIEW READY ===');
                console.log('pywebview ready, loading config...');
                loadConfig();
            });
            
            // Auto-format access code input
            const codeInput = document.getElementById('access-code');
            codeInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/[^0-9]/g, '').slice(0, 6);
                document.getElementById('btn-register').disabled = e.target.value.length !== 6;
            });
            
            // Enter key handlers
            document.getElementById('server-url').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') connectToServer();
            });
            codeInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && e.target.value.length === 6) registerDevice();
            });
        });
        
        function waitForPywebview() {
            return new Promise((resolve) => {
                // Check if API is ready - either via js_api or window.expose
                function isReady() {
                    return (window.pywebview && window.pywebview.api && Object.keys(window.pywebview.api).length > 0) 
                        || typeof window.get_config === 'function';
                }
                
                if (isReady()) {
                    resolve();
                } else {
                    // Check every 100ms for up to 5 seconds
                    let attempts = 0;
                    const interval = setInterval(() => {
                        attempts++;
                        if (isReady()) {
                            clearInterval(interval);
                            resolve();
                        } else if (attempts > 50) {
                            clearInterval(interval);
                            console.error('pywebview API not available after 5 seconds');
                            resolve(); // Continue anyway
                        }
                    }, 100);
                }
            });
        }
        
        // Helper to get API function (works with both js_api and expose)
        function getApi(name) {
            return window[name] || (window.pywebview && window.pywebview.api && window.pywebview.api[name]);
        }
        
        function loadConfig() {
            console.log('loadConfig called');
            
            let getConfigFn = getApi('get_config');
            console.log('get_config function:', getConfigFn);
            
            if (getConfigFn) {
                getConfigFn().then(cfg => {
                    console.log('Config loaded:', JSON.stringify(cfg));
                    config = cfg;  // Set config FIRST
                    document.getElementById('server-url').value = cfg.server_url || '';
                    
                    // If already configured with both server and access code, auto-connect
                    if (cfg.server_url && cfg.access_code) {
                        console.log('Found saved config, auto-connecting...');
                        serverUrl = cfg.server_url;
                        accessCode = cfg.access_code;
                        autoConnect();
                    } else {
                        console.log('No saved config, showing setup...');
                        showSetupScreen();
                        scanForServers();
                    }
                }).catch(err => {
                    console.error('Error loading config:', err);
                    showSetupScreen();
                    scanForServers();
                });
            } else {
                console.log('No API yet, showing setup...');
                showSetupScreen();
                scanForServers();
            }
        }
        
        // Called by Python after expose() completes
        function retryLoadConfig() {
            console.log('retryLoadConfig called - API should be ready now');
            loadConfig();
        }
        
        function showSetupScreen() {
            document.getElementById('setup-screen').classList.add('active');
            document.getElementById('setup-screen').style.display = 'flex';
            goToStep(1);
        }
        
        function autoConnect() {
            console.log('Auto-connecting with config:', JSON.stringify(config));
            showStatus('server-status', 'Reconnecting...', 'loading');
            
            let syncFn = getApi('sync_content');
            if (syncFn) {
                syncFn().then(result => {
                    console.log('Auto-connect sync result:', JSON.stringify(result));
                    if (result.success) {
                        playlist = result.playlist || [];
                        defaultDisplay = result.default_display;
                        console.log('Playlist items:', playlist.length);
                        
                        // Hide setup screen completely
                        document.getElementById('setup-screen').style.display = 'none';
                        document.getElementById('setup-screen').classList.remove('active');
                        
                        // Go fullscreen if configured
                        if (config.fullscreen) {
                            let toggleFn = getApi('toggle_fullscreen');
                            if (toggleFn) toggleFn();
                        }
                        
                        startPlayback();
                        startSyncLoop();
                    } else {
                        // Connection failed, show setup
                        console.error('Auto-connect failed:', result.error);
                        hideStatus('server-status');
                        showSetupScreen();
                        scanForServers();
                    }
                }).catch(err => {
                    console.error('Auto-connect exception:', err);
                    hideStatus('server-status');
                    showSetupScreen();
                    scanForServers();
                });
            } else {
                console.error('No sync_content API available');
                showSetupScreen();
            }
        }
        
        function goToStep(step) {
            document.querySelectorAll('.form-section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.step-dot').forEach(d => d.classList.remove('active', 'complete'));
            
            if (step === 1) {
                document.getElementById('section-server').classList.add('active');
                document.getElementById('step1').classList.add('active');
            } else if (step === 2) {
                document.getElementById('section-code').classList.add('active');
                document.getElementById('step1').classList.add('complete');
                document.getElementById('step2').classList.add('active');
                document.getElementById('access-code').focus();
            } else if (step === 3) {
                document.getElementById('section-success').classList.add('active');
                document.getElementById('step1').classList.add('complete');
                document.getElementById('step2').classList.add('complete');
            }
        }
        
        function showStatus(id, message, type) {
            const status = document.getElementById(id);
            status.textContent = message;
            status.className = 'status ' + type;
        }
        
        function hideStatus(id) {
            document.getElementById(id).className = 'status';
        }
        
        function scanForServers() {
            // In a real implementation, this would scan the network
            // For now, we'll just check common ports on the local network
            const container = document.getElementById('discovered-servers');
            container.innerHTML = '<div class="status loading">Scanning for servers...</div>';
            
            let discoverFn = getApi('discover_servers');
            if (discoverFn) {
                discoverFn().then(servers => {
                    if (servers.length === 0) {
                        container.innerHTML = '';
                    } else {
                        let html = '<div class="server-list">';
                        servers.forEach((server, i) => {
                            html += `
                                <div class="server-item" onclick="selectServer('${server.url}', this)">
                                    <div class="server-icon">🖥️</div>
                                    <div class="server-info">
                                        <div class="server-name">${server.name}</div>
                                        <div class="server-ip">${server.url}</div>
                                    </div>
                                </div>
                            `;
                        });
                        html += '</div>';
                        container.innerHTML = html;
                    }
                });
            } else {
                container.innerHTML = '';
            }
        }
        
        function selectServer(url, element) {
            document.querySelectorAll('.server-item').forEach(s => s.classList.remove('selected'));
            element.classList.add('selected');
            document.getElementById('server-url').value = url;
        }
        
        function connectToServer() {
            serverUrl = document.getElementById('server-url').value.trim();
            
            if (!serverUrl) {
                showStatus('server-status', 'Please enter a server address', 'error');
                return;
            }
            
            // Ensure URL has protocol
            if (!serverUrl.startsWith('http://') && !serverUrl.startsWith('https://')) {
                serverUrl = 'http://' + serverUrl;
                document.getElementById('server-url').value = serverUrl;
            }
            
            showStatus('server-status', 'Connecting...', 'loading');
            
            let testFn = getApi('test_server');
            if (testFn) {
                testFn(serverUrl).then(result => {
                    if (result.success) {
                        hideStatus('server-status');
                        goToStep(2);
                    } else {
                        showStatus('server-status', result.error || 'Could not connect to server', 'error');
                    }
                });
            } else {
                // For testing without pywebview
                setTimeout(() => {
                    hideStatus('server-status');
                    goToStep(2);
                }, 1000);
            }
        }
        
        function registerDevice() {
            accessCode = document.getElementById('access-code').value.trim();
            
            if (accessCode.length !== 6) {
                showStatus('code-status', 'Please enter a 6-digit code', 'error');
                return;
            }
            
            showStatus('code-status', 'Verifying...', 'loading');
            
            let registerFn = getApi('register_device');
            let saveFn = getApi('save_config');
            let syncFn = getApi('sync_content');
            let toggleFn = getApi('toggle_fullscreen');
            
            if (registerFn) {
                registerFn(serverUrl, accessCode).then(result => {
                    console.log('Register result:', result);
                    if (result.success) {
                        document.getElementById('connected-device-name').textContent = result.device_name;
                        goToStep(3);
                        
                        // Save config and start playback
                        if (saveFn) {
                            saveFn(serverUrl, accessCode, true).then(() => {
                                console.log('Config saved, syncing content...');
                                setTimeout(() => {
                                    if (syncFn) {
                                        syncFn().then(syncResult => {
                                            console.log('Sync result:', syncResult);
                                            if (syncResult.success) {
                                                playlist = syncResult.playlist || [];
                                                defaultDisplay = syncResult.default_display;
                                                console.log('Playlist items:', playlist.length);
                                                console.log('Default display:', defaultDisplay);
                                                
                                                // Hide setup screen and start
                                                document.getElementById('setup-screen').style.display = 'none';
                                                if (toggleFn) toggleFn();
                                                startPlayback();
                                                startSyncLoop();
                                            } else {
                                                console.error('Sync failed:', syncResult.error);
                                                showStatus('code-status', 'Sync failed: ' + (syncResult.error || 'Unknown error'), 'error');
                                                goToStep(2);
                                            }
                                        }).catch(err => {
                                            console.error('Sync exception:', err);
                                            showStatus('code-status', 'Sync error: ' + err, 'error');
                                            goToStep(2);
                                        });
                                    }
                                }, 1500);
                            });
                        }
                    } else {
                        showStatus('code-status', result.error || 'Invalid access code', 'error');
                    }
                }).catch(err => {
                    console.error('Register exception:', err);
                    showStatus('code-status', 'Connection error: ' + err, 'error');
                });
            }
        }
        
        function startSyncLoop() {
            syncInterval = setInterval(() => {
                let syncFn = getApi('sync_content');
                if (syncFn) {
                    syncFn().then(result => {
                        if (result.success) {
                            playlist = result.playlist;
                            defaultDisplay = result.default_display;
                        }
                    });
                }
            }, 60000);
        }
        
        function startPlayback() {
            console.log('Starting playback...');
            console.log('Playlist:', JSON.stringify(playlist));
            console.log('Default display:', JSON.stringify(defaultDisplay));
            showContent();
        }
        
        function showContent() {
            console.log('showContent called, playlist length:', playlist ? playlist.length : 0, 'currentIndex:', currentIndex);
            
            const media = document.getElementById('media');
            const video = document.getElementById('video');
            const logo = document.getElementById('logo');
            const background = document.getElementById('background');
            
            media.style.display = 'none';
            video.style.display = 'none';
            logo.style.display = 'none';
            
            if (playlist && playlist.length > 0) {
                const item = playlist[currentIndex];
                const localPath = item._local_url || item.local_url;
                console.log('Showing content:', item.name, 'type:', item.file_type, 'path:', localPath);
                
                if (item.file_type === 'video') {
                    video.src = localPath;
                    video.style.display = 'block';
                    video.play().catch(e => console.error('Video play error:', e));
                    video.onended = () => advance();
                    video.onerror = (e) => {
                        console.error('Video error:', e);
                        advance();
                    };
                } else {
                    media.src = localPath;
                    media.style.display = 'block';
                    media.onerror = (e) => {
                        console.error('Image error:', e, 'src:', localPath);
                    };
                    media.onload = () => {
                        console.log('Image loaded successfully');
                    };
                    advanceTimeout = setTimeout(() => advance(), item.display_duration * 1000);
                }
                
                background.style.backgroundColor = '#000';
                background.style.backgroundImage = 'none';
                
            } else if (defaultDisplay) {
                console.log('Showing default display');
                if (defaultDisplay.background_mode === 'solid') {
                    background.style.backgroundColor = defaultDisplay.background_color || '#000';
                    background.style.backgroundImage = 'none';
                } else if (defaultDisplay.backgrounds && defaultDisplay.backgrounds.length > 0) {
                    const bgUrl = defaultDisplay.backgrounds[0]._local_url;
                    if (bgUrl) {
                        background.style.backgroundImage = `url('${bgUrl}')`;
                    }
                }
                
                if (defaultDisplay._local_logo) {
                    logo.src = defaultDisplay._local_logo;
                    logo.style.display = 'block';
                    logo.style.transform = `scale(${defaultDisplay.logo_scale || 0.5})`;
                }
                
                advanceTimeout = setTimeout(() => showContent(), 10000);
            } else {
                console.log('No content or default display, showing black screen');
                background.style.backgroundColor = '#000';
                advanceTimeout = setTimeout(() => showContent(), 5000);
            }
        }
        
        function advance() {
            if (advanceTimeout) clearTimeout(advanceTimeout);
            if (playlist.length > 0) {
                currentIndex = (currentIndex + 1) % playlist.length;
            }
            showContent();
        }
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                let toggleFn = getApi('toggle_fullscreen');
                if (toggleFn) toggleFn();
            } else if (e.key === 's' && e.ctrlKey) {
                document.getElementById('setup-screen').classList.add('active');
                goToStep(1);
            }
        });
    </script>
</body>
</html>
'''


class PlayerAPI:
    """API exposed to the webview JavaScript"""
    
    def __init__(self, player, window=None):
        self.player = player
        self.window = window
    
    def set_window(self, window):
        self.window = window
    
    def get_config(self):
        config_dict = dict(self.player.config.__dict__)
        logger.info(f"get_config called, returning: {config_dict}")
        return config_dict
    
    def save_config(self, server_url, access_code, fullscreen):
        logger.info(f"save_config called: server_url={server_url}, access_code={access_code}")
        self.player.config.server_url = server_url
        self.player.config.access_code = access_code
        self.player.config.fullscreen = fullscreen
        self.player.config.save()
    
    def discover_servers(self):
        """Discover signage servers - check localhost first (instant)"""
        servers = []
        
        # Check localhost first - this should be instant
        for port in [8000, 8080, 5000]:
            result = self._check_server(f'http://localhost:{port}')
            if result:
                servers.append(result)
                break  # Found localhost, that's probably it
        
        # Also check 127.0.0.1 if localhost didn't work
        if not servers:
            result = self._check_server('http://127.0.0.1:8000')
            if result:
                servers.append(result)
        
        return servers
    
    def _get_local_ip(self) -> Optional[str]:
        """Get local IP address"""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return None
    
    def _check_server(self, url: str) -> Optional[Dict]:
        """Check if a server exists at the given URL"""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(f"{url}/api/discover")
            with urllib.request.urlopen(req, timeout=0.5, context=ctx) as response:
                data = json.loads(response.read().decode())
                return {
                    'url': url,
                    'name': data.get('name', 'Signage Server'),
                    'ip': data.get('ip', url)
                }
        except:
            return None
    
    def test_server(self, server_url):
        """Test connection to a server"""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            url = f"{server_url.rstrip('/')}/api/discover"
            req = urllib.request.Request(url)
            
            with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
                data = json.loads(response.read().decode())
                return {'success': True, 'server_name': data.get('name', 'Signage Server')}
        except urllib.error.URLError as e:
            return {'success': False, 'error': f'Cannot reach server: {e.reason}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def register_device(self, server_url, access_code):
        """Register with a server using access code"""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            url = f"{server_url.rstrip('/')}/api/player/register"
            data = urllib.parse.urlencode({'access_code': access_code}).encode()
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
                result = json.loads(response.read().decode())
                
                # Save to config
                self.player.config.server_url = server_url
                self.player.config.access_code = access_code
                
                return {
                    'success': True,
                    'device_name': result.get('device_name', 'Device'),
                    'device_id': result.get('device_id')
                }
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {'success': False, 'error': 'Invalid access code'}
            elif e.code == 403:
                return {'success': False, 'error': 'Device is disabled'}
            return {'success': False, 'error': f'Server error: {e.code}'}
        except urllib.error.URLError as e:
            return {'success': False, 'error': f'Cannot reach server'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def sync_content(self):
        """Sync content and return playlist"""
        logger.info("sync_content API called")
        try:
            success = self.player.sync_content()
            if success:
                playlist_data = []
                for item in self.player.playlist:
                    # Read file as base64 for display
                    file_data = None
                    if item.local_path.exists():
                        import base64
                        file_data = base64.b64encode(item.local_path.read_bytes()).decode('utf-8')
                        mime_type = 'image/jpeg' if item.file_type == 'image' else 'video/mp4'
                        if item.filename.endswith('.png'):
                            mime_type = 'image/png'
                        elif item.filename.endswith('.gif'):
                            mime_type = 'image/gif'
                        elif item.filename.endswith('.webp'):
                            mime_type = 'image/webp'
                        elif item.filename.endswith('.mp4'):
                            mime_type = 'video/mp4'
                        elif item.filename.endswith('.webm'):
                            mime_type = 'video/webm'
                        file_data = f"data:{mime_type};base64,{file_data}"
                    
                    playlist_data.append({
                        'id': item.id,
                        'name': item.name,
                        'file_type': item.file_type,
                        'display_duration': item.display_duration,
                        '_local_url': file_data  # Now a data URL
                    })
                
                # Also convert default display assets to base64
                default_display = None
                if self.player.default_display:
                    default_display = dict(self.player.default_display)
                    
                    # Convert logo
                    if default_display.get('_local_logo'):
                        logo_path = default_display['_local_logo'].replace('file:///', '').replace('file://', '')
                        # Handle Windows paths
                        if logo_path.startswith('/') and len(logo_path) > 2 and logo_path[2] == ':':
                            logo_path = logo_path[1:]  # Remove leading /
                        logo_path = Path(logo_path.replace('%20', ' '))
                        if logo_path.exists():
                            import base64
                            logo_data = base64.b64encode(logo_path.read_bytes()).decode('utf-8')
                            mime = 'image/png' if str(logo_path).endswith('.png') else 'image/jpeg'
                            default_display['_local_logo'] = f"data:{mime};base64,{logo_data}"
                
                logger.info(f"sync_content returning success with {len(playlist_data)} items")
                return {
                    'success': True,
                    'playlist': playlist_data,
                    'default_display': default_display
                }
            else:
                logger.warning("sync_content: Sync failed")
                return {'success': False, 'error': 'Sync failed'}
        except Exception as e:
            logger.error(f"Sync error: {e}")
            import traceback
            traceback.print_exc()
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
    
    # Create window - frameless for true fullscreen
    window = webview.create_window(
        'Signage Player',
        html=PLAYER_HTML,
        js_api=api,
        width=config.window_width,
        height=config.window_height,
        resizable=True,
        frameless=True,
        easy_drag=False,
        background_color='#000000',
        fullscreen=config.fullscreen
    )
    
    api.set_window(window)
    
    def on_loaded():
        """Called when window is loaded - expose API methods"""
        logger.info("Window loaded, exposing API methods...")
        window.expose(api.get_config)
        window.expose(api.save_config)
        window.expose(api.discover_servers)
        window.expose(api.test_server)
        window.expose(api.register_device)
        window.expose(api.sync_content)
        window.expose(api.toggle_fullscreen)
        window.expose(api.exit_app)
        logger.info("API methods exposed")
        # Trigger JS to retry loading config
        window.evaluate_js('if(typeof retryLoadConfig === "function") retryLoadConfig();')
    
    window.events.loaded += on_loaded
    
    # Start webview
    logger.info("Starting webview")
    webview.start(debug=False)


if __name__ == "__main__":
    main()