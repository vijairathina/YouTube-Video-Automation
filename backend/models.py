import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Index
from backend.database import Base

class UploadLog(Base):
    __tablename__ = "upload_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    video_id = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False, index=True) # Success, Failed, Pending
    error_details = Column(Text, nullable=True)
    file_path = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "title": self.title,
            "video_id": self.video_id or "N/A",
            "status": self.status,
            "error_details": self.error_details or "",
            "file_path": self.file_path or "",
            "uploaded_at": self.uploaded_at.strftime("%Y-%m-%d %H:%M:%S") if self.uploaded_at else ""
        }

class UploaderConfig(Base):
    __tablename__ = "uploader_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    folder_path = Column(Text, default=".")
    is_smb = Column(Boolean, default=False)
    smb_share = Column(String(255), default="")
    smb_username = Column(String(100), default="")
    smb_password = Column(String(255), default="")
    upload_interval_mins = Column(Integer, default=45)
    retry_interval_hours = Column(Integer, default=24)
    upload_enabled = Column(Boolean, default=True)
    status = Column(String(100), default="Idle")
    last_scan_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "folder_path": self.folder_path,
            "is_smb": self.is_smb,
            "smb_share": self.smb_share,
            "smb_username": self.smb_username,
            "upload_interval_mins": self.upload_interval_mins,
            "retry_interval_hours": self.retry_interval_hours,
            "upload_enabled": self.upload_enabled,
            "status": self.status,
            "last_scan_at": self.last_scan_at.isoformat() if self.last_scan_at else None
        }

class YouTubeAccount(Base):
    __tablename__ = "youtube_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String(100), nullable=True)
    channel_name = Column(String(255), nullable=True)
    token_json = Column(Text, nullable=True) # Serialized Credentials
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "channel_id": self.channel_id or "Not Configured",
            "channel_name": self.channel_name or "YouTube Account",
            "has_token": bool(self.token_json),
            "is_active": self.is_active,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class ScheduledVideo(Base):
    __tablename__ = "scheduled_videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(Text, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    category_id = Column(String(20), default="22")
    privacy_status = Column(String(20), default="private")
    scheduled_time = Column(DateTime, nullable=True)
    status = Column(String(50), default="pending") # pending, uploaded, failed
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "file_path": self.file_path,
            "title": self.title,
            "description": self.description,
            "category_id": self.category_id,
            "privacy_status": self.privacy_status,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "status": self.status
        }

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False, index=True)
    message = Column(String(255), nullable=False)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "event_type": self.event_type,
            "message": self.message,
            "details": json.loads(self.details_json) if self.details_json else {},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
