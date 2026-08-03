import logging

from sqlalchemy import select

from app.models.workspace_memory import (
    WorkspaceMemory
)

logger = logging.getLogger(__name__)


async def find_similar_memory(

    db,

    workspace_id: int,

    embedding: list[float],

    threshold: float = 0.92
):
    logger.debug("finding_similar_memory", extra={"workspace_id": workspace_id, "threshold": threshold})
    similarity_expr = (
        1 -
        WorkspaceMemory.embedding.cosine_distance(
            embedding
        )
    ).label(
        "similarity"
    )

    stmt = (

        select(
            WorkspaceMemory,
            similarity_expr
        )

        .where(
            WorkspaceMemory.workspace_id
            == workspace_id
        )

        .order_by(

            WorkspaceMemory.embedding.cosine_distance(
                embedding
            )
        )

        .limit(1)
    )

    result = await db.execute(
        stmt
    )

    row = result.first()

    if not row:
        return None

    memory, similarity = row

    if similarity is None:
        return None

    similarity = float(
        similarity
    )

    if similarity < threshold:
        return None

    logger.debug("similar_memory_found", extra={"workspace_id": workspace_id, "similarity": similarity})
    return memory