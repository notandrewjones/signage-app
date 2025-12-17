#!/usr/bin/env python3
"""
Digital Signage Player
Cross-platform player using pywebview with proper image scaling and orientation support
"""
import os
import sys
import json
import time
import socket
import hashlib
import threading
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
import webview

# Configuration
CONFIG_FILE = Path.home() / ".signage_player" / "config.json"
CACHE_DIR = Path.home() / ".signage_player" / "cache"
DEFAULT_SERVER = "http://localhost:8000"

# Ensure directories exist
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class Config:
    """Player configuration management"""
    def __init__(self):
        self.server_url = DEFAULT_SERVER
        self.access_code = None
        self.device_name = None
        self.fullscreen = True
        self.debug = False
        self.load()
    
    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    data = json.load(f)
                    self.server_url = data.get("server_url", DEFAULT_SERVER)
                    self.access_code = data.get("access_code")
                    self.device_name = data.get("device_name")
                    self.fullscreen = data.get("fullscreen", True)
                    self.debug = data.get("debug", False)
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def save(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump({
                    "server_url": self.server_url,
                    "access_code": self.access_code,
                    "device_name": self.device_name,
                    "fullscreen": self.fullscreen,
                    "debug": self.debug,
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def clear(self):
        self.access_code = None
        self.device_name = None
        self.save()


config = Config()


class PlayerAPI:
    """API exposed to JavaScript in the webview"""
    
    def __init__(self, window):
        self.window = window
        self.playlist = []
        self.current_index = 0
        self.orientation = "landscape"
        self.flip_horizontal = False
        self.flip_vertical = False
        self.running = True
    
    def get_config(self):
        return {
            "server_url": config.server_url,
            "access_code": config.access_code,
            "device_name": config.device_name,
            "is_connected": config.access_code is not None,
        }
    
    def register(self, server_url, access_code):
        """Register with the server using access code"""
        config.server_url = server_url.rstrip("/")
        
        try:
            data = urllib.parse.urlencode({"access_code": access_code}).encode()
            req = urllib.request.Request(
                f"{config.server_url}/api/player/register",
                data=data,
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read())
                if result.get("success"):
                    config.access_code = access_code
                    config.device_name = result.get("device_name")
                    config.save()
                    return {"success": True, "device_name": config.device_name}
                else:
                    return {"success": False, "error": "Registration failed"}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            try:
                error_data = json.loads(error_body)
                return {"success": False, "error": error_data.get("detail", "Invalid access code")}
            except:
                return {"success": False, "error": f"HTTP {e.code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def disconnect(self):
        """Disconnect from server"""
        config.clear()
        self.playlist = []
        return {"success": True}
    
    def get_playlist(self):
        """Fetch current playlist from server"""
        if not config.access_code:
            return {"success": False, "error": "Not connected"}
        
        try:
            req = urllib.request.Request(
                f"{config.server_url}/api/player/{config.access_code}/playlist"
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read())
                self.playlist = result.get("playlist", [])
                
                # Get orientation settings from device config
                device_config = result.get("device", {})
                self.orientation = device_config.get("orientation", "landscape")
                self.flip_horizontal = device_config.get("flip_horizontal", False)
                self.flip_vertical = device_config.get("flip_vertical", False)
                
                return {
                    "success": True,
                    "playlist": self.playlist,
                    "active_schedule": result.get("active_schedule"),
                    "orientation": self.orientation,
                    "flip_horizontal": self.flip_horizontal,
                    "flip_vertical": self.flip_vertical,
                    "debug": result.get("debug"),  # Pass through server debug info
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_default_display(self):
        """Fetch splash screen settings"""
        if not config.access_code:
            return {"success": False, "error": "Not connected"}
        
        try:
            req = urllib.request.Request(
                f"{config.server_url}/api/player/{config.access_code}/config"
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read())
                default_display = result.get("default_display", {})
                
                # Get orientation settings
                device = result.get("device", {})
                
                return {
                    "success": True,
                    "default_display": default_display,
                    "server_url": config.server_url,  # Include server URL for building full paths
                    "orientation": device.get("orientation", "landscape"),
                    "flip_horizontal": device.get("flip_horizontal", False),
                    "flip_vertical": device.get("flip_vertical", False),
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_content_url(self, filename):
        """Get full URL for content file"""
        return f"{config.server_url}/uploads/content/{filename}"
    
    def get_screen_info(self):
        """Get screen dimensions"""
        return {
            "width": self.window.width if hasattr(self.window, 'width') else 1920,
            "height": self.window.height if hasattr(self.window, 'height') else 1080,
        }
    
    def log(self, message):
        """Log message from JavaScript"""
        print(f"[JS] {message}")


def get_player_html():
    """Generate the player HTML with proper image scaling and orientation support"""
    return r'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Digital Signage Player</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: #000;
            color: #fff;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            overflow: hidden;
            width: 100vw;
            height: 100vh;
        }
        
        #player-container {
            width: 100%;
            height: 100%;
            position: relative;
        }
        
        /* Content display - uses object-fit: contain for proper scaling */
        #content-display {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #000;
        }
        
        #content-display img,
        #content-display video {
            max-width: 100%;
            max-height: 100%;
            width: 100%;
            height: 100%;
            object-fit: contain; /* Show full image, touch edges, maintain aspect ratio */
        }
        
        /* Splash screen */
        #splash-screen {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #000;
            z-index: 1;
        }
        
        #splash-screen.position-top {
            align-items: flex-start;
            padding-top: 5%;
        }
        
        #splash-screen.position-bottom {
            align-items: flex-end;
            padding-bottom: 5%;
        }
        
        #splash-logo {
            max-width: 80%;
            max-height: 80%;
            object-fit: contain;
            position: relative;
            z-index: 2;
        }
        
        #splash-background {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            z-index: 0;
        }
        
        /* Setup screen */
        #setup-screen {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            z-index: 1000;
        }
        
        .setup-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 24px;
            padding: 48px;
            max-width: 480px;
            width: 90%;
            text-align: center;
            backdrop-filter: blur(20px);
        }
        
        .setup-card h1 {
            font-size: 28px;
            margin-bottom: 8px;
        }
        
        .setup-card p {
            color: rgba(255,255,255,0.6);
            margin-bottom: 32px;
        }
        
        .form-group {
            margin-bottom: 20px;
            text-align: left;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-size: 14px;
            color: rgba(255,255,255,0.8);
        }
        
        .form-group input {
            width: 100%;
            padding: 16px;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 12px;
            background: rgba(255,255,255,0.05);
            color: #fff;
            font-size: 18px;
            outline: none;
            transition: border-color 0.2s;
        }
        
        .form-group input:focus {
            border-color: #6366f1;
        }
        
        .form-group input::placeholder {
            color: rgba(255,255,255,0.3);
        }
        
        .code-input {
            font-family: monospace;
            font-size: 32px !important;
            text-align: center;
            letter-spacing: 0.3em;
        }
        
        .btn {
            padding: 16px 32px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            width: 100%;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: #fff;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
        }
        
        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .error-message {
            color: #f87171;
            margin-top: 16px;
            font-size: 14px;
        }
        
        .connected-info {
            background: rgba(34, 197, 94, 0.1);
            border: 1px solid rgba(34, 197, 94, 0.3);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 24px;
        }
        
        .connected-info h3 {
            color: #22c55e;
            margin-bottom: 4px;
        }
        
        .btn-secondary {
            background: rgba(255,255,255,0.1);
            color: #fff;
            margin-top: 12px;
        }
        
        .btn-secondary:hover {
            background: rgba(255,255,255,0.2);
        }
        
        /* Loading spinner */
        .spinner {
            width: 48px;
            height: 48px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: #6366f1;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 16px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Status indicator */
        #status-bar {
            position: fixed;
            bottom: 16px;
            right: 16px;
            padding: 8px 16px;
            background: rgba(0,0,0,0.8);
            border-radius: 8px;
            font-size: 12px;
            color: rgba(255,255,255,0.6);
            z-index: 100;
            display: none;
        }
        
        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-online { background: #22c55e; }
        .status-offline { background: #ef4444; }
        
        /* Hidden class */
        .hidden {
            display: none !important;
        }
        
        /* Fade transitions */
        .fade-out {
            opacity: 0;
            transition: opacity 0.5s ease-out;
        }
        
        .fade-in {
            opacity: 1;
            transition: opacity 0.5s ease-in;
        }
    </style>
</head>
<body>
    <div id="player-container">
        <!-- Content Display -->
        <div id="content-display" class="hidden"></div>
        
        <!-- Splash Screen -->
        <div id="splash-screen" class="hidden"></div>
        
        <!-- Setup Screen -->
        <div id="setup-screen">
            <div class="setup-card">
                <h1>Digital Signage</h1>
                <p>Connect this display to your signage server</p>
                
                <div id="connected-panel" class="hidden">
                    <div class="connected-info">
                        <h3>✓ Connected</h3>
                        <p id="device-name-display"></p>
                    </div>
                    <button class="btn btn-primary" onclick="startPlayback()">Start Display</button>
                    <button class="btn btn-secondary" onclick="disconnect()">Disconnect</button>
                </div>
                
                <div id="connect-panel">
                    <div class="form-group">
                        <label>Server URL</label>
                        <input type="text" id="server-url" placeholder="http://192.168.1.100:8000" />
                    </div>
                    
                    <div class="form-group">
                        <label>Access Code</label>
                        <input type="text" id="access-code" class="code-input" maxlength="6" placeholder="000000" />
                    </div>
                    
                    <button class="btn btn-primary" id="connect-btn" onclick="connect()">Connect</button>
                    <p id="error-message" class="error-message hidden"></p>
                </div>
            </div>
        </div>
        
        <!-- Status bar (debug mode) -->
        <div id="status-bar">
            <span class="status-dot status-online"></span>
            <span id="status-text">Connected</span>
        </div>
    </div>
    
    <script>
        // Player state
        let playlist = [];
        let currentIndex = 0;
        let playbackTimer = null;
        let pollTimer = null;
        let orientation = 'landscape';
        let flipHorizontal = false;
        let flipVertical = false;
        let serverUrl = ''; // Will be set from config
        
        // DOM elements
        const setupScreen = document.getElementById('setup-screen');
        const contentDisplay = document.getElementById('content-display');
        const splashScreen = document.getElementById('splash-screen');
        const connectPanel = document.getElementById('connect-panel');
        const connectedPanel = document.getElementById('connected-panel');
        const serverUrlInput = document.getElementById('server-url');
        const accessCodeInput = document.getElementById('access-code');
        const errorMessage = document.getElementById('error-message');
        const deviceNameDisplay = document.getElementById('device-name-display');
        
        // Initialize
        async function init() {
            log('Initializing player...');
            try {
                const config = await pywebview.api.get_config();
                log('Config loaded: ' + JSON.stringify(config));
                
                if (config.server_url) {
                    serverUrlInput.value = config.server_url;
                    serverUrl = config.server_url; // Store for later use
                }
                
                if (config.is_connected && config.access_code) {
                    deviceNameDisplay.textContent = config.device_name || 'Device';
                    connectPanel.classList.add('hidden');
                    connectedPanel.classList.remove('hidden');
                    
                    // Auto-start playback
                    log('Auto-starting playback...');
                    setTimeout(() => startPlayback(), 500);
                } else {
                    log('Not connected, showing setup screen');
                }
            } catch (e) {
                log('Init error: ' + e.message);
                console.error('Init error:', e);
            }
        }
        
        // Connect to server
        async function connect() {
            const serverUrlValue = serverUrlInput.value.trim();
            const accessCode = accessCodeInput.value.trim();
            
            log('Connecting to ' + serverUrlValue + ' with code ' + accessCode);
            
            if (!serverUrlValue || !accessCode) {
                showError('Please enter server URL and access code');
                return;
            }
            
            const btn = document.getElementById('connect-btn');
            btn.disabled = true;
            btn.textContent = 'Connecting...';
            hideError();
            
            try {
                const result = await pywebview.api.register(serverUrlValue, accessCode);
                log('Register result: ' + JSON.stringify(result));
                
                if (result.success) {
                    serverUrl = serverUrlValue; // Store for later use
                    deviceNameDisplay.textContent = result.device_name || 'Device';
                    connectPanel.classList.add('hidden');
                    connectedPanel.classList.remove('hidden');
                } else {
                    showError(result.error || 'Connection failed');
                }
            } catch (e) {
                log('Connect error: ' + e.message);
                showError('Connection error: ' + e.message);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Connect';
            }
        }
        
        // Disconnect
        async function disconnect() {
            try {
                await pywebview.api.disconnect();
                stopPlayback();
                connectedPanel.classList.add('hidden');
                connectPanel.classList.remove('hidden');
                setupScreen.classList.remove('hidden');
                contentDisplay.classList.add('hidden');
                splashScreen.classList.add('hidden');
            } catch (e) {
                console.error('Disconnect error:', e);
            }
        }
        
        // Start playback
        async function startPlayback() {
            log('Starting playback...');
            setupScreen.classList.add('hidden');
            await syncAndPlay();
            startPolling();
        }
        
        // Sync and start playback
        async function syncAndPlay() {
            log('Syncing playlist...');
            try {
                const result = await pywebview.api.get_playlist();
                log('Playlist result: success=' + result.success + ', items=' + (result.playlist?.length || 0));
                
                if (result.success) {
                    playlist = result.playlist || [];
                    orientation = result.orientation || 'landscape';
                    flipHorizontal = result.flip_horizontal || false;
                    flipVertical = result.flip_vertical || false;
                    
                    // Capture debug info from server
                    if (result.debug) {
                        lastDebugInfo = result.debug;
                        log('Server debug: schedules=' + result.debug.total_schedules + ', content=' + result.debug.total_content);
                        if (result.debug.schedule_check_results) {
                            result.debug.schedule_check_results.forEach(s => {
                                if (s.selected) {
                                    log('Active schedule: ' + s.name);
                                }
                            });
                        }
                    }
                    
                    log('Got ' + playlist.length + ' items, orientation: ' + orientation);
                    applyOrientation();
                    
                    if (playlist.length > 0) {
                        log('Showing content');
                        showContent();
                    } else {
                        log('No playlist items, showing splash screen');
                        showSplashScreen();
                    }
                } else {
                    log('Playlist fetch failed: ' + result.error);
                    showSplashScreen();
                }
            } catch (e) {
                log('Sync error: ' + e.message);
                console.error('Sync error:', e);
                showSplashScreen();
            }
        }
        
        // Apply orientation transforms
        function applyOrientation() {
            const container = document.getElementById('player-container');
            let transform = '';
            
            // Note: For portrait mode, the display should already be physically rotated
            // The flip options handle cases where it's rotated the "wrong way"
            
            if (flipHorizontal) {
                transform += 'scaleX(-1) ';
            }
            if (flipVertical) {
                transform += 'scaleY(-1) ';
            }
            
            container.style.transform = transform.trim() || 'none';
        }
        
        // Show content
        function showContent() {
            log('showContent called');
            splashScreen.classList.add('hidden');
            contentDisplay.classList.remove('hidden');
            currentIndex = 0;
            playCurrentItem();
        }
        
        // Play current item
        function playCurrentItem() {
            if (playlist.length === 0) {
                log('Playlist empty, showing splash');
                showSplashScreen();
                return;
            }
            
            const item = playlist[currentIndex];
            // Build full URL - item.url is relative like /uploads/content/...
            const fullUrl = serverUrl + item.url;
            log('Playing item ' + currentIndex + ': ' + item.name + ' (' + item.file_type + ')');
            log('URL: ' + fullUrl);
            contentDisplay.innerHTML = '';
            
            if (item.file_type === 'video') {
                const video = document.createElement('video');
                video.src = fullUrl;
                video.autoplay = true;
                video.muted = false;
                video.playsInline = true;
                video.style.objectFit = 'contain'; // Show full video
                
                video.onloadeddata = () => log('Video loaded: ' + item.name);
                video.onended = () => {
                    log('Video ended: ' + item.name);
                    nextItem();
                };
                video.onerror = (e) => {
                    log('Video error: ' + item.name + ' - ' + (e.message || 'unknown error'));
                    console.error('Video error:', item.name, e);
                    setTimeout(() => nextItem(), 1000);
                };
                
                contentDisplay.appendChild(video);
            } else {
                const img = document.createElement('img');
                img.src = fullUrl;
                img.alt = item.name;
                img.style.objectFit = 'contain'; // Show full image, touch edges
                
                img.onload = () => log('Image loaded: ' + item.name);
                img.onerror = (e) => {
                    log('Image error: ' + item.name + ' - failed to load from ' + fullUrl);
                    console.error('Image error:', item.name);
                    setTimeout(() => nextItem(), 1000);
                };
                
                contentDisplay.appendChild(img);
                
                // Use display_duration for images
                const duration = (item.display_duration || 10) * 1000;
                log('Image will display for ' + duration + 'ms');
                playbackTimer = setTimeout(() => nextItem(), duration);
            }
        }
        
        // Next item
        function nextItem() {
            if (playbackTimer) {
                clearTimeout(playbackTimer);
                playbackTimer = null;
            }
            
            currentIndex = (currentIndex + 1) % playlist.length;
            log('Next item, index now: ' + currentIndex);
            playCurrentItem();
        }
        
        // Show splash screen
        async function showSplashScreen() {
            log('Showing splash screen...');
            contentDisplay.classList.add('hidden');
            
            try {
                const result = await pywebview.api.get_default_display();
                log('Splash screen result: ' + JSON.stringify(result));
                
                if (!result.success || !result.default_display) {
                    log('No splash config, showing black screen');
                    splashScreen.innerHTML = '';
                    splashScreen.style.background = '#000';
                    splashScreen.classList.remove('hidden');
                    return;
                }
                
                const display = result.default_display;
                const serverUrl = result.server_url || '';
                splashScreen.innerHTML = '';
                splashScreen.className = 'position-' + (display.logo_position || 'center');
                
                log('Splash mode: ' + display.background_mode + ', server: ' + serverUrl);
                
                // Background
                if (display.background_mode === 'solid') {
                    splashScreen.style.background = display.background_color || '#000';
                } else if (display.background_mode === 'video' && display.background_video_url) {
                    const videoUrl = serverUrl + display.background_video_url;
                    log('Loading background video: ' + videoUrl);
                    const bgVideo = document.createElement('video');
                    bgVideo.id = 'splash-background';
                    bgVideo.src = videoUrl;
                    bgVideo.autoplay = true;
                    bgVideo.muted = true;
                    bgVideo.loop = true;
                    bgVideo.playsInline = true;
                    bgVideo.onerror = (e) => log('Background video error: ' + e.message);
                    bgVideo.onloadeddata = () => log('Background video loaded');
                    splashScreen.appendChild(bgVideo);
                    splashScreen.style.background = '#000';
                } else if (display.background_mode === 'image' && display.backgrounds?.length > 0) {
                    const imgUrl = serverUrl + display.backgrounds[0].url;
                    log('Loading background image: ' + imgUrl);
                    const bgImg = document.createElement('img');
                    bgImg.id = 'splash-background';
                    bgImg.src = imgUrl;
                    bgImg.onerror = () => log('Background image failed to load');
                    bgImg.onload = () => log('Background image loaded');
                    splashScreen.appendChild(bgImg);
                    splashScreen.style.background = '#000';
                } else if (display.background_mode === 'slideshow' && display.backgrounds?.length > 0) {
                    const imgUrl = serverUrl + display.backgrounds[0].url;
                    const bgImg = document.createElement('img');
                    bgImg.id = 'splash-background';
                    bgImg.src = imgUrl;
                    splashScreen.appendChild(bgImg);
                    splashScreen.style.background = '#000';
                } else {
                    splashScreen.style.background = display.background_color || '#000';
                }
                
                // Logo
                if (display.logo_url) {
                    const logoUrl = serverUrl + display.logo_url;
                    log('Loading logo: ' + logoUrl);
                    const logo = document.createElement('img');
                    logo.id = 'splash-logo';
                    logo.src = logoUrl;
                    logo.style.maxWidth = (display.logo_scale * 100) + '%';
                    logo.style.maxHeight = (display.logo_scale * 80) + '%';
                    logo.onerror = () => log('Logo failed to load');
                    logo.onload = () => log('Logo loaded successfully');
                    splashScreen.appendChild(logo);
                }
                
                splashScreen.classList.remove('hidden');
                log('Splash screen displayed');
                
            } catch (e) {
                log('Splash screen error: ' + e.message);
                console.error('Splash screen error:', e);
                splashScreen.innerHTML = '';
                splashScreen.style.background = '#000';
                splashScreen.classList.remove('hidden');
            }
        }
        
        // Stop playback
        function stopPlayback() {
            if (playbackTimer) {
                clearTimeout(playbackTimer);
                playbackTimer = null;
            }
            stopPolling();
        }
        
        // Polling for updates
        function startPolling() {
            pollTimer = setInterval(async () => {
                try {
                    const result = await pywebview.api.get_playlist();
                    
                    if (result.success) {
                        const newPlaylist = result.playlist || [];
                        const playlistChanged = JSON.stringify(newPlaylist.map(i => i.id)) !== 
                                                JSON.stringify(playlist.map(i => i.id));
                        
                        // Check for orientation changes
                        const orientationChanged = 
                            orientation !== result.orientation ||
                            flipHorizontal !== result.flip_horizontal ||
                            flipVertical !== result.flip_vertical;
                        
                        if (orientationChanged) {
                            orientation = result.orientation || 'landscape';
                            flipHorizontal = result.flip_horizontal || false;
                            flipVertical = result.flip_vertical || false;
                            applyOrientation();
                        }
                        
                        if (playlistChanged) {
                            playlist = newPlaylist;
                            if (playlist.length > 0) {
                                currentIndex = 0;
                                showContent();
                            } else {
                                showSplashScreen();
                            }
                        }
                    }
                } catch (e) {
                    console.error('Poll error:', e);
                }
            }, 30000); // Poll every 30 seconds
        }
        
        function stopPolling() {
            if (pollTimer) {
                clearInterval(pollTimer);
                pollTimer = null;
            }
        }
        
        // Error handling
        function showError(message) {
            errorMessage.textContent = message;
            errorMessage.classList.remove('hidden');
        }
        
        function hideError() {
            errorMessage.classList.add('hidden');
        }
        
        // Debug logging
        let debugMode = false;
        const debugLog = [];
        let lastDebugInfo = null;
        
        function log(msg) {
            const timestamp = new Date().toLocaleTimeString();
            const entry = `[${timestamp}] ${msg}`;
            debugLog.push(entry);
            if (debugLog.length > 50) debugLog.shift();
            console.log(entry);
            if (debugMode) updateDebugOverlay();
            try { pywebview.api.log(msg); } catch(e) {}
        }
        
        function updateDebugOverlay() {
            let overlay = document.getElementById('debug-overlay');
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.id = 'debug-overlay';
                overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.95);color:#0f0;font-family:monospace;font-size:12px;padding:20px;overflow:auto;z-index:9999;white-space:pre-wrap;';
                document.body.appendChild(overlay);
            }
            
            let debugInfoStr = 'No debug info yet';
            if (lastDebugInfo) {
                debugInfoStr = `Server Time: ${lastDebugInfo.current_time}
Day of Week: ${lastDebugInfo.current_day} (0=Mon, 6=Sun)
Has Schedule Group: ${lastDebugInfo.has_schedule_group}
Schedule Group Active: ${lastDebugInfo.schedule_group_active}
Total Schedules: ${lastDebugInfo.total_schedules}
Total Content Items: ${lastDebugInfo.total_content}
Fallback Mode: ${lastDebugInfo.fallback_mode || false}

Schedule Checks:
${(lastDebugInfo.schedule_check_results || []).map(s => 
    `  - ${s.name}: ${s.start}-${s.end} days=${s.days} active=${s.is_active} day_match=${s.day_match} time_match=${s.time_match} SELECTED=${s.selected}`
).join('\n') || '  (none)'}`;
            }
            
            overlay.innerHTML = `<h2 style="color:#0f0;margin-bottom:10px;">DEBUG MODE</h2>
<div style="color:#888;margin-bottom:10px;">Keys: D=close debug, R=refresh, S=setup screen, ESC=toggle fullscreen</div>

<b style="color:#ff0;">Playlist:</b> ${playlist.length} items
<b style="color:#ff0;">Current Index:</b> ${currentIndex}
<b style="color:#ff0;">Orientation:</b> ${orientation} (flip H:${flipHorizontal} V:${flipVertical})

<b style="color:#0ff;">Current Item:</b>
${playlist[currentIndex] ? JSON.stringify(playlist[currentIndex], null, 2) : 'None - showing splash screen'}

<b style="color:#f0f;">Server Debug Info:</b>
${debugInfoStr}

<b style="color:#aaa;">Log (last 20):</b>
${debugLog.slice(-20).join('\n')}`; 
        }
        
        function hideDebugOverlay() {
            const overlay = document.getElementById('debug-overlay');
            if (overlay) overlay.remove();
        }
        
        // Keyboard handler
        document.addEventListener('keydown', (e) => {
            // D = Toggle debug overlay
            if (e.key === 'd' || e.key === 'D') {
                debugMode = !debugMode;
                if (debugMode) {
                    updateDebugOverlay();
                } else {
                    hideDebugOverlay();
                }
            }
            // R = Refresh playlist
            if (e.key === 'r' || e.key === 'R') {
                log('Manual refresh triggered');
                syncAndPlay();
            }
            // S = Show setup screen
            if (e.key === 's' || e.key === 'S') {
                log('Showing setup screen');
                setupScreen.classList.remove('hidden');
                contentDisplay.classList.add('hidden');
                splashScreen.classList.add('hidden');
            }
            // Escape - handled by pywebview for fullscreen toggle
        });
        
        // Auto-uppercase access code
        accessCodeInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/\D/g, '').slice(0, 6);
        });
        
        // Enter key to connect
        accessCodeInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                connect();
            }
        });
        
        // Wait for pywebview API
        window.addEventListener('pywebviewready', init);
        
        // Fallback init
        setTimeout(() => {
            if (typeof pywebview !== 'undefined') {
                init();
            }
        }, 1000);
    </script>
</body>
</html>
'''


def main():
    """Main entry point"""
    api = None
    
    def on_loaded():
        """Called when webview is loaded"""
        pass
    
    # Create window - starts in fullscreen based on config
    window = webview.create_window(
        title="Digital Signage Player",
        html=get_player_html(),
        width=1280,
        height=720,
        fullscreen=config.fullscreen,
        frameless=False,
        easy_drag=False,
        background_color="#000000",
    )
    
    # Create API instance
    api = PlayerAPI(window)
    
    # Expose individual API methods to JavaScript
    window.expose(
        api.get_config,
        api.register,
        api.disconnect,
        api.get_playlist,
        api.get_default_display,
        api.get_content_url,
        api.get_screen_info,
        api.log,
    )
    
    # Start webview
    webview.start(
        on_loaded,
        debug=config.debug,
        private_mode=False,
    )


if __name__ == "__main__":
    main()