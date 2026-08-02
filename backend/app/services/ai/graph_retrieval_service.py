import logging

from sqlalchemy import select

from app.models.memory_edge import (
    MemoryEdge
)

from app.models.room_memory import (
    RoomMemory
)

from app.services.ai.retrieval_service import (
    search_room_memories
)

logger = logging.getLogger(__name__)


async def graph_enhanced_retrieval(

    db,

    room_id: int,

    query: str,

    top_k: int = 5
):
    logger.debug("graph_enhanced_retrieval_started", extra={"room_id": room_id, "query": query})
    primary_memories = await (
        search_room_memories(

            db,

            room_id,

            query,

            top_k
        )
    )

    related_memories = []

    seen_memory_ids = set()

    for memory in primary_memories:

        seen_memory_ids.add(
            memory.id
        )

        result = await db.execute(

            select(MemoryEdge)

            .where(
                MemoryEdge.source_memory_id
                == memory.id
            )
        )

        edges = (
            result.scalars().all()
        )

        for edge in edges:

            related_result = (
                await db.execute(

                    select(RoomMemory)

                    .where(
                        RoomMemory.id
                        == edge.target_memory_id
                    )
                )
            )

            related_memory = (
                related_result
                .scalar_one_or_none()
            )

            if (
                related_memory
                and related_memory.id
                not in seen_memory_ids
            ):

                related_memories.append(
                    related_memory
                )

                seen_memory_ids.add(
                    related_memory.id
                )

    return (
        primary_memories
        + related_memories
    )