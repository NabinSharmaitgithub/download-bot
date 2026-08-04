import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base, TimestampMixin


class DownloadStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueueStatus(str, enum.Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    BANNED = "banned"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    preferred_video_quality: Mapped[str] = mapped_column(String(20), default="best", nullable=False)
    preferred_audio_format: Mapped[str] = mapped_column(String(10), default="mp3", nullable=False)
    max_concurrent_downloads: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    download_limit_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    downloads: Mapped[list["Download"]] = relationship(
        "Download", back_populates="user", lazy="selectin"
    )
    queue_items: Mapped[list["QueueItem"]] = relationship(
        "QueueItem", back_populates="user", lazy="selectin"
    )
    settings: Mapped[Optional["UserSettings"]] = relationship(
        "UserSettings", back_populates="user", uselist=False, lazy="selectin"
    )

    __table_args__ = (
        Index("ix_users_telegram_id", "telegram_id"),
        Index("ix_users_role", "role"),
    )


class Download(Base, TimestampMixin):
    __tablename__ = "downloads"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    status: Mapped[DownloadStatus] = mapped_column(
        Enum(DownloadStatus), default=DownloadStatus.PENDING, nullable=False, index=True
    )
    progress: Mapped[float] = mapped_column(default=0.0, nullable=False)
    speed: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    eta: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    temp_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="downloads")
    queue_item: Mapped[Optional["QueueItem"]] = relationship(
        "QueueItem", back_populates="download", uselist=False, lazy="selectin"
    )

    __table_args__ = (
        Index("ix_downloads_user_status", "user_id", "status"),
        Index("ix_downloads_provider", "provider"),
        Index("ix_downloads_created_at", "created_at"),
    )


class DownloadHistory(Base, TimestampMixin):
    __tablename__ = "download_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    status: Mapped[DownloadStatus] = mapped_column(Enum(DownloadStatus), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_download_history_user_created", "user_id", "created_at"),
        Index("ix_download_history_status", "status"),
    )


class QueueItem(Base, TimestampMixin):
    __tablename__ = "queue"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    download_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("downloads.id", ondelete="SET NULL"), nullable=True, unique=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[QueueStatus] = mapped_column(
        Enum(QueueStatus), default=QueueStatus.WAITING, nullable=False, index=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="queue_items")
    download: Mapped[Optional["Download"]] = relationship(
        "Download", back_populates="queue_item", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_queue_user_status", "user_id", "status"),
        Index("ix_queue_position", "user_id", "position"),
    )


class UserSettings(Base, TimestampMixin):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    video_quality: Mapped[str] = mapped_column(String(20), default="best", nullable=False)
    audio_format: Mapped[str] = mapped_column(String(10), default="mp3", nullable=False)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_download_start: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_download_complete: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_download_failed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_queue_finished: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_link_expired: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_concurrent_downloads: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    auto_delete_after_delivery: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="settings")


class AdminLog(Base, TimestampMixin):
    __tablename__ = "admin_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_admin_logs_admin_created", "admin_id", "created_at"),
        Index("ix_admin_logs_action", "action"),
    )


class Statistics(Base, TimestampMixin):
    __tablename__ = "statistics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, unique=True, index=True
    )
    total_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_users: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_downloads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_downloads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_downloads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_bytes_downloaded: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    youtube_downloads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    google_drive_downloads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    dropbox_downloads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    terabox_downloads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_download_duration: Mapped[float] = mapped_column(default=0.0, nullable=False)
    queue_peak_length: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (Index("ix_statistics_date", "date"),)
