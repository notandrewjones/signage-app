"""
Database models for the Digital Signage System
"""
from datetime import datetime, time
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Time, 
    ForeignKey, Table, Text, Float, create_engine
)
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()

# Association tables for many-to-many relationships
device_content_groups = Table(
    'device_content_groups',
    Base.metadata,
    Column('device_id', Integer, ForeignKey('devices.id'), primary_key=True),
    Column('content_group_id', Integer, ForeignKey('content_groups.id'), primary_key=True)
)

schedule_content_groups = Table(
    'schedule_content_groups',
    Base.metadata,
    Column('schedule_id', Integer, ForeignKey('schedules.id'), primary_key=True),
    Column('content_group_id', Integer, ForeignKey('content_groups.id'), primary_key=True)
)


class ContentGroup(Base):
    """Groups of content (e.g., 'Gym Content', 'Check-in Content')"""
    __tablename__ = 'content_groups'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), default='#3B82F6')  # Hex color for UI
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    content_items = relationship('ContentItem', back_populates='group', cascade='all, delete-orphan')
    devices = relationship('Device', secondary=device_content_groups, back_populates='content_groups')
    schedules = relationship('Schedule', secondary=schedule_content_groups, back_populates='content_groups')


class ContentItem(Base):
    """Individual content items (videos, images)"""
    __tablename__ = 'content_items'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # 'video', 'image'
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    duration = Column(Float, nullable=True)  # seconds, for videos
    display_duration = Column(Float, default=10.0)  # seconds to display (for images)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    group_id = Column(Integer, ForeignKey('content_groups.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    group = relationship('ContentGroup', back_populates='content_items')


class ScheduleGroup(Base):
    """Groups of schedules (e.g., 'Morning Rotation', 'Weekend Schedule')"""
    __tablename__ = 'schedule_groups'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), default='#10B981')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    schedules = relationship('Schedule', back_populates='schedule_group', cascade='all, delete-orphan')
    devices = relationship('Device', back_populates='schedule_group')


class Schedule(Base):
    """Individual schedule entries"""
    __tablename__ = 'schedules'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    schedule_group_id = Column(Integer, ForeignKey('schedule_groups.id'), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    days_of_week = Column(String(20), default='0123456')  # 0=Mon, 6=Sun
    priority = Column(Integer, default=0)  # Higher priority wins conflicts
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    schedule_group = relationship('ScheduleGroup', back_populates='schedules')
    content_groups = relationship('ContentGroup', secondary=schedule_content_groups, back_populates='schedules')


class Device(Base):
    """Individual display devices"""
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    device_key = Column(String(64), nullable=False, unique=True)  # Unique identifier
    description = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)
    ip_address = Column(String(45), nullable=True)
    last_seen = Column(DateTime, nullable=True)
    is_online = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    screen_width = Column(Integer, nullable=True)
    screen_height = Column(Integer, nullable=True)
    schedule_group_id = Column(Integer, ForeignKey('schedule_groups.id'), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    schedule_group = relationship('ScheduleGroup', back_populates='devices')
    content_groups = relationship('ContentGroup', secondary=device_content_groups, back_populates='devices')


class DefaultDisplay(Base):
    """Default display settings (logo, backgrounds) when no content is scheduled"""
    __tablename__ = 'default_display'
    
    id = Column(Integer, primary_key=True)
    logo_filename = Column(String(500), nullable=True)
    logo_scale = Column(Float, default=0.5)  # 0.1 to 1.0
    logo_position = Column(String(20), default='center')  # center, top, bottom
    background_mode = Column(String(20), default='solid')  # solid, image, slideshow
    background_color = Column(String(7), default='#000000')
    slideshow_duration = Column(Float, default=30.0)  # seconds per background
    slideshow_transition = Column(String(20), default='fade')  # fade, slide, none
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    backgrounds = relationship('BackgroundImage', back_populates='default_display', cascade='all, delete-orphan')


class BackgroundImage(Base):
    """Background images for the default display"""
    __tablename__ = 'background_images'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(500), nullable=False)
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    default_display_id = Column(Integer, ForeignKey('default_display.id'), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    default_display = relationship('DefaultDisplay', back_populates='backgrounds')


class SyncLog(Base):
    """Log of content sync operations"""
    __tablename__ = 'sync_logs'
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey('devices.id'), nullable=False)
    action = Column(String(50), nullable=False)  # download, delete, sync_complete
    content_item_id = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False)  # pending, success, failed
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())


def init_db(db_url: str = "sqlite:///signage.db"):
    """Initialize the database"""
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create default display settings if not exists
    if not session.query(DefaultDisplay).first():
        default_display = DefaultDisplay()
        session.add(default_display)
        session.commit()
    
    session.close()
    return engine


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
