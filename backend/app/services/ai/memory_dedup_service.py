import logging

from sqlalchemy import select

from app.models.room_memory import (
    RoomMemory
)

logger = logging.getLogger(__name__)


async def find_similar_memory(

    db,

    room_id: int,

    embedding: list[float],

    threshold: float = 0.92
):
    logger.debug("finding_similar_memory", extra={"room_id": room_id, "threshold": threshold})
    similarity_expr = (
        1 -
        RoomMemory.embedding.cosine_distance(
            embedding
        )
    ).label(
        "similarity"
    )

    stmt = (

        select(
            RoomMemory,
            similarity_expr
        )

        .where(
            RoomMemory.room_id
            == room_id
        )

        .order_by(

            RoomMemory.embedding.cosine_distance(
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

    logger.debug("similar_memory_found", extra={"room_id": room_id, "similarity": similarity})
    return memory