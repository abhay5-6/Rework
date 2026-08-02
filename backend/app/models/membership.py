from sqlalchemy import (
    ForeignKey,
    String,
    DateTime,
    Index
)
from datetime import datetime, timezone
from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.database import Base


class RoomMembership(Base):
    __tablename__ = "room_memberships"
    __table_args__ = (
        Index("ix_room_membership_user_id", "user_id"),
        Index("ix_room_membership_room_id", "room_id"),
        Index("ix_room_membership_user_room", "user_id", "room_id"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id")
    )    

    role: Mapped[str] = mapped_column(
        String(20),
        default="member"
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    