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
        Index("ix_messages_room_id", "room_id"),
        Index("ix_messages_sender_id", "sender_id"),
        Index("ix_messages_created_at", "created_at"),
        Index(
            "ix_messages_room_created_at",
            "room_id",
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

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id")
    )

    desk_id: Mapped[int | None] = mapped_column(
        ForeignKey("desks.id", ondelete="CASCADE"),
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
