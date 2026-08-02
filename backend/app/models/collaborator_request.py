from datetime import datetime, timezone

from sqlalchemy import (
    ForeignKey,
    String,
    DateTime,
    Index
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.database import Base


class CollaboratorRequest(Base):

    __tablename__ = (
        "collaborator_requests"
    )
    __table_args__ = (
        Index(
            "ix_collaborator_requests_sender_id",
            "sender_id"
        ),
        Index(
            "ix_collaborator_requests_receiver_status",
            "receiver_id",
            "status"
        ),
        Index(
            "ix_collaborator_requests_created_at",
            "created_at"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    receiver_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    status: Mapped[str] = mapped_column(
        String,
        default="pending"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
