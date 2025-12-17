#!/usr/bin/env python3
"""
Digital Signage Player Client
Runs on lightweight devices (Raspberry Pi, etc.) connected to displays
"""
import os
import sys
import json
import time
import hashlib
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, field
import urllib.request
import urllib.error
import ssl
import subprocess
import signal

# Try to import websockets, fallback to polling if not available
try:
    import websockets
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    print("websockets not installed, falling back to polling mode")

# Configuration
CONFIG_FILE = Path.home() / ".signage" / "config.json"
CONTENT_DIR = Path.home() / ".signage" / "content"
CACHE_FILE = Path.home() / ".signage" / "cache.json"
LOG_FILE = Path.home() / ".signage" / "player.log"

# Ensure directories exist
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
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
class PlayerConfig:
    server_url: str = "http://localhost:8000"
    device_key: str = ""
    sync_interval: int = 60  # seconds
    heartbeat_interval: int = 30  # seconds
    display_method: str = "chromium"  # chromium, vlc, feh
    fullscreen: bool = True
    
    def save(self):
        CONFIG_FILE.write_text(json.dumps(self.__dict__, indent=2))
    
    @classmethod
    def load(cls) -> 'PlayerConfig':
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


class ContentCache:
    """Manages local content cache"""
    
    def __init__(self):
        self.cache: Dict[int, dict] = {}
        self.load()
    
    def load(self):
        if CACHE_FILE.exists():
            try:
                self.cache = json.loads(CACHE_FILE.read_text())
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                self.cache = {}
    
    def save(self):
        CACHE_FILE.write_text(json.dumps(self.cache, indent=2))
    
    def is_cached(self, item: ContentItem) -> bool:
        """Check if content is already downloaded and valid"""
        if item.id not in self.cache:
            return False
        
        cached = self.cache[item.id]
        local_path = item.local_path
        
        if not local_path.exists():
            return False
        
        if local_path.stat().st_size != item.file_size:
            return False
        
        return True
    
    def add(self, item: ContentItem):
        self.cache[item.id] = {
            'filename': item.filename,
            'file_size': item.file_size,
            'downloaded_at': datetime.now().isoformat()
        }
        self.save()
    
    def remove(self, item_id: int):
        if item_id in self.cache:
            del self.cache[item_id]
            self.save()
    
    def get_orphaned_files(self, current_items: List[ContentItem]) -> List[Path]:
        """Find local files that are no longer in the playlist"""
        current_filenames = {item.filename for item in current_items}
        orphaned = []
        
        for file_path in CONTENT_DIR.iterdir():
            if file_path.name not in current_filenames:
                orphaned.append(file_path)
        
        return orphaned


class SignagePlayer:
    """Main player class"""
    
    def __init__(self, config: PlayerConfig):
        self.config = config
        self.cache = ContentCache()
        self.current_playlist: List[ContentItem] = []
        self.default_display: Optional[dict] = None
        self.running = False
        self.display_process: Optional[subprocess.Popen] = None
        self.current_index = 0
        self.last_sync = 0
    
    def api_request(self, endpoint: str) -> Optional[dict]:
        """Make API request to server"""
        url = f"{self.config.server_url}/api{endpoint}"
        
        try:
            # Create SSL context that doesn't verify certificates (for local dev)
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
        full_url = f"{self.config.server_url}{url}"
        
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
        logger.info("Syncing content...")
        
        # Get current playlist
        playlist_data = self.api_request(f"/player/{self.config.device_key}/playlist")
        if not playlist_data:
            logger.error("Failed to get playlist")
            return False
        
        # Get full config for default display
        config_data = self.api_request(f"/player/{self.config.device_key}/config")
        if config_data:
            self.default_display = config_data.get('default_display')
        
        # Parse playlist items
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
            if not self.cache.is_cached(item):
                if self.download_file(item.url, item.local_path):
                    self.cache.add(item)
        
        # Clean up orphaned files
        orphaned = self.cache.get_orphaned_files(new_playlist)
        for file_path in orphaned:
            logger.info(f"Removing orphaned file: {file_path.name}")
            try:
                file_path.unlink()
            except Exception as e:
                logger.error(f"Error removing file: {e}")
        
        # Download default display assets if needed
        if self.default_display:
            # Download logo
            if self.default_display.get('logo_url'):
                logo_path = CONTENT_DIR / f"_logo_{self.default_display['logo_filename']}"
                if not logo_path.exists():
                    self.download_file(self.default_display['logo_url'], logo_path)
            
            # Download backgrounds
            for bg in self.default_display.get('backgrounds', []):
                bg_path = CONTENT_DIR / f"_bg_{bg['filename']}"
                if not bg_path.exists():
                    self.download_file(bg['url'], bg_path)
        
        self.current_playlist = new_playlist
        self.last_sync = time.time()
        
        logger.info(f"Sync complete. {len(new_playlist)} items in playlist")
        return True
    
    def get_current_content(self) -> Optional[Path]:
        """Get the current content to display"""
        if not self.current_playlist:
            return None
        
        if self.current_index >= len(self.current_playlist):
            self.current_index = 0
        
        item = self.current_playlist[self.current_index]
        
        if item.local_path.exists():
            return item.local_path
        
        return None
    
    def advance_playlist(self):
        """Move to next item in playlist"""
        if self.current_playlist:
            self.current_index = (self.current_index + 1) % len(self.current_playlist)
    
    def get_current_duration(self) -> float:
        """Get display duration for current content"""
        if not self.current_playlist:
            return 10.0
        
        if self.current_index < len(self.current_playlist):
            return self.current_playlist[self.current_index].display_duration
        
        return 10.0
    
    def display_content_chromium(self, content_path: Path):
        """Display content using Chromium in kiosk mode"""
        # For images and videos, we'll use a simple HTML wrapper
        html_path = CONTENT_DIR / "_display.html"
        
        item = self.current_playlist[self.current_index] if self.current_playlist else None
        
        if item and item.file_type == 'video':
            html_content = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    * {{ margin: 0; padding: 0; }}
                    body {{ background: #000; overflow: hidden; }}
                    video {{ width: 100vw; height: 100vh; object-fit: contain; }}
                </style>
            </head>
            <body>
                <video autoplay muted>
                    <source src="file://{content_path.absolute()}" type="{item.mime_type if hasattr(item, 'mime_type') else 'video/mp4'}">
                </video>
            </body>
            </html>
            '''
        else:
            html_content = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    * {{ margin: 0; padding: 0; }}
                    body {{ 
                        background: #000; 
                        overflow: hidden;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                    }}
                    img {{ max-width: 100vw; max-height: 100vh; object-fit: contain; }}
                </style>
            </head>
            <body>
                <img src="file://{content_path.absolute()}">
            </body>
            </html>
            '''
        
        html_path.write_text(html_content)
        
        # Launch or refresh Chromium
        if self.display_process is None or self.display_process.poll() is not None:
            cmd = [
                'chromium-browser',
                '--kiosk',
                '--noerrdialogs',
                '--disable-infobars',
                '--disable-session-crashed-bubble',
                '--disable-features=TranslateUI',
                '--check-for-update-interval=31536000',
                f'file://{html_path.absolute()}'
            ]
            
            if self.config.fullscreen:
                cmd.append('--start-fullscreen')
            
            try:
                self.display_process = subprocess.Popen(cmd, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                logger.error("Chromium not found, trying chromium")
                cmd[0] = 'chromium'
                try:
                    self.display_process = subprocess.Popen(cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
                except FileNotFoundError:
                    logger.error("Chromium not found")
    
    def display_default(self):
        """Display default screen (logo with background)"""
        if not self.default_display:
            logger.info("No default display configured")
            return
        
        # Build HTML for default display
        bg_style = ''
        if self.default_display['background_mode'] == 'solid':
            bg_style = f"background-color: {self.default_display['background_color']};"
        elif self.default_display.get('backgrounds'):
            bg_path = CONTENT_DIR / f"_bg_{self.default_display['backgrounds'][0]['filename']}"
            if bg_path.exists():
                bg_style = f"background-image: url('file://{bg_path.absolute()}'); background-size: cover; background-position: center;"
        
        logo_html = ''
        if self.default_display.get('logo_filename'):
            logo_path = CONTENT_DIR / f"_logo_{self.default_display['logo_filename']}"
            if logo_path.exists():
                scale = self.default_display.get('logo_scale', 0.5)
                logo_html = f'<img src="file://{logo_path.absolute()}" style="transform: scale({scale}); max-width: 80%; max-height: 80%;">'
        
        position_style = {
            'top': 'align-items: flex-start; padding-top: 10%;',
            'center': 'align-items: center;',
            'bottom': 'align-items: flex-end; padding-bottom: 10%;'
        }.get(self.default_display.get('logo_position', 'center'), 'align-items: center;')
        
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                * {{ margin: 0; padding: 0; }}
                body {{ 
                    {bg_style}
                    overflow: hidden;
                    display: flex;
                    justify-content: center;
                    {position_style}
                    height: 100vh;
                }}
            </style>
        </head>
        <body>
            {logo_html}
        </body>
        </html>
        '''
        
        html_path = CONTENT_DIR / "_display.html"
        html_path.write_text(html_content)
        
        # Launch Chromium if not running
        if self.display_process is None or self.display_process.poll() is not None:
            cmd = [
                'chromium-browser',
                '--kiosk',
                '--noerrdialogs',
                f'file://{html_path.absolute()}'
            ]
            try:
                self.display_process = subprocess.Popen(cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                cmd[0] = 'chromium'
                try:
                    self.display_process = subprocess.Popen(cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
                except:
                    logger.error("Could not launch display")
    
    def run_display_loop(self):
        """Main display loop"""
        while self.running:
            # Check if we need to sync
            if time.time() - self.last_sync > self.config.sync_interval:
                self.sync_content()
            
            # Get current content
            content_path = self.get_current_content()
            
            if content_path:
                logger.debug(f"Displaying: {content_path.name}")
                
                if self.config.display_method == 'chromium':
                    self.display_content_chromium(content_path)
                
                # Wait for duration
                duration = self.get_current_duration()
                time.sleep(duration)
                
                # Advance to next
                self.advance_playlist()
            else:
                # No content, show default display
                logger.debug("No content, showing default display")
                self.display_default()
                time.sleep(10)
    
    def stop(self):
        """Stop the player"""
        self.running = False
        if self.display_process:
            self.display_process.terminate()
            self.display_process = None
    
    def start(self):
        """Start the player"""
        logger.info("Starting signage player...")
        logger.info(f"Server: {self.config.server_url}")
        logger.info(f"Device Key: {self.config.device_key[:8]}...")
        
        self.running = True
        
        # Initial sync
        if not self.sync_content():
            logger.warning("Initial sync failed, will retry...")
        
        # Run display loop
        try:
            self.run_display_loop()
        except KeyboardInterrupt:
            logger.info("Interrupted")
        finally:
            self.stop()


def setup_wizard():
    """Interactive setup wizard"""
    print("\n=== Digital Signage Player Setup ===\n")
    
    config = PlayerConfig.load()
    
    server_url = input(f"Server URL [{config.server_url}]: ").strip()
    if server_url:
        config.server_url = server_url
    
    device_key = input(f"Device Key [{config.device_key[:8] + '...' if config.device_key else 'none'}]: ").strip()
    if device_key:
        config.device_key = device_key
    
    config.save()
    print("\nConfiguration saved!")
    print(f"Config file: {CONFIG_FILE}")
    print(f"Content directory: {CONTENT_DIR}")
    
    return config


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Digital Signage Player')
    parser.add_argument('--setup', action='store_true', help='Run setup wizard')
    parser.add_argument('--server', help='Server URL')
    parser.add_argument('--key', help='Device key')
    parser.add_argument('--sync-only', action='store_true', help='Sync content and exit')
    
    args = parser.parse_args()
    
    if args.setup:
        config = setup_wizard()
    else:
        config = PlayerConfig.load()
        
        if args.server:
            config.server_url = args.server
        if args.key:
            config.device_key = args.key
    
    if not config.device_key:
        print("Error: No device key configured. Run with --setup or provide --key")
        sys.exit(1)
    
    player = SignagePlayer(config)
    
    if args.sync_only:
        player.sync_content()
        print("Sync complete")
    else:
        # Handle signals
        def signal_handler(sig, frame):
            logger.info("Shutting down...")
            player.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        player.start()


if __name__ == "__main__":
    main()
