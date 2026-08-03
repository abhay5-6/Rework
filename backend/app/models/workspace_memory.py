from datetime import datetime, timezone

from sqlalchemy import (
Integer,
ForeignKey,
Text,
String,
DateTime,
JSON,
Float,
Index
)

from sqlalchemy.orm import (
Mapped,
mapped_column,
)

from pgvector.sqlalchemy import Vector

from app.db.database import Base

class WorkspaceMemory(Base):


    __tablename__ = "workspace_memories"

    __table_args__ = (
        Index("ix_workspace_memories_workspace_id", "workspace_id"),
        Index("ix_workspace_memories_created_by", "created_by"),
        Index("ix_workspace_memories_created_at", "created_at"),
        Index(
            "ix_workspace_memories_workspace_created_at",
            "workspace_id",
            "created_at"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id")
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    content: Mapped[str] = mapped_column(
        Text
    )

    memory_type: Mapped[str] = mapped_column(
        String(50),
        default="note"
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        default="message"
    )

    source_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    domain: Mapped[str] = mapped_column(
        String(100),
        default="general"
    )

    importance_score: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    confidence_score: Mapped[float] = mapped_column(
        Float,
        default=1.0
    )

    tags: Mapped[list] = mapped_column(
        JSON,
        default=list
    )

    access_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    times_referenced: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    agreement_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    disagreement_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    embedding: Mapped[list] = mapped_column(
        Vector(384)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    last_reinforced_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

