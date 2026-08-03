import logging

from sqlalchemy.ext.asyncio import (
    AsyncSession
)

logger = logging.getLogger(__name__)

from app.services.ai.hybrid_retrieval_service import (
    retrieve_context
)


async def build_workspace_context(

    db: AsyncSession,

    workspace_id: int,

    query: str
):
    logger.debug(
        "building_workspace_context",
        extra={"workspace_id": workspace_id, "query": query},
    )

    retrieval_result = await retrieve_context(
        db=db,
        workspace_id=workspace_id,
        query=query,
        memory_limit=5,
        message_limit=10
    )

    messages = retrieval_result["messages"]
    memories = retrieval_result["memories"]

    logger.debug("context_retrieved", extra={"messages": len(messages), "memories": len(memories)})

    context_parts = []

    #
    # Relevant Messages
    #

    if messages:

        message_section = [
            "=== RELEVANT MESSAGES ==="
        ]

        for message in messages:

            formatted_message = f"""
Score:
{round(message["score"], 3)}

Message:
{message["content"]}
"""

            message_section.append(
                formatted_message
            )

        context_parts.append(
            "\n".join(
                message_section
            )
        )

    #
    # Relevant Memories
    #

    if memories:

        domain_groups = {}

        for memory in memories:

            domain = (
                memory.domain
                or "general"
            )

            if domain not in domain_groups:

                domain_groups[
                    domain
                ] = []

            domain_groups[
                domain
            ].append(
                memory
            )

        for (
            domain,
            domain_memories
        ) in domain_groups.items():

            section = [
                f"=== {domain.upper()} DOMAIN ==="
            ]

            for memory in domain_memories:

                tags = ", ".join(
                    memory.tags or []
                )

                formatted_memory = f"""
Memory Type:
{memory.memory_type}

Importance:
{memory.importance_score}

Times Referenced:
{memory.times_referenced}

Tags:
{tags}

Content:
{memory.content}
"""

                section.append(
                    formatted_memory
                )

            context_parts.append(
                "\n".join(section)
            )

    #
    # Empty Context
    #

    if not context_parts:

        return (
            "No relevant messages or memories found."
        )

    context = "\n---\n".join(
        context_parts
    )

    logger.debug(
        "context_built",
        extra={"sections": len(context_parts)},
    )

    return context