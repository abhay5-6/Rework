import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message

from app.services.ai.embedding_service import (
    generate_embedding
)

logger = logging.getLogger(__name__)


async def search_messages(
    db: AsyncSession,
    workspace_id: int,
    query: str,
    top_k: int = 10,
):

    logger.info(
        "message_search_started",
        extra={
            "workspace_id": workspace_id,
            "query": query,
        },
    )

    query_embedding = await generate_embedding(
        query
    )

    similarity_expr = (
        1
        - Message.embedding.cosine_distance(
            query_embedding
        )
    ).label(
        "similarity"
    )

    stmt = (
        select(
            Message,
            similarity_expr
        )
        .where(
            Message.workspace_id == workspace_id
        )
        .where(
            Message.embedding.is_not(
                None
            )
        )
        .order_by(
            Message.embedding.cosine_distance(
                query_embedding
            )
        )
        .limit(
            top_k * 3
        )
    )

    result = await db.execute(
        stmt
    )

    rows = result.all()

    messages = []

    for message, similarity in rows:

        if similarity is None:
            continue

        if similarity < 0.30:
            continue

        messages.append(
            {
                "type": "message",
                "id": message.id,
                "content": message.content,
                "created_at": message.created_at,
                "score": float(
                    similarity
                ),
            }
        )

    messages.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    logger.info(
        "message_search_finished",
        extra={
            "workspace_id": workspace_id,
            "results": len(
                messages
            ),
        },
    )

    return messages[:top_k]