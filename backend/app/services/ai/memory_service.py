import logging
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from app.models.user import User
from app.repositories.memory_repository import memory_repo

logger = logging.getLogger(__name__)


async def create_workspace_memory(
    db: AsyncSession,
    workspace_id: int,
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
    """
    Creates a new memory for a workspace with associated embeddings and metadata.
    
    Args:
        db: Database session.
        workspace_id: ID of the workspace.
        created_by: ID of the user or AI creating the memory.
        content: The text content to store.
        embedding: Vector embedding of the content.
        memory_type: Type of memory (e.g., 'note', 'decision').
        source_type: The origin of the memory (e.g., 'message', 'document').
        source_id: The ID of the source entity, if applicable.
        importance_score: Integer score representing how crucial this memory is (1-5).
        tags: List of semantic tags.
        domain: Semantic domain of the memory.
        
    Returns:
        The newly created WorkspaceMemory object.
    """
    if tags is None:
        tags = []

    memory = await memory_repo.create(
        db,
        obj_in={
            "workspace_id": workspace_id,
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
    logger.info("Workspace memory created", extra={"memory_id": memory.id, "workspace_id": workspace_id, "created_by": created_by, "domain": domain})
    return memory


async def get_stale_memories(db: AsyncSession, workspace_id: int, days_old: int = 30):
    """
    Retrieves memories that have not been reinforced within a certain timeframe.
    
    Args:
        db: Database session.
        workspace_id: ID of the workspace.
        days_old: Threshold in days to consider a memory stale.
        
    Returns:
        A list of stale WorkspaceMemory objects.
    """
    threshold_date = (datetime.now(timezone.utc) - timedelta(days=days_old)).replace(tzinfo=None)
    memories = await memory_repo.get_stale_memories(db, workspace_id=workspace_id, threshold_date=threshold_date)
    logger.debug("Fetched stale memories", extra={"workspace_id": workspace_id, "count": len(memories)})
    return memories


async def get_workspace_memories(
    db: AsyncSession,
    workspace_id: int,
    limit: int = 20
):
    """
    Retrieves the most relevant memories for a workspace, including creator usernames.
    
    Args:
        db: Database session.
        workspace_id: ID of the workspace.
        limit: Maximum number of memories to fetch.
        
    Returns:
        A list of formatted dictionary representations of memories.
    """
    result = await memory_repo.get_memories_for_workspace_with_users(db, workspace_id=workspace_id, limit=limit)

    memories = []
    for memory, creator_username in result:
        memories.append({
            "id": memory.id,
            "workspace_id": memory.workspace_id,
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
    logger.debug("Fetched workspace memories", extra={"workspace_id": workspace_id, "count": len(memories)})
    return memories


async def reinforce_memory(
    db: AsyncSession,
    workspace_id: int,
    memory_id: int
):
    """
    Reinforces a memory by updating its last reinforced timestamp and bumping its confidence score.
    
    Args:
        db: Database session.
        workspace_id: ID of the workspace containing the memory.
        memory_id: ID of the memory to reinforce.
        
    Returns:
        The updated memory object, or None if not found.
    """
    memory = await memory_repo.get_memory_in_workspace(db, workspace_id=workspace_id, memory_id=memory_id)
    if memory:
        memory.last_reinforced_at = datetime.now(timezone.utc)
        memory.confidence_score = min(1.0, memory.confidence_score + 0.2)
        await db.commit()
        logger.info("Memory reinforced", extra={"memory_id": memory_id, "workspace_id": workspace_id, "new_score": memory.confidence_score})
    else:
        logger.warning("Attempted to reinforce non-existent memory", extra={"memory_id": memory_id, "workspace_id": workspace_id})
    return memory


async def update_memory(
    db: AsyncSession,
    workspace_id: int,
    memory_id: int,
    content: str | None = None,
    embedding: list[float] | None = None,
    importance_score: int | None = None,
    tags: list[str] | None = None,
):
    """
    Partially updates an existing memory's fields.
    
    Args:
        db: Database session.
        workspace_id: ID of the workspace.
        memory_id: ID of the memory.
        content: New content (if any).
        embedding: New vector embedding (if any).
        importance_score: New score (if any).
        tags: New list of tags (if any).
        
    Returns:
        The updated memory object, or None if not found.
    """
    memory = await memory_repo.get_memory_in_workspace(db, workspace_id=workspace_id, memory_id=memory_id)
    if not memory:
        logger.warning("Attempted to update non-existent memory", extra={"memory_id": memory_id, "workspace_id": workspace_id})
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
    logger.info("Memory updated", extra={"memory_id": memory_id, "workspace_id": workspace_id})
    return memory


async def delete_memory(
    db: AsyncSession,
    workspace_id: int,
    memory_id: int
):
    """
    Deletes a specific memory from a workspace.
    
    Args:
        db: Database session.
        workspace_id: ID of the workspace.
        memory_id: ID of the memory to delete.
        
    Returns:
        True if successfully deleted, False if the memory was not found.
    """
    memory = await memory_repo.get_memory_in_workspace(db, workspace_id=workspace_id, memory_id=memory_id)
    if memory:
        await memory_repo.remove(db, id=memory.id)
        logger.info("Memory deleted", extra={"memory_id": memory_id, "workspace_id": workspace_id})
        return True
    logger.warning("Attempted to delete non-existent memory", extra={"memory_id": memory_id, "workspace_id": workspace_id})
    return False
