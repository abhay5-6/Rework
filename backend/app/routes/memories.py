from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request
)

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from app.db.session import get_db

from app.schemas.room_memory import (
    RoomMemoryCreate,
    RoomMemoryResponse,
    RoomMemoryUpdate,
    SearchResult
)

from app.services.ai.memory_service import (
    create_room_memory,
    get_room_memories,
    get_stale_memories,
    reinforce_memory,
    update_memory,
    delete_memory
)

from app.services.ai.embedding_service import (
    generate_embedding
)

from app.core.dependencies import (
    get_current_user
)

from app.core.config import settings

from app.core.rate_limit import limiter

from app.models.user import User

from app.services.message_service import has_room_access

from app.services.ai.retrieval_service import (
    search_room_memories
)

from app.services.ai.ai_client import (
    generate_room_answer
)

from app.services.ai.hybrid_retrieval_service import (
    retrieve_context
)
from app.schemas.common import (
    MemoryReinforceResponse,
    MessageOnlyResponse,
    RoomAiAnswerResponse,
)

router = APIRouter(
    prefix="/rooms",
    tags=["Memories"]
)


async def require_room_access(
    db: AsyncSession,
    room_id: int,
    current_user: User
):
    if not await has_room_access(db, room_id, current_user):
        raise HTTPException(
            status_code=403,
            detail="Access denied to this room"
        )


@router.post(
    "/{room_id}/memories",
    response_model=RoomMemoryResponse
)
async def add_room_memory(
    room_id: int,
    memory: RoomMemoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    await require_room_access(
        db,
        room_id,
        current_user
    )

    embedding = await generate_embedding(
        memory.content
    )

    created_memory = await create_room_memory(
        db=db,
        room_id=room_id,
        created_by=current_user.id,
        content=memory.content,
        embedding=embedding,
        memory_type=memory.memory_type,
        source_type=memory.source_type,
        source_id=memory.source_id,
        importance_score=memory.importance_score,
        tags=memory.tags,
        domain=memory.domain,
    )

    await db.commit()

    return created_memory


@router.get(
    "/{room_id}/memories",
    response_model=List[RoomMemoryResponse]
)
async def list_room_memories(
    room_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await require_room_access(db, room_id, current_user)

    return await get_room_memories(db, room_id, min(max(limit, 1), 50))


@router.get(
    "/{room_id}/memories/search",
    response_model=List[RoomMemoryResponse]
)
@limiter.limit(settings.ai_rate_limit)
async def semantic_memory_search(
    request: Request,
    room_id: int,
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await require_room_access(db, room_id, current_user)

    memories = await search_room_memories(
        db,
        room_id,
        query
    )

    return memories


@router.get(
    "/{room_id}/search",
    response_model=SearchResult
)
@limiter.limit(settings.ai_rate_limit)
async def hybrid_search(
    request: Request,
    room_id: int,
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await require_room_access(db, room_id, current_user)

    result = await retrieve_context(
        db=db,
        room_id=room_id,
        query=query,
        memory_limit=5,
        message_limit=10
    )

    return result


@router.get(
    "/{room_id}/ai",
    response_model=RoomAiAnswerResponse
)
@limiter.limit(settings.ai_rate_limit)
async def room_ai_query(
    request: Request,
    room_id: int,
    query: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await require_room_access(db, room_id, current_user)

    answer = await generate_room_answer(
        db,
        room_id,
        query
    )

    return {
        "answer": answer
    }

@router.get(
    "/{room_id}/memories/stale",
    response_model=List[RoomMemoryResponse]
)
async def get_stale(
    room_id: int,
    days_old: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await require_room_access(db, room_id, current_user)

    memories = await get_stale_memories(db, room_id, days_old)
    return memories

@router.post(
    "/{room_id}/memories/{memory_id}/reinforce",
    response_model=MemoryReinforceResponse
)
async def reinforce(
    room_id: int,
    memory_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await require_room_access(db, room_id, current_user)

    memory = await reinforce_memory(db, room_id, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"message": "Memory reinforced", "confidence_score": memory.confidence_score}


@router.patch(
    "/{room_id}/memories/{memory_id}",
    response_model=RoomMemoryResponse
)
async def edit_memory(
    room_id: int,
    memory_id: int,
    payload: RoomMemoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await require_room_access(db, room_id, current_user)

    content = payload.content.strip() if payload.content is not None else None
    if content == "":
        raise HTTPException(status_code=422, detail="Memory content cannot be empty")

    embedding = await generate_embedding(content) if content else None
    memory = await update_memory(
        db,
        room_id,
        memory_id,
        content=content,
        embedding=embedding,
        importance_score=payload.importance_score,
        tags=payload.tags,
    )
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    await db.commit()
    return memory

@router.delete(
    "/{room_id}/memories/{memory_id}",
    response_model=MessageOnlyResponse
)
async def delete_stale_memory(
    room_id: int,
    memory_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await require_room_access(db, room_id, current_user)

    success = await delete_memory(db, room_id, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"message": "Memory pruned successfully"}
