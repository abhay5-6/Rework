from sqlalchemy import (
    ForeignKey,
    String
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column
)

from app.db.database import Base


class MemoryEdge(Base):

    __tablename__ = "memory_edges"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    source_memory_id: Mapped[int] = (
        mapped_column(
            ForeignKey(
                "room_memories.id"
            )
        )
    )

    target_memory_id: Mapped[int] = (
        mapped_column(
            ForeignKey(
                "room_memories.id"
            )
        )
    )

    relationship_type: Mapped[str] = (
        mapped_column(
            String(50)
        )
    )