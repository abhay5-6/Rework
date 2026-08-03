import logging

from collections import deque

from sqlalchemy import select

from app.models.memory_edge import (
    MemoryEdge
)

from app.models.workspace_memory import (
    WorkspaceMemory
)

from app.services.ai.retrieval_service import (
    search_workspace_memories
)

logger = logging.getLogger(__name__)

RELATIONSHIP_WEIGHTS = {

    "DEPENDS_ON": 1.0,

    "IMPLEMENTS": 0.9,

    "EXTENDS": 0.8,

    "RELATED_TO": 0.5,

    "CONTRADICTS": 0.3
}


async def multi_hop_graph_retrieval(

    db,

    workspace_id: int,

    query: str,

    top_k: int = 5,

    max_depth: int = 2
):
    logger.debug("multi_hop_retrieval_started", extra={"workspace_id": workspace_id, "query": query})

    primary_memories = await (
        search_workspace_memories(

            db=db,

            workspace_id=workspace_id,

            query=query,

            top_k=top_k
        )
    )

    if not primary_memories:
        return []

    visited = set()

    collected_memories = []

    queue = deque()

    for memory in primary_memories:

        queue.append(
            (
                memory,
                0,
                1.0
            )
        )

        visited.add(memory.id)

        collected_memories.append(
            memory
        )

    while queue:

        current_memory, depth, current_score = (
            queue.popleft()
        )

        if depth >= max_depth:
            continue

        edge_result = await db.execute(

            select(MemoryEdge)

            .where(
                MemoryEdge.source_memory_id
                == current_memory.id
            )
        )

        edges = (
            edge_result.scalars().all()
        )

        for edge in edges:
            relationship_weight = (
                RELATIONSHIP_WEIGHTS.get(
                    edge.relationship_type,
                    0.4
                )
            )
            new_score = (
                current_score
                * relationship_weight
            )
            if new_score < 0.25:
                continue

            memory_result = (
                await db.execute(

                    select(WorkspaceMemory)

                    .where(
                        WorkspaceMemory.id
                        == edge.target_memory_id
                    )
                )
            )

            related_memory = (
                memory_result
                .scalar_one_or_none()
            )

            if (
                not related_memory
                or related_memory.id
                in visited
            ):
                continue

            visited.add(
                related_memory.id
            )

            collected_memories.append(
                related_memory
            )

            queue.append(
                (
                    related_memory,
                    depth + 1,
                    new_score
                )
            )

    return collected_memories