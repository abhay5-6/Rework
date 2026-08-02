from sqlalchemy import String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from app.db.database import Base


class Desk(Base):
    __tablename__ = "desks"
    __table_args__ = (
        Index("ix_desks_room_id", "room_id"),
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

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
