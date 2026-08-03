from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from app.models.user import User
from app.repositories.memory_repository import memory_repo


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

    memory = await memory_repo.create(
        db,
        obj_in={
            "room_id": room_id,
            "created_by": created_by,
            "content": content,
            "memory_type": memory_type,
            "source_type": source_type,
            "source_id": source_id,
            "importance_score": importance_score,
            "access_count": 0,
            "tags": tags,
            "embedding": embedding,
            "domain": domain,
        }
    )
    return memory


async def get_stale_memories(db: AsyncSession, room_id: int, days_old: int = 30):
    threshold_date = datetime.now(timezone.utc) - timedelta(days=days_old)
    memories = await memory_repo.get_stale_memories(db, room_id=room_id, threshold_date=threshold_date)
    return memories


async def get_room_memories(
    db: AsyncSession,
    room_id: int,
    limit: int = 20
):
    result = await memory_repo.get_memories_for_room_with_users(db, room_id=room_id, limit=limit)

    memories = []
    for memory, creator_username in result:
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
    memory = await memory_repo.get_memory_in_room(db, room_id=room_id, memory_id=memory_id)
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
    memory = await memory_repo.get_memory_in_room(db, room_id=room_id, memory_id=memory_id)
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
    memory = await memory_repo.get_memory_in_room(db, room_id=room_id, memory_id=memory_id)
    if memory:
        await memory_repo.remove(db, id=memory.id)
        return True
    return False
