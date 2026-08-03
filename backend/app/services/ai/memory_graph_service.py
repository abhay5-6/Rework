import logging

from sqlalchemy import select

from app.models.workspace_memory import (
    WorkspaceMemory
)

from app.models.memory_edge import (
    MemoryEdge
)

from app.services.ai.relationship_extractor import (
    extract_relationship
)

logger = logging.getLogger(__name__)


async def build_memory_relationships(

    db,

    new_memory
):
    logger.debug("building_relationships", extra={"memory_id": new_memory.id, "workspace_id": new_memory.workspace_id})

    result = await db.execute(

        select(WorkspaceMemory)

        .where(
            WorkspaceMemory.workspace_id
            == new_memory.workspace_id
        )
    )

    memories = result.scalars().all()

    for memory in memories:

        if memory.id == new_memory.id:
            continue

        relationship = await (
            extract_relationship(

                new_memory.content,

                memory.content
            )
        )

        if not relationship:
            continue

        edge = MemoryEdge(

            source_memory_id=
                new_memory.id,

            target_memory_id=
                memory.id,

            relationship_type=
                relationship
        )

        db.add(edge)

    await db.flush()
    logger.debug("relationships_built", extra={"memory_id": new_memory.id})
