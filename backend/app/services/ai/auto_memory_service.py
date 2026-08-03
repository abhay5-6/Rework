from datetime import datetime, timezone
import logging

from app.db.session import AsyncSessionLocal

from app.models.message import Message

from app.services.ai.embedding_service import (
    generate_embedding
)

from app.services.ai.memory_extractor import (
    extract_memory_from_text
)

from app.services.ai.memory_service import (
    create_workspace_memory
)

from app.services.ai.memory_dedup_service import (
    find_similar_memory
)

from app.services.ai.memory_graph_service import (
    build_memory_relationships
)

from app.models.workspace_memory import WorkspaceMemory
from app.models.memory_edge import MemoryEdge
from app.models.workspace_task import WorkspaceTask
from app.websocket.manager import manager

from app.core.config import (
    MEMORY_MAX_CONTENT_LENGTH,
    MEMORY_MIN_CONTENT_LENGTH,
    MEMORY_MIN_IMPORTANCE_SCORE,
)

logger = logging.getLogger(__name__)


async def process_message_for_memory(
    db,
    workspace_id: int,
    user_id: int,
    message_id: int,
    message_content: str,
    extra_data: dict = None,
):
    logger.info(
        "message_ingestion_started",
        extra={
            "workspace_id": workspace_id,
            "user_id": user_id,
            "message_id": message_id,
        },
    )

    if not message_content and not extra_data:
        return None

    extra_data = extra_data or {}
    ai_parse = extra_data.get("ai_parse", False)
    file_url = extra_data.get("file_url")

    if file_url and ai_parse:
        file_name = extra_data.get("file_name", file_url)
        message_content += f"\n\n[Attached File: {file_name}]"

    # STEP 1 - Embed and persist message

    message_embedding = await generate_embedding(
        message_content
    )

    logger.debug(
        "message_embedding_generated",
        extra={"message_id": message_id, "dims": len(message_embedding)},
    )

    message = await db.get(
        Message,
        message_id
    )

    if message:
        message.embedding = message_embedding

        await db.flush()

        logger.debug(
            "message_embedding_saved",
            extra={
                "message_id": message_id,
            },
        )
        logger.debug(
            "message_embedding_persisted",
            extra={"message_id": message_id},
        )

    # STEP 2 - Extract memory candidate

    result = await extract_memory_from_text(
        message_content
    )

    logger.debug(
        "memory_extraction_result",
        extra={"message_id": message_id, "result": result},
    )

    if not result:
        logger.debug("no_memory_extracted", extra={"message_id": message_id})
        return None

    content = str(
        result.get(
            "content",
            "",
        )
    ).strip()

    importance_score = int(
        result.get(
            "importance_score",
            1,
        )
    )

    if (
        len(content)
        < MEMORY_MIN_CONTENT_LENGTH
    ):
        return None

    if (
        len(content)
        > MEMORY_MAX_CONTENT_LENGTH
    ):
        return None

    if (
        importance_score
        < MEMORY_MIN_IMPORTANCE_SCORE
    ):
        return None

    # STEP 3 - Generate memory embedding

    embedding = await generate_embedding(
        content
    )

    logger.debug(
        "memory_embedding_generated",
        extra={"message_id": message_id, "dims": len(embedding)},
    )

    # STEP 4 - Deduplication / reinforcement

    similar_memory = await find_similar_memory(
        db=db,
        workspace_id=workspace_id,
        embedding=embedding,
    )

    logger.debug(
        "dedup_check_complete",
        extra={"message_id": message_id, "has_similar": similar_memory is not None},
    )

    if similar_memory:

        similar_memory.times_referenced += 1

        similar_memory.importance_score += 1

        similar_memory.last_reinforced_at = (
            datetime.now(timezone.utc)
        )

        await db.flush()

        logger.info(
            "memory_reinforced",
            extra={
                "workspace_id": workspace_id,
                "memory_id": similar_memory.id,
                "message_id": message_id,
            },
        )

        logger.debug(
            "memory_reinforced_returning",
            extra={"memory_id": similar_memory.id},
        )
        return similar_memory

    # STEP 5 - Create new memory

    memory = await create_workspace_memory(
        db=db,
        workspace_id=workspace_id,
        created_by=user_id,
        content=content,
        memory_type=result.get(
            "memory_type",
            "note",
        ),
        source_type="message",
        source_id=message_id,
        embedding=embedding,
        importance_score=importance_score,
        tags=result.get(
            "tags",
            [],
        ),
        domain=result.get(
            "domain",
            "general",
        ),
    )

    logger.debug(
        "new_memory_created",
        extra={"memory_id": memory.id, "workspace_id": workspace_id},
    )

    if memory.memory_type == "task":
        task = WorkspaceTask(
            workspace_id=workspace_id,
            description=content,
            assignee_username=result.get("assignee")
        )
        db.add(task)
        await db.flush()
        logger.debug(
            "task_extracted_from_memory",
            extra={"task_id": task.id, "workspace_id": workspace_id},
        )
        
        # Broadcast the new task to the workspace
        await manager.broadcast(
            workspace_id,
            {
                "type": "task_created",
                "data": {
                    "id": task.id,
                    "description": task.description,
                    "assignee_username": task.assignee_username,
                    "status": task.status,
                    "created_at": task.created_at.isoformat() if task.created_at else None
                }
            }
        )


    # STEP 6 - Build graph relationships

    await build_memory_relationships(
        db=db,
        new_memory=memory,
    )

    logger.info(
        "memory_created",
        extra={
            "workspace_id": workspace_id,
            "memory_id": memory.id,
            "message_id": message_id,
        },
    )

    logger.debug(
        "graph_relationships_built",
        extra={"memory_id": memory.id, "workspace_id": workspace_id},
    )

    return memory

async def process_memory_background(
    workspace_id: int,
    user_id: int,
    message_id: int,
    content: str,
    extra_data: dict = None
):
    logger.debug(
        "background_memory_task_started",
        extra={"workspace_id": workspace_id, "user_id": user_id, "message_id": message_id},
    )

    async with AsyncSessionLocal() as db:

        try:

            async with db.begin():

                await process_message_for_memory(
                    db=db,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    message_id=message_id,
                    message_content=content,
                    extra_data=extra_data,
                )

            logger.debug(
                "background_memory_task_completed",
                extra={"workspace_id": workspace_id, "message_id": message_id},
            )

        except Exception as e:

            logger.error(
                "background_memory_task_failed",
                extra={"workspace_id": workspace_id, "error": str(e)},
            )

            logger.exception(
                "background_memory_processing_failed",
                extra={
                    "workspace_id": workspace_id,
                    "user_id": user_id,
                    "message_id": message_id,
                },
            )