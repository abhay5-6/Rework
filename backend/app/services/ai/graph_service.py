import logging

from random import randint

from sqlalchemy import select

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from app.models.room_memory import (
    RoomMemory
)

from app.models.memory_edge import (
    MemoryEdge
)

logger = logging.getLogger(__name__)


async def build_room_graph(

    db: AsyncSession,

    room_id: int
):
    logger.debug("building_room_graph", extra={"room_id": room_id})

    memory_result = await db.execute(

        select(RoomMemory)

        .where(
            RoomMemory.room_id
            == room_id
        )
    )

    memories = (
        memory_result.scalars().all()
    )

    memory_ids = [
        memory.id
        for memory in memories
    ]

    edge_result = await db.execute(

        select(MemoryEdge)

        .where(
            MemoryEdge.source_memory_id.in_(
                memory_ids
            )
        )
    )

    relationships = (
        edge_result.scalars().all()
    )

    nodes = []

    edges = []

    for memory in memories:

        nodes.append({

            "id": f"memory_{memory.id}",

            "type": memory.memory_type,

            "data": {

                "label": (
                    memory.content[:80]
                ),

                "domain": memory.domain,

                "importance": (
                    memory.importance_score
                )
            },

            "position": {

                "x": randint(0, 1200),

                "y": randint(0, 800)
            }
        })

    for rel in relationships:

        edges.append({

            "id": f"edge_{rel.id}",

            "source": (
                f"memory_{rel.source_memory_id}"
            ),

            "target": (
                f"memory_{rel.target_memory_id}"
            ),

            "label": (
                rel.relationship_type
            )
        })

    return {

        "nodes": nodes,

        "edges": edges
    }