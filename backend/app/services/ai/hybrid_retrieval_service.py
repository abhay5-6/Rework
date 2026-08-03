from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai.retrieval_service import (
    search_workspace_memories
)

from app.services.ai.message_retrieval_service import (
    search_messages
)


async def retrieve_context(
    db: AsyncSession,
    workspace_id: int,
    query: str,
    memory_limit: int = 5,
    message_limit: int = 10,
):

    memories = await search_workspace_memories(
        db=db,
        workspace_id=workspace_id,
        query=query,
        top_k=memory_limit,
    )

    messages = await search_messages(
        db=db,
        workspace_id=workspace_id,
        query=query,
        top_k=message_limit,
    )

    return {
        "messages": messages,
        "memories": memories,
    }