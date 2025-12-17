"""
Digital Signage System - Server API
FastAPI backend for managing content, schedules, and devices
"""
import os
import sys
import uuid
import random
import asyncio
import hashlib
import socket
from datetime import datetime, time, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path

# Add the server directory to Python path for imports
SERVER_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(SERVER_DIR))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, Session, joinedload
import json

from models import (
    Base, ScheduleGroup, Schedule, ContentItem,
    Device, DefaultDisplay, BackgroundImage, SyncLog, init_db
)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{SERVER_DIR}/signage.db")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", SERVER_DIR / "uploads"))
CONTENT_DIR = UPLOAD_DIR / "content"
LOGOS_DIR = UPLOAD_DIR / "logos"
BACKGROUNDS_DIR = UPLOAD_DIR / "backgrounds"


def generate_access_code(db: Session) -> str:
    """Generate a unique 6-digit access code"""
    while True:
        code = str(random.randint(100000, 999999))
        existing = db.query(Device).filter(Device.access_code == code).first()
        if not existing:
            return code


def get_local_ip() -> str:
    """Get the local IP address of this machine"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# Ensure directories exist
for dir_path in [CONTENT_DIR, LOGOS_DIR, BACKGROUNDS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize database
init_db(DATABASE_URL)

# FastAPI app
app = FastAPI(
    title="Digital Signage System",
    description="Control and manage digital signage displays",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, device_key: str):
        await websocket.accept()
        self.active_connections[device_key] = websocket
    
    def disconnect(self, device_key: str):
        if device_key in self.active_connections:
            del self.active_connections[device_key]
    
    async def send_to_device(self, device_key: str, message: dict):
        if device_key in self.active_connections:
            await self.active_connections[device_key].send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)

manager = ConnectionManager()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Models
class ScheduleGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "#3B82F6"
    is_active: bool = True

class ScheduleGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None

class ContentItemUpdate(BaseModel):
    name: Optional[str] = None
    display_duration: Optional[float] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None

class ScheduleCreate(BaseModel):
    name: str
    schedule_group_id: int
    start_time: str  # HH:MM format
    end_time: str    # HH:MM format
    days_of_week: str = "0123456"
    priority: int = 0
    is_active: bool = True

class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    days_of_week: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None

class DeviceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    location: Optional[str] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None
    orientation: Optional[str] = None
    flip_horizontal: Optional[bool] = None
    flip_vertical: Optional[bool] = None
    schedule_group_id: Optional[int] = None

class DefaultDisplayUpdate(BaseModel):
    logo_scale: Optional[float] = None
    logo_position: Optional[str] = None
    background_mode: Optional[str] = None
    background_color: Optional[str] = None
    slideshow_duration: Optional[float] = None
    slideshow_transition: Optional[str] = None

# Helper functions
def parse_time(time_str: str) -> time:
    """Parse HH:MM string to time object"""
    parts = time_str.split(":")
    return time(int(parts[0]), int(parts[1]))

def get_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def serialize_content_item(item: ContentItem) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "filename": item.filename,
        "file_type": item.file_type,
        "mime_type": item.mime_type,
        "file_size": item.file_size,
        "duration": item.duration,
        "display_duration": item.display_duration,
        "width": item.width,
        "height": item.height,
        "order": item.order,
        "is_active": item.is_active,
        "schedule_group_id": item.schedule_group_id,
        "url": f"/uploads/content/{item.filename}",
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }

def serialize_schedule_group(group: ScheduleGroup) -> dict:
    return {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "color": group.color,
        "is_active": group.is_active,
        "content_count": len(group.content_items) if group.content_items else 0,
        "schedule_count": len(group.schedules) if group.schedules else 0,
        "device_count": len(group.devices) if group.devices else 0,
        "created_at": group.created_at.isoformat() if group.created_at else None,
        "updated_at": group.updated_at.isoformat() if group.updated_at else None,
    }

def serialize_schedule(schedule: Schedule) -> dict:
    return {
        "id": schedule.id,
        "name": schedule.name,
        "schedule_group_id": schedule.schedule_group_id,
        "start_time": schedule.start_time.strftime("%H:%M"),
        "end_time": schedule.end_time.strftime("%H:%M"),
        "days_of_week": schedule.days_of_week,
        "priority": schedule.priority,
        "is_active": schedule.is_active,
        "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
    }

def serialize_device(device: Device) -> dict:
    return {
        "id": device.id,
        "name": device.name,
        "access_code": device.access_code,
        "description": device.description,
        "location": device.location,
        "ip_address": device.ip_address,
        "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        "is_online": device.is_online,
        "is_active": device.is_active,
        "is_registered": device.is_registered,
        "screen_width": device.screen_width,
        "screen_height": device.screen_height,
        "orientation": device.orientation,
        "flip_horizontal": device.flip_horizontal,
        "flip_vertical": device.flip_vertical,
        "schedule_group_id": device.schedule_group_id,
        "schedule_group": serialize_schedule_group(device.schedule_group) if device.schedule_group else None,
        "created_at": device.created_at.isoformat() if device.created_at else None,
    }

def serialize_default_display(display: DefaultDisplay) -> dict:
    return {
        "id": display.id,
        "logo_filename": display.logo_filename,
        "logo_url": f"/uploads/logos/{display.logo_filename}" if display.logo_filename else None,
        "logo_scale": display.logo_scale,
        "logo_position": display.logo_position,
        "background_mode": display.background_mode,
        "background_color": display.background_color,
        "background_video_filename": display.background_video_filename,
        "background_video_url": f"/uploads/backgrounds/{display.background_video_filename}" if display.background_video_filename else None,
        "slideshow_duration": display.slideshow_duration,
        "slideshow_transition": display.slideshow_transition,
        "backgrounds": [
            {
                "id": bg.id,
                "filename": bg.filename,
                "url": f"/uploads/backgrounds/{bg.filename}",
                "order": bg.order,
                "is_active": bg.is_active,
            }
            for bg in sorted(display.backgrounds, key=lambda x: x.order)
            if bg.is_active
        ],
    }

# ============== Schedule Groups (now includes content) ==============

@app.get("/api/schedule-groups")
def list_schedule_groups(db: Session = Depends(get_db)):
    groups = db.query(ScheduleGroup).options(
        joinedload(ScheduleGroup.schedules),
        joinedload(ScheduleGroup.devices),
        joinedload(ScheduleGroup.content_items)
    ).all()
    return [serialize_schedule_group(g) for g in groups]

@app.post("/api/schedule-groups")
def create_schedule_group(data: ScheduleGroupCreate, db: Session = Depends(get_db)):
    group = ScheduleGroup(**data.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)
    return serialize_schedule_group(group)

@app.get("/api/schedule-groups/{group_id}")
def get_schedule_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(ScheduleGroup).options(
        joinedload(ScheduleGroup.schedules),
        joinedload(ScheduleGroup.devices),
        joinedload(ScheduleGroup.content_items)
    ).filter(ScheduleGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Schedule group not found")
    
    result = serialize_schedule_group(group)
    result["schedules"] = [serialize_schedule(s) for s in group.schedules]
    result["devices"] = [serialize_device(d) for d in group.devices]
    result["content_items"] = [serialize_content_item(item) for item in sorted(group.content_items, key=lambda x: x.order)]
    return result

@app.patch("/api/schedule-groups/{group_id}")
def update_schedule_group(group_id: int, data: ScheduleGroupUpdate, db: Session = Depends(get_db)):
    group = db.query(ScheduleGroup).filter(ScheduleGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Schedule group not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(group, key, value)
    
    db.commit()
    db.refresh(group)
    return serialize_schedule_group(group)

@app.delete("/api/schedule-groups/{group_id}")
def delete_schedule_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(ScheduleGroup).filter(ScheduleGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Schedule group not found")
    
    # Delete associated content files
    for item in group.content_items:
        file_path = CONTENT_DIR / item.filename
        if file_path.exists():
            file_path.unlink()
    
    db.delete(group)
    db.commit()
    return {"status": "deleted"}

# ============== Content Items (now part of schedule groups) ==============

@app.post("/api/schedule-groups/{group_id}/content")
async def upload_content(
    group_id: int,
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    display_duration: float = Form(10.0),
    db: Session = Depends(get_db)
):
    group = db.query(ScheduleGroup).filter(ScheduleGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Schedule group not found")
    
    # Determine file type
    mime_type = file.content_type or "application/octet-stream"
    if mime_type.startswith("video/"):
        file_type = "video"
    elif mime_type.startswith("image/"):
        file_type = "image"
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # Generate unique filename
    ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = CONTENT_DIR / unique_filename
    
    # Save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Get max order
    max_order = db.query(ContentItem).filter(ContentItem.schedule_group_id == group_id).count()
    
    # Create content item
    item = ContentItem(
        name=name or file.filename,
        filename=unique_filename,
        file_type=file_type,
        mime_type=mime_type,
        file_size=len(content),
        display_duration=display_duration,
        order=max_order,
        schedule_group_id=group_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    # Notify connected devices
    await manager.broadcast({
        "type": "content_updated",
        "group_id": group_id,
    })
    
    return serialize_content_item(item)

@app.patch("/api/content/{item_id}")
async def update_content_item(item_id: int, data: ContentItemUpdate, db: Session = Depends(get_db)):
    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    
    db.commit()
    db.refresh(item)
    
    await manager.broadcast({
        "type": "content_updated",
        "group_id": item.schedule_group_id,
    })
    
    return serialize_content_item(item)

@app.delete("/api/content/{item_id}")
async def delete_content_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")
    
    group_id = item.schedule_group_id
    
    # Delete file
    file_path = CONTENT_DIR / item.filename
    if file_path.exists():
        file_path.unlink()
    
    db.delete(item)
    db.commit()
    
    await manager.broadcast({
        "type": "content_updated",
        "group_id": group_id,
    })
    
    return {"status": "deleted"}

@app.post("/api/schedule-groups/{group_id}/reorder")
async def reorder_content(group_id: int, item_ids: List[int], db: Session = Depends(get_db)):
    for order, item_id in enumerate(item_ids):
        item = db.query(ContentItem).filter(
            ContentItem.id == item_id,
            ContentItem.schedule_group_id == group_id
        ).first()
        if item:
            item.order = order
    
    db.commit()
    
    await manager.broadcast({
        "type": "content_updated",
        "group_id": group_id,
    })
    
    return {"status": "reordered"}

# ============== Schedules ==============

@app.post("/api/schedules")
async def create_schedule(data: ScheduleCreate, db: Session = Depends(get_db)):
    schedule = Schedule(
        name=data.name,
        schedule_group_id=data.schedule_group_id,
        start_time=parse_time(data.start_time),
        end_time=parse_time(data.end_time),
        days_of_week=data.days_of_week,
        priority=data.priority,
        is_active=data.is_active,
    )
    
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    
    await manager.broadcast({"type": "schedule_updated"})
    
    return serialize_schedule(schedule)

@app.patch("/api/schedules/{schedule_id}")
async def update_schedule(schedule_id: int, data: ScheduleUpdate, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    if "start_time" in update_data:
        update_data["start_time"] = parse_time(update_data["start_time"])
    if "end_time" in update_data:
        update_data["end_time"] = parse_time(update_data["end_time"])
    
    for key, value in update_data.items():
        setattr(schedule, key, value)
    
    db.commit()
    db.refresh(schedule)
    
    await manager.broadcast({"type": "schedule_updated"})
    
    return serialize_schedule(schedule)

@app.delete("/api/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    db.delete(schedule)
    db.commit()
    
    await manager.broadcast({"type": "schedule_updated"})
    
    return {"status": "deleted"}

# ============== Devices ==============

@app.get("/api/devices")
def list_devices(db: Session = Depends(get_db)):
    devices = db.query(Device).options(
        joinedload(Device.schedule_group)
    ).all()
    return [serialize_device(d) for d in devices]

@app.post("/api/devices")
def create_device(data: DeviceCreate, db: Session = Depends(get_db)):
    device = Device(
        name=data.name,
        description=data.description,
        location=data.location,
        access_code=generate_access_code(db),
        is_registered=False,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return serialize_device(device)

@app.get("/api/devices/{device_id}")
def get_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).options(
        joinedload(Device.schedule_group).joinedload(ScheduleGroup.schedules),
        joinedload(Device.schedule_group).joinedload(ScheduleGroup.content_items)
    ).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return serialize_device(device)

@app.patch("/api/devices/{device_id}")
async def update_device(device_id: int, data: DeviceUpdate, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(device, key, value)
    
    db.commit()
    db.refresh(device)
    
    # Notify the specific device
    await manager.send_to_device(device.access_code, {
        "type": "config_updated",
    })
    
    return serialize_device(device)

@app.delete("/api/devices/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    db.delete(device)
    db.commit()
    return {"status": "deleted"}

@app.post("/api/devices/{device_id}/regenerate-code")
def regenerate_access_code(device_id: int, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.access_code = generate_access_code(db)
    device.is_registered = False  # Require re-registration
    db.commit()
    db.refresh(device)
    return {"access_code": device.access_code}

# ============== Default Display (Splash Screen) ==============

@app.get("/api/default-display")
def get_default_display(db: Session = Depends(get_db)):
    display = db.query(DefaultDisplay).options(
        joinedload(DefaultDisplay.backgrounds)
    ).first()
    if not display:
        display = DefaultDisplay()
        db.add(display)
        db.commit()
        db.refresh(display)
    return serialize_default_display(display)

@app.patch("/api/default-display")
async def update_default_display(data: DefaultDisplayUpdate, db: Session = Depends(get_db)):
    display = db.query(DefaultDisplay).first()
    if not display:
        display = DefaultDisplay()
        db.add(display)
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(display, key, value)
    
    db.commit()
    db.refresh(display)
    
    await manager.broadcast({"type": "default_display_updated"})
    
    return serialize_default_display(display)

@app.post("/api/default-display/logo")
async def upload_logo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    display = db.query(DefaultDisplay).first()
    if not display:
        display = DefaultDisplay()
        db.add(display)
    
    # Delete old logo if exists
    if display.logo_filename:
        old_path = LOGOS_DIR / display.logo_filename
        if old_path.exists():
            old_path.unlink()
    
    # Save new logo
    ext = Path(file.filename).suffix
    unique_filename = f"logo_{uuid.uuid4().hex}{ext}"
    file_path = LOGOS_DIR / unique_filename
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    display.logo_filename = unique_filename
    db.commit()
    db.refresh(display)
    
    await manager.broadcast({"type": "default_display_updated"})
    
    return serialize_default_display(display)

@app.delete("/api/default-display/logo")
async def delete_logo(db: Session = Depends(get_db)):
    display = db.query(DefaultDisplay).first()
    if display and display.logo_filename:
        file_path = LOGOS_DIR / display.logo_filename
        if file_path.exists():
            file_path.unlink()
        display.logo_filename = None
        db.commit()
    
    await manager.broadcast({"type": "default_display_updated"})
    
    return {"status": "deleted"}

@app.post("/api/default-display/backgrounds")
async def upload_background(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    display = db.query(DefaultDisplay).first()
    if not display:
        display = DefaultDisplay()
        db.add(display)
        db.commit()
        db.refresh(display)
    
    # Save background
    ext = Path(file.filename).suffix
    unique_filename = f"bg_{uuid.uuid4().hex}{ext}"
    file_path = BACKGROUNDS_DIR / unique_filename
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Get max order
    max_order = db.query(BackgroundImage).filter(
        BackgroundImage.default_display_id == display.id
    ).count()
    
    background = BackgroundImage(
        filename=unique_filename,
        order=max_order,
        default_display_id=display.id,
    )
    db.add(background)
    db.commit()
    db.refresh(background)
    
    await manager.broadcast({"type": "default_display_updated"})
    
    return {
        "id": background.id,
        "filename": background.filename,
        "url": f"/uploads/backgrounds/{background.filename}",
        "order": background.order,
    }

@app.delete("/api/default-display/backgrounds/{background_id}")
async def delete_background(background_id: int, db: Session = Depends(get_db)):
    background = db.query(BackgroundImage).filter(BackgroundImage.id == background_id).first()
    if not background:
        raise HTTPException(status_code=404, detail="Background not found")
    
    file_path = BACKGROUNDS_DIR / background.filename
    if file_path.exists():
        file_path.unlink()
    
    db.delete(background)
    db.commit()
    
    await manager.broadcast({"type": "default_display_updated"})
    
    return {"status": "deleted"}

@app.post("/api/default-display/background-video")
async def upload_background_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    display = db.query(DefaultDisplay).first()
    if not display:
        display = DefaultDisplay()
        db.add(display)
    
    # Check if it's a video
    mime_type = file.content_type or ""
    if not mime_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Delete old video if exists
    if display.background_video_filename:
        old_path = BACKGROUNDS_DIR / display.background_video_filename
        if old_path.exists():
            old_path.unlink()
    
    # Save new video
    ext = Path(file.filename).suffix
    unique_filename = f"bgvideo_{uuid.uuid4().hex}{ext}"
    file_path = BACKGROUNDS_DIR / unique_filename
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    display.background_video_filename = unique_filename
    db.commit()
    db.refresh(display)
    
    await manager.broadcast({"type": "default_display_updated"})
    
    return serialize_default_display(display)

@app.delete("/api/default-display/background-video")
async def delete_background_video(db: Session = Depends(get_db)):
    display = db.query(DefaultDisplay).first()
    if display and display.background_video_filename:
        file_path = BACKGROUNDS_DIR / display.background_video_filename
        if file_path.exists():
            file_path.unlink()
        display.background_video_filename = None
        db.commit()
    
    await manager.broadcast({"type": "default_display_updated"})
    
    return {"status": "deleted"}

# ============== Player API ==============

@app.get("/api/discover")
def discover_server():
    """Endpoint for players to discover this server"""
    return {
        "name": "Digital Signage Server",
        "version": "1.0.0",
        "ip": get_local_ip(),
        "port": 8000,
    }

@app.post("/api/player/register")
def register_player(access_code: str = Form(...), db: Session = Depends(get_db)):
    """Register a player with an access code"""
    device = db.query(Device).filter(Device.access_code == access_code).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Invalid access code")
    
    if not device.is_active:
        raise HTTPException(status_code=403, detail="Device is disabled")
    
    # Mark as registered
    device.is_registered = True
    device.last_seen = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "device_name": device.name,
        "device_id": device.id,
        "access_code": device.access_code,
    }

@app.get("/api/player/{access_code}/config")
def get_player_config(access_code: str, db: Session = Depends(get_db)):
    """Get configuration for a player device"""
    device = db.query(Device).options(
        joinedload(Device.schedule_group).joinedload(ScheduleGroup.schedules),
        joinedload(Device.schedule_group).joinedload(ScheduleGroup.content_items)
    ).filter(Device.access_code == access_code).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Update last seen
    device.last_seen = datetime.utcnow()
    device.is_online = True
    db.commit()
    
    # Get default display (splash screen)
    default_display = db.query(DefaultDisplay).options(
        joinedload(DefaultDisplay.backgrounds)
    ).first()
    
    # Build content manifest from schedule group
    content_items = {}
    if device.schedule_group:
        for item in device.schedule_group.content_items:
            if item.is_active:
                content_items[item.id] = serialize_content_item(item)
    
    return {
        "device": serialize_device(device),
        "content_items": list(content_items.values()),
        "default_display": serialize_default_display(default_display) if default_display else None,
        "server_time": datetime.utcnow().isoformat(),
    }

@app.get("/api/player/{access_code}/playlist")
def get_player_playlist(access_code: str, db: Session = Depends(get_db)):
    """Get current playlist for a player device based on current time and schedule"""
    device = db.query(Device).options(
        joinedload(Device.schedule_group).joinedload(ScheduleGroup.schedules),
        joinedload(Device.schedule_group).joinedload(ScheduleGroup.content_items)
    ).filter(Device.access_code == access_code).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    now = datetime.now()
    current_time = now.time()
    current_day = str(now.weekday())
    
    playlist = []
    active_schedule = None
    debug_info = {
        "current_time": current_time.strftime("%H:%M:%S"),
        "current_day": current_day,
        "has_schedule_group": device.schedule_group is not None,
        "schedule_group_active": device.schedule_group.is_active if device.schedule_group else False,
        "total_schedules": 0,
        "total_content": 0,
        "schedule_check_results": [],
    }
    
    # Check if there's an active schedule
    if device.schedule_group and device.schedule_group.is_active:
        debug_info["total_schedules"] = len(device.schedule_group.schedules)
        debug_info["total_content"] = len(device.schedule_group.content_items)
        
        for schedule in device.schedule_group.schedules:
            schedule_info = {
                "name": schedule.name,
                "start": schedule.start_time.strftime("%H:%M"),
                "end": schedule.end_time.strftime("%H:%M"),
                "days": schedule.days_of_week,
                "is_active": schedule.is_active,
                "day_match": current_day in schedule.days_of_week,
                "time_match": False,
                "selected": False,
            }
            
            if not schedule.is_active:
                debug_info["schedule_check_results"].append(schedule_info)
                continue
            if current_day not in schedule.days_of_week:
                debug_info["schedule_check_results"].append(schedule_info)
                continue
            
            # Handle schedules that cross midnight
            if schedule.start_time <= schedule.end_time:
                in_range = schedule.start_time <= current_time <= schedule.end_time
            else:
                in_range = current_time >= schedule.start_time or current_time <= schedule.end_time
            
            schedule_info["time_match"] = in_range
            
            if in_range:
                if active_schedule is None or schedule.priority > active_schedule.priority:
                    active_schedule = schedule
                    schedule_info["selected"] = True
            
            debug_info["schedule_check_results"].append(schedule_info)
        
        # Get content from schedule group if schedule is active
        if active_schedule:
            for item in sorted(device.schedule_group.content_items, key=lambda x: x.order):
                if item.is_active:
                    playlist.append(serialize_content_item(item))
        
        # If no active schedule but there's content, optionally play it anyway
        # This makes testing easier - content plays even without a matching schedule
        if not active_schedule and len(device.schedule_group.content_items) > 0:
            debug_info["fallback_mode"] = True
            # Uncomment the following lines to always play content regardless of schedule:
            # for item in sorted(device.schedule_group.content_items, key=lambda x: x.order):
            #     if item.is_active:
            #         playlist.append(serialize_content_item(item))
    
    return {
        "playlist": playlist,
        "active_schedule": serialize_schedule(active_schedule) if active_schedule else None,
        "device": {
            "orientation": device.orientation,
            "flip_horizontal": device.flip_horizontal,
            "flip_vertical": device.flip_vertical,
        },
        "server_time": datetime.utcnow().isoformat(),
        "debug": debug_info,
    }

# ============== WebSocket ==============

@app.websocket("/ws/{access_code}")
async def websocket_endpoint(websocket: WebSocket, access_code: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.access_code == access_code).first()
    if not device:
        await websocket.close(code=4004)
        return
    
    await manager.connect(websocket, access_code)
    
    # Update device status
    device.is_online = True
    device.last_seen = datetime.utcnow()
    db.commit()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "heartbeat":
                device.last_seen = datetime.utcnow()
                device.ip_address = data.get("ip_address")
                device.screen_width = data.get("screen_width")
                device.screen_height = data.get("screen_height")
                db.commit()
                await websocket.send_json({"type": "heartbeat_ack"})
            
            elif data.get("type") == "sync_complete":
                # Log sync completion
                pass
            
    except WebSocketDisconnect:
        manager.disconnect(access_code)
        device.is_online = False
        db.commit()

# ============== Dashboard Stats ==============

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total_content = db.query(ContentItem).count()
    return {
        "total_devices": db.query(Device).count(),
        "online_devices": db.query(Device).filter(Device.is_online == True).count(),
        "schedule_groups": db.query(ScheduleGroup).count(),
        "total_content": total_content,
    }

# ============== Health Check ==============

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)