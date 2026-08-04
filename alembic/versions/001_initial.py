"""Initial migration

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("preferred_language", sa.String(length=10), nullable=False, server_default="en"),
        sa.Column(
            "preferred_video_quality", sa.String(length=20), nullable=False, server_default="best"
        ),
        sa.Column(
            "preferred_audio_format", sa.String(length=10), nullable=False, server_default="mp3"
        ),
        sa.Column("max_concurrent_downloads", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("download_limit_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column(
            "role",
            sa.Enum("user", "admin", "banned", name="userrole"),
            nullable=False,
            server_default="user",
        ),
        sa.Column("is_banned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=False)
    op.create_index("ix_users_role", "users", ["role"], unique=False)

    op.create_table(
        "downloads",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "queued",
                "downloading",
                "paused",
                "completed",
                "failed",
                "cancelled",
                name="downloadstatus",
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("speed", sa.BigInteger(), nullable=True),
        sa.Column("eta", sa.Integer(), nullable=True),
        sa.Column("temp_path", sa.String(length=500), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_downloads_user_status", "downloads", ["user_id", "status"], unique=False)
    op.create_index("ix_downloads_provider", "downloads", ["provider"], unique=False)
    op.create_index("ix_downloads_created_at", "downloads", ["created_at"], unique=False)

    op.create_table(
        "download_history",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "queued",
                "downloading",
                "paused",
                "completed",
                "failed",
                "cancelled",
                name="downloadstatus",
            ),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_download_history_user_created",
        "download_history",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index("ix_download_history_status", "download_history", ["status"], unique=False)

    op.create_table(
        "queue",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("download_id", sa.BigInteger(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.Enum("waiting", "active", "completed", "failed", "cancelled", name="queuestatus"),
            nullable=False,
            server_default="waiting",
        ),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["download_id"], ["downloads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("download_id"),
    )
    op.create_index("ix_queue_user_status", "queue", ["user_id", "status"], unique=False)
    op.create_index("ix_queue_position", "queue", ["user_id", "position"], unique=False)

    op.create_table(
        "user_settings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="en"),
        sa.Column("video_quality", sa.String(length=20), nullable=False, server_default="best"),
        sa.Column("audio_format", sa.String(length=10), nullable=False, server_default="mp3"),
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_download_start", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_download_complete", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_download_failed", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_queue_finished", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_link_expired", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("max_concurrent_downloads", sa.Integer(), nullable=False, server_default="3"),
        sa.Column(
            "auto_delete_after_delivery", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "admin_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("admin_id", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("target_user_id", sa.BigInteger(), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_admin_logs_admin_created", "admin_logs", ["admin_id", "created_at"], unique=False
    )
    op.create_index("ix_admin_logs_action", "admin_logs", ["action"], unique=False)

    op.create_table(
        "statistics",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_users", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_users", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_users", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_downloads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_downloads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_downloads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_bytes_downloaded", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("youtube_downloads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("google_drive_downloads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dropbox_downloads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("terabox_downloads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_download_duration", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("queue_peak_length", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date"),
    )
    op.create_index("ix_statistics_date", "statistics", ["date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_statistics_date", table_name="statistics")
    op.drop_table("statistics")
    op.drop_index("ix_admin_logs_action", table_name="admin_logs")
    op.drop_index("ix_admin_logs_admin_created", table_name="admin_logs")
    op.drop_table("admin_logs")
    op.drop_table("user_settings")
    op.drop_index("ix_queue_position", table_name="queue")
    op.drop_index("ix_queue_user_status", table_name="queue")
    op.drop_table("queue")
    op.drop_index("ix_download_history_status", table_name="download_history")
    op.drop_index("ix_download_history_user_created", table_name="download_history")
    op.drop_table("download_history")
    op.drop_index("ix_downloads_created_at", table_name="downloads")
    op.drop_index("ix_downloads_provider", table_name="downloads")
    op.drop_index("ix_downloads_user_status", table_name="downloads")
    op.drop_table("downloads")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")

    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="downloadstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="queuestatus").drop(op.get_bind(), checkfirst=True)