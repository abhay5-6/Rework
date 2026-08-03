from sqlalchemy import select

from app.models.memory_edge import (
    MemoryEdge
)

from app.models.workspace_memory import (
    WorkspaceMemory
)


async def apply_contradictions(

    db,

    source_memory
):

    result = await db.execute(

        select(MemoryEdge)

        .where(
            MemoryEdge.source_memory_id
            == source_memory.id
        )

        .where(
            MemoryEdge.relationship_type
            == "CONTRADICTS"
        )
    )

    contradiction_edges = (
        result.scalars().all()
    )

    for edge in contradiction_edges:

        memory_result = await db.execute(

            select(WorkspaceMemory)

            .where(
                WorkspaceMemory.id
                == edge.target_memory_id
            )
        )

        contradicted_memory = (
            memory_result
            .scalar_one_or_none()
        )

        if contradicted_memory:

            contradicted_memory.confidence_score *= 0.7

    await db.commit()