from datetime import datetime, timezone
from app.core.config import settings
from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, String ,DateTime
from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.database import Base


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_workspace_id", "workspace_id"),
        Index("ix_messages_sender_id", "sender_id"),
        Index("ix_messages_created_at", "created_at"),
        Index(
            "ix_messages_workspace_created_at",
            "workspace_id",
            "created_at"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    sender_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id")
    )

    channel_id: Mapped[int | None] = mapped_column(
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=True
    )

    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=True
    )

    edited_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    embedding: Mapped[list | None] = (
        mapped_column(
            Vector(settings.embedding_dimension),
            nullable=True
        )
    )

    message_type: Mapped[str] = (
        mapped_column(
            String(50),
            default="chat"
        )
    )

    extra_data: Mapped[dict] = (
        mapped_column(
            JSON,
            default=dict
        )
    )
