#!/usr/bin/env python3
"""
Digital Signage Player
Cross-platform player with local content caching and synchronized playback
"""
import os
import sys
import json
import time
import hashlib
import threading
import urllib.request
import urllib.error
import urllib.parse
import mimetypes
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webview

# Configuration - store data in ./data folder next to player.py
PLAYER_DIR = Path(__file__).parent
DATA_DIR = PLAYER_DIR / "data"
CONFIG_FILE = DATA_DIR / "config.json"
CACHE_DIR = DATA_DIR / "cache"
CONTENT_DIR = CACHE_DIR / "content"
SPLASH_DIR = CACHE_DIR / "splash"
DEFAULT_SERVER = "http://localhost:8000"
LOCAL_SERVER_PORT = 8089  # Local cache server port

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CONTENT_DIR.mkdir(parents=True, exist_ok=True)
SPLASH_DIR.mkdir(parents=True, exist_ok=True)


class CacheHTTPHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves files from the cache directory"""
    
    def __init__(self, *args, **kwargs):
        # Set the directory to serve from
        super().__init__(*args, directory=str(CACHE_DIR), **kwargs)
    
    def log_message(self, format, *args):
        # Suppress logging to keep console clean
        pass
    
    def end_headers(self):
        # Add CORS headers for local access
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()


def start_local_server():
    """Start local HTTP server in background thread"""
    try:
        server = HTTPServer(('127.0.0.1', LOCAL_SERVER_PORT), CacheHTTPHandler)
        print(f"Local cache server running on http://127.0.0.1:{LOCAL_SERVER_PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"Failed to start local server: {e}")


# Start local server in background
local_server_thread = threading.Thread(target=start_local_server, daemon=True)
local_server_thread.start()


class Config:
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


class ContentSyncManager:
    def __init__(self):
        self.manifest = {}
        self.sync_in_progress = False
        self.sync_progress = 0
        self.sync_total = 0
        self.sync_status = "idle"
        self.load_manifest()
    
    def load_manifest(self):
        manifest_file = CACHE_DIR / "manifest.json"
        if manifest_file.exists():
            try:
                with open(manifest_file) as f:
                    self.manifest = json.load(f)
            except:
                self.manifest = {}
    
    def save_manifest(self):
        manifest_file = CACHE_DIR / "manifest.json"
        try:
            with open(manifest_file, "w") as f:
                json.dump(self.manifest, f, indent=2)
        except Exception as e:
            print(f"Error saving manifest: {e}")
    
    def is_cached(self, filename, expected_size=None):
        if filename not in self.manifest:
            return False
        local_path = Path(self.manifest[filename].get("local_path", ""))
        if not local_path.exists():
            return False
        if expected_size and local_path.stat().st_size != expected_size:
            return False
        return True
    
    def get_local_path(self, filename):
        if filename in self.manifest:
            local_path = Path(self.manifest[filename].get("local_path", ""))
            if local_path.exists():
                return str(local_path)
        return None
    
    def download_file(self, url, filename, file_size=None, content_type="content"):
        try:
            target_dir = SPLASH_DIR if content_type == "splash" else CONTENT_DIR
            local_path = target_dir / filename
            print(f"Downloading: {filename}")
            urllib.request.urlretrieve(url, local_path)
            self.manifest[filename] = {
                "local_path": str(local_path),
                "url": url,
                "size": local_path.stat().st_size,
                "synced_at": datetime.now().isoformat(),
            }
            self.save_manifest()
            return str(local_path)
        except Exception as e:
            print(f"Download error for {filename}: {e}")
            return None
    
    def sync_playlist(self, playlist, server_url, progress_callback=None):
        self.sync_in_progress = True
        self.sync_total = len(playlist)
        self.sync_progress = 0
        self.sync_status = "syncing"
        synced_files = []
        
        for i, item in enumerate(playlist):
            self.sync_progress = i + 1
            filename = item.get("filename")
            file_size = item.get("file_size")
            relative_url = item.get("url", "")
            
            if self.is_cached(filename, file_size):
                print(f"Already cached: {filename}")
                synced_files.append(filename)
                continue
            
            full_url = server_url + relative_url
            local_path = self.download_file(full_url, filename, file_size, "content")
            if local_path:
                synced_files.append(filename)
        
        self.cleanup_unused(synced_files, CONTENT_DIR)
        self.sync_in_progress = False
        self.sync_status = "complete"
        return synced_files
    
    def sync_splash_content(self, splash_config, server_url):
        if not splash_config:
            return
        if splash_config.get("logo_filename"):
            filename = splash_config["logo_filename"]
            if not self.is_cached(filename):
                url = server_url + splash_config.get("logo_url", "")
                self.download_file(url, filename, None, "splash")
        if splash_config.get("background_video_filename"):
            filename = splash_config["background_video_filename"]
            if not self.is_cached(filename):
                url = server_url + splash_config.get("background_video_url", "")
                self.download_file(url, filename, None, "splash")
        for bg in splash_config.get("backgrounds", []):
            filename = bg.get("filename")
            if filename and not self.is_cached(filename):
                url = server_url + bg.get("url", "")
                self.download_file(url, filename, None, "splash")
    
    def cleanup_unused(self, keep_files, directory):
        try:
            for file in directory.iterdir():
                if file.is_file() and file.name not in keep_files:
                    print(f"Removing unused: {file.name}")
                    file.unlink()
                    if file.name in self.manifest:
                        del self.manifest[file.name]
            self.save_manifest()
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def get_sync_status(self):
        return {
            "in_progress": self.sync_in_progress,
            "progress": self.sync_progress,
            "total": self.sync_total,
            "status": self.sync_status,
        }


sync_manager = ContentSyncManager()


class PlayerAPI:
    def __init__(self, window):
        self.window = window
        self.playlist = []
        self.orientation = "landscape"
        self.flip_horizontal = False
        self.flip_vertical = False
    
    def get_config(self):
        return {
            "server_url": config.server_url,
            "access_code": config.access_code,
            "device_name": config.device_name,
            "is_connected": config.access_code is not None,
        }
    
    def register(self, server_url, access_code):
        config.server_url = server_url.rstrip("/")
        try:
            data = urllib.parse.urlencode({"access_code": access_code}).encode()
            req = urllib.request.Request(f"{config.server_url}/api/player/register", data=data, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read())
                if result.get("success"):
                    config.access_code = access_code
                    config.device_name = result.get("device_name")
                    config.save()
                    return {"success": True, "device_name": config.device_name}
                return {"success": False, "error": "Registration failed"}
        except urllib.error.HTTPError as e:
            try:
                error_data = json.loads(e.read().decode())
                return {"success": False, "error": error_data.get("detail", "Invalid access code")}
            except:
                return {"success": False, "error": f"HTTP {e.code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def disconnect(self):
        config.clear()
        self.playlist = []
        return {"success": True}
    
    def get_playlist(self):
        if not config.access_code:
            return {"success": False, "error": "Not connected"}
        try:
            req = urllib.request.Request(f"{config.server_url}/api/player/{config.access_code}/playlist")
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read())
                self.playlist = result.get("playlist", [])
                device_config = result.get("device", {})
                self.orientation = device_config.get("orientation", "landscape")
                self.flip_horizontal = device_config.get("flip_horizontal", False)
                self.flip_vertical = device_config.get("flip_vertical", False)
                
                # Get transition settings
                transition = result.get("transition", {})
                transition_type = transition.get("type", "cut")
                transition_duration = transition.get("duration", 0.5)
                
                # Get sync settings
                sync_info = result.get("sync", {})
                
                if self.playlist:
                    threading.Thread(target=sync_manager.sync_playlist, args=(self.playlist, config.server_url), daemon=True).start()
                
                local_playlist = []
                for item in self.playlist:
                    local_item = item.copy()
                    local_path = sync_manager.get_local_path(item.get("filename"))
                    if local_path:
                        local_item["local_path"] = local_path
                        local_item["use_local"] = True
                    else:
                        local_item["use_local"] = False
                        local_item["remote_url"] = config.server_url + item.get("url", "")
                    local_playlist.append(local_item)
                
                return {
                    "success": True,
                    "playlist": local_playlist,
                    "active_schedule": result.get("active_schedule"),
                    "orientation": self.orientation,
                    "flip_horizontal": self.flip_horizontal,
                    "flip_vertical": self.flip_vertical,
                    "transition_type": transition_type,
                    "transition_duration": transition_duration,
                    "sync": sync_info,  # Pass sync info to JS
                    "debug": result.get("debug"),
                    "server_url": config.server_url,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_default_display(self):
        if not config.access_code:
            return {"success": False, "error": "Not connected"}
        try:
            req = urllib.request.Request(f"{config.server_url}/api/player/{config.access_code}/config")
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read())
                default_display = result.get("default_display", {})
                
                if default_display:
                    threading.Thread(target=sync_manager.sync_splash_content, args=(default_display, config.server_url), daemon=True).start()
                    if default_display.get("logo_filename"):
                        default_display["logo_local_path"] = sync_manager.get_local_path(default_display["logo_filename"])
                    if default_display.get("background_video_filename"):
                        default_display["background_video_local_path"] = sync_manager.get_local_path(default_display["background_video_filename"])
                    for bg in default_display.get("backgrounds", []):
                        bg["local_path"] = sync_manager.get_local_path(bg.get("filename"))
                
                device = result.get("device", {})
                return {
                    "success": True,
                    "default_display": default_display,
                    "server_url": config.server_url,
                    "orientation": device.get("orientation", "landscape"),
                    "flip_horizontal": device.get("flip_horizontal", False),
                    "flip_vertical": device.get("flip_vertical", False),
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_sync_status(self):
        return sync_manager.get_sync_status()
    
    def get_local_file_url(self, filename):
        local_path = sync_manager.get_local_path(filename)
        if local_path:
            return "file:///" + local_path.replace("\\", "/")
        return None
    
    def get_content_url(self, filename):
        local_path = sync_manager.get_local_path(filename)
        if local_path:
            return "file:///" + local_path.replace("\\", "/")
        return f"{config.server_url}/uploads/content/{filename}"
    
    def get_screen_info(self):
        return {"width": 1920, "height": 1080}
    
    def time_sync(self):
        """NTP-style time synchronization - returns server time and round-trip info"""
        if not config.access_code:
            return {"success": False, "error": "Not connected"}
        try:
            client_send_time = time.time()
            req = urllib.request.Request(f"{config.server_url}/api/time")
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read())
                return {
                    "success": True,
                    "server_time": result.get("time"),
                    "client_send_time": client_send_time,
                }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def log(self, message):
        print(f"[JS] {message}")


def get_player_html():
    """Return the HTML/JS for the synchronized player"""
    return r'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Digital Signage</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#000;color:#fff;font-family:system-ui;overflow:hidden;width:100vw;height:100vh}
#player-container{width:100%;height:100%;position:relative}
#content-display{position:absolute;inset:0;background:#000;z-index:1}
.content-layer{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;opacity:0;z-index:1;transition:opacity 0s}
.content-layer.active{opacity:1}
.content-layer img,.content-layer video{max-width:100%;max-height:100%;width:100%;height:100%;object-fit:contain}
#splash-screen{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:#000;z-index:3}
#splash-screen.position-top{align-items:flex-start;padding-top:5%}
#splash-screen.position-bottom{align-items:flex-end;padding-bottom:5%}
#splash-logo{max-width:80%;max-height:80%;object-fit:contain;position:relative;z-index:2}
#splash-background{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:0}
#setup-screen{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#1a1a2e,#16213e);z-index:1000}
.setup-card{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:24px;padding:48px;max-width:480px;width:90%;text-align:center}
.setup-card h1{font-size:28px;margin-bottom:8px}
.setup-card p{color:rgba(255,255,255,0.6);margin-bottom:32px}
.form-group{margin-bottom:20px;text-align:left}
.form-group label{display:block;margin-bottom:8px;font-size:14px;color:rgba(255,255,255,0.8)}
.form-group input{width:100%;padding:16px;border:1px solid rgba(255,255,255,0.2);border-radius:12px;background:rgba(255,255,255,0.05);color:#fff;font-size:18px;outline:none}
.form-group input:focus{border-color:#6366f1}
.code-input{font-family:monospace;font-size:32px!important;text-align:center;letter-spacing:0.3em}
.btn{padding:16px 32px;border:none;border-radius:12px;font-size:16px;font-weight:600;cursor:pointer;width:100%}
.btn-primary{background:linear-gradient(135deg,#6366f1,#8b5cf6);color:#fff}
.btn-primary:disabled{opacity:0.5}
.btn-secondary{background:rgba(255,255,255,0.1);color:#fff;margin-top:12px}
.connected-info{background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);border-radius:12px;padding:16px;margin-bottom:24px}
.connected-info h3{color:#22c55e;margin-bottom:4px}
.error-message{color:#f87171;margin-top:16px;font-size:14px}
.hidden{display:none!important}
#sync-indicator{position:fixed;top:10px;right:10px;padding:8px 16px;background:rgba(0,0,0,0.7);border-radius:8px;font-size:12px;font-family:monospace;z-index:100;display:none}
#sync-indicator.synced{border:1px solid #22c55e;color:#22c55e}
#sync-indicator.syncing{border:1px solid #f59e0b;color:#f59e0b}
</style></head>
<body>
<div id="player-container">
<div id="content-display" class="hidden">
  <div id="content-layer-0" class="content-layer"></div>
  <div id="content-layer-1" class="content-layer"></div>
</div>
<div id="splash-screen" class="hidden"></div>
<div id="setup-screen">
  <div class="setup-card">
    <h1>Digital Signage</h1>
    <p>Connect to your signage server</p>
    <div id="connected-panel" class="hidden">
      <div class="connected-info"><h3>✓ Connected</h3><p id="device-name-display"></p></div>
      <button class="btn btn-primary" onclick="startPlayback()">Start Display</button>
      <button class="btn btn-secondary" onclick="disconnect()">Disconnect</button>
    </div>
    <div id="connect-panel">
      <div class="form-group"><label>Server URL</label><input type="text" id="server-url" placeholder="http://192.168.1.100:8000"/></div>
      <div class="form-group"><label>Access Code</label><input type="text" id="access-code" class="code-input" maxlength="6" placeholder="000000"/></div>
      <button class="btn btn-primary" id="connect-btn" onclick="connect()">Connect</button>
      <p id="error-message" class="error-message hidden"></p>
    </div>
  </div>
</div>
<div id="sync-indicator"></div>
</div>

<script>
// ============================================================
// SYNCHRONIZED PLAYBACK SYSTEM
// All devices calculate position based on elapsed time since sync_start_time
// ============================================================

let playlist = [], currentIndex = 0, activeLayer = 0;
let playbackTimer = null, pollTimer = null, syncCheckInterval = null;
let serverUrl = '';

// Sync timing variables
let syncStartTime = 0;        // Unix timestamp when playlist cycle started
let totalCycleDuration = 0;   // Total duration of one playlist cycle
let serverTimeOffset = 0;     // Difference between server clock and local clock

// Display settings
let orientation = 'landscape', flipH = false, flipV = false;
let transitionType = 'cut', transitionDuration = 0.5;
let debugMode = false, debugLog = [];

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
const contentLayers = [document.getElementById('content-layer-0'), document.getElementById('content-layer-1')];
const syncIndicator = document.getElementById('sync-indicator');
const LOCAL_CACHE_URL = 'http://127.0.0.1:8089';

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function log(m) {
    const entry = `[${new Date().toLocaleTimeString()}] ${m}`;
    debugLog.push(entry);
    if (debugLog.length > 100) debugLog.shift();
    console.log(entry);
    if (debugMode) updateDebug();
    try { pywebview.api.log(m); } catch(e) {}
}

function updateSyncIndicator(status, info = '') {
    syncIndicator.style.display = debugMode ? 'block' : 'none';
    syncIndicator.className = status;
    syncIndicator.textContent = info;
}

function applyTransitionStyle() {
    const dur = transitionType === 'cut' ? 0 : transitionDuration;
    contentLayers.forEach(l => { l.style.transition = `opacity ${dur}s ease-in-out`; });
}

function applyOrientation() {
    const c = document.getElementById('player-container');
    let t = '';
    if (flipH) t += 'scaleX(-1) ';
    if (flipV) t += 'scaleY(-1) ';
    c.style.transform = t || 'none';
}

function getUrl(item) {
    if (item.use_local && item.filename) {
        return `${LOCAL_CACHE_URL}/content/${item.filename}`;
    }
    if (item.remote_url) return item.remote_url;
    return serverUrl + item.url;
}

// ============================================================
// DIRECT HTTP TIME SYNCHRONIZATION
// Simplified: just verify clocks are close, use local time
// ============================================================

async function performTimeSync() {
    log('Checking time sync with server...');
    
    try {
        const localBefore = Date.now() / 1000;
        
        const response = await fetch(serverUrl + '/api/time', {
            method: 'GET',
            cache: 'no-store'
        });
        
        const localAfter = Date.now() / 1000;
        const data = await response.json();
        const serverTime = data.time;
        
        // Calculate approximate offset (for display/debugging only)
        const roundTrip = localAfter - localBefore;
        const localMidpoint = (localBefore + localAfter) / 2;
        const offset = serverTime - localMidpoint;
        
        log(`Server time: ${serverTime.toFixed(3)}, Local: ${localMidpoint.toFixed(3)}, Offset: ${(offset*1000).toFixed(0)}ms, RTT: ${(roundTrip*1000).toFixed(0)}ms`);
        
        // Warn if clocks are way off
        if (Math.abs(offset) > 1) {
            log(`WARNING: Device clock is ${offset.toFixed(1)}s off from server!`);
        }
        
        return offset;
        
    } catch (e) {
        log(`Time sync failed: ${e.message}`);
        return 0;
    }
}

// Get current time for sync calculations
// Use LOCAL time directly - both devices should have accurate system clocks
function getServerTime() {
    return Date.now() / 1000;
}

// Start periodic time check (just for monitoring, not used for sync)
let timeSyncInterval = null;
function startTimeSyncLoop() {
    if (timeSyncInterval) clearInterval(timeSyncInterval);
    timeSyncInterval = setInterval(async () => {
        await performTimeSync();  // Just log, don't use the offset
    }, 60000);  // Check every 60 seconds
}

function stopTimeSyncLoop() {
    if (timeSyncInterval) {
        clearInterval(timeSyncInterval);
        timeSyncInterval = null;
    }
}

// ============================================================
// SYNC CALCULATION FUNCTIONS
// ============================================================

// Calculate when each item starts within the playlist cycle
function calculateItemStartTimes() {
    let cumulative = 0;
    playlist.forEach((item, i) => {
        item._startTime = cumulative;
        const duration = getItemDuration(item);
        item._duration = duration;
        cumulative += duration;
        item._endTime = cumulative;
        log(`Item ${i}: "${item.name}" ${item._startTime.toFixed(1)}s-${item._endTime.toFixed(1)}s (${duration}s)`);
    });
}

// Get effective duration of a playlist item
function getItemDuration(item) {
    if (item.file_type === 'video') {
        return item.duration || item.display_duration || 10;
    }
    return item.display_duration || 10;
}

// Get current position within the playlist cycle
function getCurrentCyclePosition() {
    const now = getServerTime();
    const elapsed = now - syncStartTime;
    const position = elapsed % totalCycleDuration;
    // Handle edge case where position might be negative due to timing
    return position < 0 ? position + totalCycleDuration : position;
}

// Find which item should be playing at a given position
function getItemAtPosition(position) {
    for (let i = 0; i < playlist.length; i++) {
        if (position >= playlist[i]._startTime && position < playlist[i]._endTime) {
            return { 
                index: i, 
                elapsed: position - playlist[i]._startTime,
                remaining: playlist[i]._endTime - position
            };
        }
    }
    // Default to first item if position doesn't match any (shouldn't happen)
    return { index: 0, elapsed: 0, remaining: playlist[0]?._duration || 10 };
}

// ============================================================
// INITIALIZATION & CONNECTION
// ============================================================

async function init() {
    log('Initializing...');
    try {
        const c = await pywebview.api.get_config();
        if (c.server_url) {
            serverUrlInput.value = c.server_url;
            serverUrl = c.server_url;
        }
        if (c.is_connected) {
            deviceNameDisplay.textContent = c.device_name || 'Device';
            connectPanel.classList.add('hidden');
            connectedPanel.classList.remove('hidden');
            setTimeout(() => startPlayback(), 500);
        }
    } catch (e) {
        log('Init error: ' + e.message);
    }
}

async function connect() {
    const url = serverUrlInput.value.trim();
    const code = accessCodeInput.value.trim();
    if (!url || !code) { showError('Enter server URL and code'); return; }
    
    const btn = document.getElementById('connect-btn');
    btn.disabled = true;
    btn.textContent = 'Connecting...';
    hideError();
    
    try {
        const r = await pywebview.api.register(url, code);
        if (r.success) {
            serverUrl = url;
            deviceNameDisplay.textContent = r.device_name || 'Device';
            connectPanel.classList.add('hidden');
            connectedPanel.classList.remove('hidden');
        } else {
            showError(r.error || 'Connection failed');
        }
    } catch (e) {
        showError('Error: ' + e.message);
    }
    btn.disabled = false;
    btn.textContent = 'Connect';
}

async function disconnect() {
    await pywebview.api.disconnect();
    stopPlayback();
    connectedPanel.classList.add('hidden');
    connectPanel.classList.remove('hidden');
    setupScreen.classList.remove('hidden');
    contentDisplay.classList.add('hidden');
    splashScreen.classList.add('hidden');
}

// ============================================================
// SYNCHRONIZED PLAYBACK
// ============================================================

async function startPlayback() {
    log('Starting playback...');
    setupScreen.classList.add('hidden');
    await syncAndPlay();
    startPolling();
}

async function syncAndPlay() {
    log('Fetching playlist with sync info...');
    updateSyncIndicator('syncing', 'Syncing...');
    
    try {
        // Check time sync (for debugging only - we use local time directly)
        await performTimeSync();
        
        const r = await pywebview.api.get_playlist();
        
        if (!r.success) {
            log('Playlist fetch failed');
            showSplash();
            return;
        }
        
        playlist = r.playlist || [];
        serverUrl = r.server_url || serverUrl;
        orientation = r.orientation || 'landscape';
        flipH = r.flip_horizontal || false;
        flipV = r.flip_vertical || false;
        transitionType = r.transition_type || 'cut';
        transitionDuration = r.transition_duration || 0.5;
        
        // Extract sync timing info - syncStartTime is the key!
        // Both devices get the SAME syncStartTime from the server
        if (r.sync) {
            syncStartTime = r.sync.start_time || 0;
            totalCycleDuration = r.sync.total_duration || 0;
            log(`Sync info: syncStartTime=${syncStartTime.toFixed(3)}, cycle=${totalCycleDuration.toFixed(1)}s`);
            log(`Local time: ${(Date.now()/1000).toFixed(3)}, elapsed since sync: ${((Date.now()/1000) - syncStartTime).toFixed(1)}s`);
        }
        
        applyOrientation();
        applyTransitionStyle();
        
        const cached = playlist.filter(i => i.use_local).length;
        log(`Playlist: ${playlist.length} items (${cached} cached)`);
        
        if (playlist.length > 0 && totalCycleDuration > 0) {
            calculateItemStartTimes();
            await startSyncedPlayback();
        } else if (playlist.length > 0) {
            log('No sync info - falling back to sequential playback');
            // Calculate duration manually
            totalCycleDuration = playlist.reduce((sum, item) => sum + getItemDuration(item), 0);
            syncStartTime = Date.now() / 1000;
            calculateItemStartTimes();
            await startSyncedPlayback();
        } else {
            showSplash();
        }
    } catch (e) {
        log('Sync error: ' + e.message);
        showSplash();
    }
}

async function startSyncedPlayback() {
    log('Starting synchronized playback');
    splashScreen.classList.add('hidden');
    contentDisplay.classList.remove('hidden');
    
    // Start periodic time resync to maintain accuracy
    startTimeSyncLoop();
    
    // Calculate current position in the cycle
    const position = getCurrentCyclePosition();
    const { index, elapsed, remaining } = getItemAtPosition(position);
    
    log(`Cycle position: ${position.toFixed(2)}s -> Item ${index} "${playlist[index]?.name}" (${elapsed.toFixed(1)}s elapsed, ${remaining.toFixed(1)}s remaining)`);
    updateSyncIndicator('synced', `Item ${index+1}/${playlist.length}`);
    
    currentIndex = index;
    activeLayer = 0;
    
    // Preload current and next items
    await preload(currentIndex, 0);
    const nextIndex = (currentIndex + 1) % playlist.length;
    preload(nextIndex, 1);
    
    // Show current item, seeking if needed
    showSyncedItem(elapsed);
    
    // Start sync monitoring
    startSyncLoop();
}

async function preload(idx, layer) {
    if (idx >= playlist.length) return;
    const item = playlist[idx];
    const url = getUrl(item);
    const el = contentLayers[layer];
    
    el.innerHTML = '';
    
    return new Promise(resolve => {
        if (item.file_type === 'video') {
            const v = document.createElement('video');
            v.src = url;
            v.preload = 'auto';
            v.playsInline = true;
            v.muted = false;
            v.style.objectFit = 'contain';
            v.onloadeddata = () => resolve();
            v.onerror = () => { log('Video load error: ' + url); resolve(); };
            el.appendChild(v);
        } else {
            const img = document.createElement('img');
            img.src = url;
            img.style.objectFit = 'contain';
            img.onload = () => resolve();
            img.onerror = () => { log('Image load error: ' + url); resolve(); };
            el.appendChild(img);
        }
    });
}

function showSyncedItem(elapsedInItem) {
    const currentLayer = contentLayers[activeLayer];
    const otherLayer = contentLayers[1 - activeLayer];
    
    // Show current layer
    currentLayer.style.zIndex = '2';
    currentLayer.classList.add('active');
    otherLayer.style.zIndex = '1';
    otherLayer.classList.remove('active');
    
    const item = playlist[currentIndex];
    const video = currentLayer.querySelector('video');
    
    if (video && item.file_type === 'video') {
        // Seek video to correct position and play
        video.currentTime = elapsedInItem;
        video.play().catch(e => log('Video play error: ' + e.message));
        log(`Video "${item.name}" seek to ${elapsedInItem.toFixed(2)}s`);
    }
    
    scheduleNextTransition();
}

// Use a single requestAnimationFrame loop for precise timing
let transitionTargetTime = 0;
let rafId = null;

function scheduleNextTransition() {
    const item = playlist[currentIndex];
    const now = getServerTime();
    
    // Calculate elapsed time since sync started
    const elapsed = now - syncStartTime;
    
    // Calculate current position within the cycle
    const cyclePosition = elapsed % totalCycleDuration;
    
    // Calculate the current cycle number
    const cycleNumber = Math.floor(elapsed / totalCycleDuration);
    
    // Calculate when this cycle started
    const cycleStartTime = syncStartTime + (cycleNumber * totalCycleDuration);
    
    // The item ends at cycleStartTime + item._endTime
    let targetTime = cycleStartTime + item._endTime;
    
    // If we're past this item's end time in the current cycle,
    // we need to target the NEXT cycle's occurrence
    if (targetTime <= now) {
        targetTime += totalCycleDuration;
        log(`Cycle boundary: targeting next cycle`);
    }
    
    transitionTargetTime = targetTime;
    
    const timeUntilTransition = transitionTargetTime - now;
    
    log(`Item ${currentIndex} ends at ${item._endTime.toFixed(1)}s in cycle. Target: ${transitionTargetTime.toFixed(3)}, in ${(timeUntilTransition*1000).toFixed(0)}ms`);
    
    // Start the animation frame loop if not already running
    if (!rafId) {
        rafId = requestAnimationFrame(transitionLoop);
    }
}

function transitionLoop(timestamp) {
    const now = getServerTime();
    const remaining = transitionTargetTime - now;
    
    if (remaining <= 0.008) {  // Within 8ms (half a frame) - fire now
        rafId = null;
        doSyncedTransition();
    } else {
        // Keep looping
        rafId = requestAnimationFrame(transitionLoop);
    }
}

function stopTransitionLoop() {
    if (rafId) {
        cancelAnimationFrame(rafId);
        rafId = null;
    }
}

async function doSyncedTransition() {
    stopTransitionLoop();
    
    // Stop current video
    const currentLayer = contentLayers[activeLayer];
    const video = currentLayer.querySelector('video');
    if (video) {
        video.pause();
        video.onended = null;
    }
    
    // Calculate what should be playing NOW
    const position = getCurrentCyclePosition();
    const { index, elapsed } = getItemAtPosition(position);
    
    currentIndex = index;
    const nextLayer = 1 - activeLayer;
    
    log(`Transition to item ${currentIndex} "${playlist[currentIndex]?.name}"`);
    updateSyncIndicator('synced', `Item ${currentIndex+1}/${playlist.length}`);
    
    // If the preloaded item doesn't match, reload
    const preloadedForNext = (currentIndex === (activeLayer === 0 ? 1 : 0));
    if (!preloadedForNext) {
        await preload(currentIndex, nextLayer);
    }
    
    // Perform transition
    const newLayer = contentLayers[nextLayer];
    const oldLayer = contentLayers[activeLayer];
    
    newLayer.style.zIndex = '2';
    newLayer.classList.add('active');
    
    const transTime = transitionType === 'dissolve' ? transitionDuration * 1000 : 0;
    
    setTimeout(async () => {
        oldLayer.style.zIndex = '1';
        oldLayer.classList.remove('active');
        
        // Preload the next-next item
        const preloadIndex = (currentIndex + 1) % playlist.length;
        preload(preloadIndex, activeLayer);
        
        activeLayer = nextLayer;
        
        // Show the item (will seek video if needed)
        showSyncedItem(elapsed);
    }, transTime + 50);
}

// ============================================================
// SYNC MONITORING & CORRECTION
// ============================================================

function startSyncLoop() {
    if (syncCheckInterval) clearInterval(syncCheckInterval);
    
    // Check sync every second for tighter accuracy
    syncCheckInterval = setInterval(() => checkAndCorrectSync(), 1000);
}

function checkAndCorrectSync() {
    const position = getCurrentCyclePosition();
    const { index, elapsed } = getItemAtPosition(position);
    
    // Check if we're on the wrong item
    if (index !== currentIndex) {
        log(`SYNC DRIFT: showing item ${currentIndex}, should be ${index} - correcting`);
        resync();
        return;
    }
    
    // Check video timing drift - tighter threshold of 50ms
    const currentLayer = contentLayers[activeLayer];
    const video = currentLayer.querySelector('video');
    if (video && playlist[currentIndex]?.file_type === 'video') {
        const drift = Math.abs(video.currentTime - elapsed);
        if (drift > 0.05) {  // More than 50ms drift
            log(`VIDEO DRIFT: ${(drift*1000).toFixed(0)}ms - correcting`);
            video.currentTime = elapsed;
        }
    }
}

async function resync() {
    log('Resyncing...');
    updateSyncIndicator('syncing', 'Resyncing...');
    
    if (playbackTimer) {
        clearTimeout(playbackTimer);
        playbackTimer = null;
    }
    
    // Recalibrate time before resync
    serverTimeOffset = await performTimeSync();
    
    const position = getCurrentCyclePosition();
    const { index, elapsed } = getItemAtPosition(position);
    
    currentIndex = index;
    await preload(currentIndex, activeLayer);
    showSyncedItem(elapsed);
    
    // Preload next
    const nextIndex = (currentIndex + 1) % playlist.length;
    preload(nextIndex, 1 - activeLayer);
    
    updateSyncIndicator('synced', `Item ${currentIndex+1}/${playlist.length}`);
}

// ============================================================
// POLLING FOR UPDATES
// ============================================================

function startPolling() {
    if (pollTimer) clearInterval(pollTimer);
    
    pollTimer = setInterval(async () => {
        try {
            const r = await pywebview.api.get_playlist();
            if (!r.success) return;
            
            // Check if sync time changed (content was modified on server)
            if (r.sync && r.sync.start_time !== syncStartTime) {
                log('Server sync time changed - full resync');
                syncStartTime = r.sync.start_time;
                totalCycleDuration = r.sync.total_duration;
                // Don't overwrite serverTimeOffset - it's managed by the time sync loop
                
                playlist = r.playlist || [];
                calculateItemStartTimes();
                await resync();
                return;
            }
            
            // Check for playlist changes
            const newIds = (r.playlist || []).map(i => i.id).join(',');
            const oldIds = playlist.map(i => i.id).join(',');
            if (newIds !== oldIds) {
                log('Playlist items changed - full resync');
                await syncAndPlay();
                return;
            }
            
            // Update display settings if changed
            if (r.orientation !== orientation || r.flip_horizontal !== flipH || r.flip_vertical !== flipV) {
                orientation = r.orientation || 'landscape';
                flipH = r.flip_horizontal || false;
                flipV = r.flip_vertical || false;
                applyOrientation();
            }
        } catch (e) {
            console.error('Poll error', e);
        }
    }, 10000);  // Poll every 10 seconds
}

function stopPolling() {
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

function stopPlayback() {
    stopTransitionLoop();
    if (playbackTimer) { clearTimeout(playbackTimer); playbackTimer = null; }
    if (syncCheckInterval) { clearInterval(syncCheckInterval); syncCheckInterval = null; }
    stopPolling();
    stopTimeSyncLoop();
    contentLayers.forEach(l => {
        const v = l.querySelector('video');
        if (v) v.pause();
    });
}

// ============================================================
// SPLASH SCREEN
// ============================================================

async function showSplash() {
    log('Showing splash screen');
    contentDisplay.classList.add('hidden');
    updateSyncIndicator('', '');
    
    try {
        const r = await pywebview.api.get_default_display();
        if (!r.success || !r.default_display) {
            splashScreen.innerHTML = '';
            splashScreen.style.background = '#000';
            splashScreen.classList.remove('hidden');
            return;
        }
        
        const d = r.default_display;
        const srv = r.server_url || serverUrl;
        
        splashScreen.innerHTML = '';
        splashScreen.className = 'position-' + (d.logo_position || 'center');
        
        if (d.background_mode === 'solid') {
            splashScreen.style.background = d.background_color || '#000';
        } else if (d.background_mode === 'video' && d.background_video_filename) {
            const url = d.background_video_local_path ? 
                `${LOCAL_CACHE_URL}/splash/${d.background_video_filename}` : 
                srv + d.background_video_url;
            const v = document.createElement('video');
            v.id = 'splash-background';
            v.src = url;
            v.autoplay = true;
            v.muted = true;
            v.loop = true;
            v.playsInline = true;
            splashScreen.appendChild(v);
            splashScreen.style.background = '#000';
        } else if (d.backgrounds?.length) {
            const bg = d.backgrounds[0];
            const url = bg.local_path ?
                `${LOCAL_CACHE_URL}/splash/${bg.filename}` :
                srv + bg.url;
            const img = document.createElement('img');
            img.id = 'splash-background';
            img.src = url;
            splashScreen.appendChild(img);
            splashScreen.style.background = '#000';
        } else {
            splashScreen.style.background = d.background_color || '#000';
        }
        
        if (d.logo_filename) {
            const url = d.logo_local_path ?
                `${LOCAL_CACHE_URL}/splash/${d.logo_filename}` :
                srv + d.logo_url;
            const logo = document.createElement('img');
            logo.id = 'splash-logo';
            logo.src = url;
            logo.style.maxWidth = (d.logo_scale * 100) + '%';
            logo.style.maxHeight = (d.logo_scale * 80) + '%';
            splashScreen.appendChild(logo);
        }
        
        splashScreen.classList.remove('hidden');
    } catch (e) {
        log('Splash error: ' + e.message);
        splashScreen.innerHTML = '';
        splashScreen.style.background = '#000';
        splashScreen.classList.remove('hidden');
    }
}

// ============================================================
// DEBUG & UTILITIES
// ============================================================

function updateDebug() {
    let o = document.getElementById('debug-overlay');
    if (!o) {
        o = document.createElement('div');
        o.id = 'debug-overlay';
        o.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.95);color:#0f0;font-family:monospace;font-size:11px;padding:20px;overflow:auto;z-index:9999;white-space:pre-wrap';
        document.body.appendChild(o);
    }
    
    const item = playlist[currentIndex];
    const pos = getCurrentCyclePosition();
    const { index, elapsed, remaining } = getItemAtPosition(pos);
    const serverNow = getServerTime();
    
    // Calculate absolute next transition time (same calc as scheduleNextTransition)
    let nextTransitionTime = 0;
    if (item && totalCycleDuration > 0) {
        const cycleNumber = Math.floor((serverNow - syncStartTime) / totalCycleDuration);
        const cycleStartTime = syncStartTime + (cycleNumber * totalCycleDuration);
        nextTransitionTime = cycleStartTime + item._endTime;
    }
    const msUntilTransition = ((nextTransitionTime - serverNow) * 1000).toFixed(0);
    
    // Get video drift if applicable
    let videoDrift = 'N/A';
    const currentLayer = contentLayers[activeLayer];
    const video = currentLayer?.querySelector('video');
    if (video && item?.file_type === 'video') {
        videoDrift = ((video.currentTime - elapsed) * 1000).toFixed(0) + 'ms';
    }
    
    o.innerHTML = `<b>SYNC DEBUG (D=close R=resync S=setup)</b>

LOCAL TIME: ${serverNow.toFixed(3)}
Sync Start (from server): ${syncStartTime.toFixed(3)}
Elapsed since sync: ${(serverNow - syncStartTime).toFixed(3)}s
Cycle Duration: ${totalCycleDuration.toFixed(1)}s
Cycle Position: ${pos.toFixed(3)}s

NEXT TRANSITION AT: ${nextTransitionTime.toFixed(3)}
TIME UNTIL TRANSITION: ${msUntilTransition}ms

Playlist: ${playlist.length} items
Current Item: ${currentIndex} "${item?.name || 'N/A'}"
Should Be: ${index} (${elapsed.toFixed(3)}s in, ${remaining.toFixed(3)}s left)
Video Drift: ${videoDrift}
Active Layer: ${activeLayer}
Transition: ${transitionType} (${transitionDuration}s)

Items:
${playlist.map((p, i) => `  ${i === currentIndex ? '>' : ' '} ${i}: ${p.name} [${p._startTime?.toFixed(1)}-${p._endTime?.toFixed(1)}s]`).join('\n')}

Log:
${debugLog.slice(-12).join('\n')}`;
}

function hideDebug() {
    const o = document.getElementById('debug-overlay');
    if (o) o.remove();
}

function showError(m) { errorMessage.textContent = m; errorMessage.classList.remove('hidden'); }
function hideError() { errorMessage.classList.add('hidden'); }

// Keyboard shortcuts
document.addEventListener('keydown', e => {
    if (e.key === 'd' || e.key === 'D') { debugMode = !debugMode; if (debugMode) updateDebug(); else hideDebug(); }
    if (e.key === 'r' || e.key === 'R') { log('Manual resync'); resync(); }
    if (e.key === 's' || e.key === 'S') { stopPlayback(); setupScreen.classList.remove('hidden'); contentDisplay.classList.add('hidden'); splashScreen.classList.add('hidden'); }
});

accessCodeInput.addEventListener('input', e => { e.target.value = e.target.value.replace(/\D/g, '').slice(0, 6); });
accessCodeInput.addEventListener('keydown', e => { if (e.key === 'Enter') connect(); });

window.addEventListener('pywebviewready', init);
setTimeout(() => { if (typeof pywebview !== 'undefined') init(); }, 1000);
</script>
</body></html>'''


def main():
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
    
    api = PlayerAPI(window)
    window.expose(
        api.get_config,
        api.register,
        api.disconnect,
        api.get_playlist,
        api.get_default_display,
        api.get_content_url,
        api.get_local_file_url,
        api.get_sync_status,
        api.get_screen_info,
        api.time_sync,
        api.log,
    )
    
    webview.start(debug=config.debug, private_mode=False)


if __name__ == "__main__":
    main()