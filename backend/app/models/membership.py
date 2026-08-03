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


class WorkspaceMembership(Base):
    __tablename__ = "workspace_memberships"
    __table_args__ = (
        Index("ix_workspace_membership_user_id", "user_id"),
        Index("ix_workspace_membership_workspace_id", "workspace_id"),
        Index("ix_workspace_membership_user_workspace", "user_id", "workspace_id"),
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

    role: Mapped[str] = mapped_column(
        String(20),
        default="member"
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    