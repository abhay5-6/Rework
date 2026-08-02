from datetime import datetime, timezone
from sqlalchemy import (
    Integer,
    ForeignKey,
    String,
    Text,
    DateTime,
    Boolean,
    Index
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from app.db.database import Base

class RoomTask(Base):
    __tablename__ = "room_tasks"
    __table_args__ = (
        Index("ix_room_tasks_room_id", "room_id"),
        Index("ix_room_tasks_assignee", "assignee_username"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"))
    
    # Text extracted directly from the chat by the AI
    description: Mapped[str] = mapped_column(Text)
    
    # The username of the person who is supposed to do it
    assignee_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Kanban Status: 'todo', 'in_progress', 'done'
    status: Mapped[str] = mapped_column(String(50), default="todo")
    
    # When the AI detected it
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    # When it was completed
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
