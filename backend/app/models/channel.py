from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from app.db.database import Base


class Channel(Base):
    __tablename__ = "channels"
    __table_args__ = (
        Index("ix_channels_workspace_id", "workspace_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    is_private: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
