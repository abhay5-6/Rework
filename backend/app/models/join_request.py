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
        "workspace_join_requests"
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id")
    )

    status: Mapped[str] = mapped_column(
        String,
        default="pending"
    )