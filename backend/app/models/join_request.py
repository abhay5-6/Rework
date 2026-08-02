from sqlalchemy import (
    ForeignKey,
    String
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.database import Base


class RoomJoinRequest(Base):

    __tablename__ = (
        "room_join_requests"
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

    status: Mapped[str] = mapped_column(
        String,
        default="pending"
    )