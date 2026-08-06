import logging
import os
import sys
from typing import Any

from app.core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_EMBEDDING_MODEL,
    settings
)
from app.services.ai.retrieval_service import search_workspace_memories
from app.services.ai.memory_service import create_workspace_memory
from app.services.ai.embedding_service import generate_embedding

logger = logging.getLogger(__name__)

_genai_client: Any = None


def _is_test_mode() -> bool:
    return (
        settings.ai_test_mode
        or os.getenv("AI_TEST_MODE", "").lower() in ("true", "1", "yes")
        or "pytest" in sys.modules
    )


def _get_client():
    global _genai_client
    if _genai_client is not None:
        return _genai_client
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY environment variable is not configured")
    from google import genai
    _genai_client = genai.Client(api_key=GEMINI_API_KEY)
    return _genai_client


async def generate_memory_summary(
    db,
    workspace_id: int,
    topic_query: str,
    created_by: int
):
    if _is_test_mode() or not settings.ai_enabled:
        return "AI memory summary is disabled or unavailable in test environment."

    client = _get_client()

    relevant_memories = await search_workspace_memories(
        db,
        workspace_id=workspace_id,
        query_text=topic_query,
        limit=5
    )

    if not relevant_memories:
        return None

    context = "\n".join([f"- {m['content']}" for m in relevant_memories])

    prompt = f"""
Summarize the following workspace memories related to "{topic_query}":

{context}

Provide a concise, clear summary.
"""

    response = await client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    summary_text = response.text

    summary_memory = await create_workspace_memory(
        db,
        workspace_id=workspace_id,
        content=f"Summary for '{topic_query}': {summary_text}",
        created_by=created_by,
        source_message_id=None,
        importance_score=4,
        tags=["summary", topic_query]
    )

    return summary_memory