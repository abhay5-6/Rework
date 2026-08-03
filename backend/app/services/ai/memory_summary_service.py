import logging

from google import genai

from app.core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_EMBEDDING_MODEL
)

from app.services.ai.retrieval_service import (
    search_workspace_memories
)

from app.services.ai.memory_service import (
    create_workspace_memory
)

from app.services.ai.embedding_service import (
    generate_embedding
)

client = genai.Client(
    api_key=GEMINI_API_KEY
)

logger = logging.getLogger(__name__)


async def generate_memory_summary(

    db,

    workspace_id: int,

    topic_query: str,

    created_by: int
):

    logger.debug(
        "generating_memory_summary",
        extra={"workspace_id": workspace_id, "topic_query": topic_query},
    )

    memories = await (
        search_workspace_memories(

            db=db,

            workspace_id=workspace_id,

            query=topic_query,

            top_k=10
        )
    )

    if not memories:
        return None

    memory_text = "\n".join(

        [
            f"- {memory.content}"
            for memory in memories
        ]
    )

    prompt = f"""
You are an AI project memory summarizer.

Summarize the following memories into:

- key decisions
- architecture choices
- implementation conventions
- important conclusions

Keep summary concise but information-dense.

Memories:
{memory_text}
"""

    response = await client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    summary = response.text.strip()

    summary_embedding = await (
        generate_embedding(
            summary
        )
    )

    stored_summary = await (
        create_workspace_memory(

            db=db,

            workspace_id=workspace_id,

            created_by=created_by,

            content=summary,

            embedding=summary_embedding,

            memory_type="summary",

            importance_score=5,

            tags=[
                "summary",
                topic_query
            ]
        )
    )

    await db.commit()

    logger.debug(
        "memory_summary_stored",
        extra={"memory_id": stored_summary.id, "workspace_id": workspace_id},
    )

    return {
        "summary": summary,
        "stored_memory_id":
            stored_summary.id
    }