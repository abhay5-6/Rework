from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from app.models.room_memory import (
    RoomMemory
)
from app.models.user import User
from sqlalchemy import select
from datetime import datetime, timedelta, timezone


async def create_room_memory(

    db: AsyncSession,

    room_id: int,

    created_by: int,

    content: str,

    embedding: list[float],

    memory_type: str = "note",

    source_type: str = "message",

    source_id: int | None = None,

    importance_score: int = 1,

    tags: list[str] | None = None,

    domain: str = "general",
):

    if tags is None:
        tags = []

    memory = RoomMemory(

        room_id=room_id,

        created_by=created_by,

        content=content,

        memory_type=memory_type,

        source_type=source_type,

        source_id=source_id,

        importance_score=importance_score,

        access_count=0,

        tags=tags,

        embedding=embedding,

        domain=domain,
    )

    db.add(memory)

    await db.flush()

    await db.refresh(memory)

    return memory

async def get_stale_memories(db: AsyncSession, room_id: int, days_old: int = 30):
    threshold_date = datetime.now(timezone.utc) - timedelta(days=days_old)
    query = select(RoomMemory).where(
        RoomMemory.room_id == room_id,
        RoomMemory.last_reinforced_at < threshold_date
    ).order_by(RoomMemory.last_reinforced_at.asc())
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_room_memories(
    db: AsyncSession,
    room_id: int,
    limit: int = 20
):
    query = (
        select(RoomMemory, User.username)
        .join(User, RoomMemory.created_by == User.id)
        .where(RoomMemory.room_id == room_id)
        .order_by(RoomMemory.created_at.desc())
        .limit(limit)
    )

    result = await db.execute(query)

    memories = []
    for memory, creator_username in result.all():
        memories.append({
            "id": memory.id,
            "room_id": memory.room_id,
            "created_by": memory.created_by,
            "content": memory.content,
            "memory_type": memory.memory_type,
            "source_type": memory.source_type,
            "source_id": memory.source_id,
            "domain": memory.domain,
            "importance_score": memory.importance_score,
            "confidence_score": memory.confidence_score,
            "tags": memory.tags or [],
            "created_at": memory.created_at,
            "last_reinforced_at": memory.last_reinforced_at,
            "creator_username": creator_username,
        })

    return memories

async def reinforce_memory(
    db: AsyncSession,
    room_id: int,
    memory_id: int
):
    query = select(RoomMemory).where(
        RoomMemory.id == memory_id,
        RoomMemory.room_id == room_id
    )
    result = await db.execute(query)
    memory = result.scalars().first()
    if memory:
        memory.last_reinforced_at = datetime.now(timezone.utc)
        memory.confidence_score = min(1.0, memory.confidence_score + 0.2)
        await db.commit()
    return memory


async def update_memory(
    db: AsyncSession,
    room_id: int,
    memory_id: int,
    content: str | None = None,
    embedding: list[float] | None = None,
    importance_score: int | None = None,
    tags: list[str] | None = None,
):
    query = select(RoomMemory).where(
        RoomMemory.id == memory_id,
        RoomMemory.room_id == room_id
    )
    result = await db.execute(query)
    memory = result.scalars().first()

    if not memory:
        return None

    if content is not None:
        memory.content = content
        memory.last_reinforced_at = datetime.now(timezone.utc)
        memory.confidence_score = 1.0
    if embedding is not None:
        memory.embedding = embedding
    if importance_score is not None:
        memory.importance_score = importance_score
    if tags is not None:
        memory.tags = tags

    await db.flush()
    await db.refresh(memory)
    return memory

async def delete_memory(
    db: AsyncSession,
    room_id: int,
    memory_id: int
):
    query = select(RoomMemory).where(
        RoomMemory.id == memory_id,
        RoomMemory.room_id == room_id
    )
    result = await db.execute(query)
    memory = result.scalars().first()
    if memory:
        await db.delete(memory)
        await db.commit()
        return True
    return False
