import logging

from google import genai

from app.core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
)

from app.services.ai.context_builder import (
    build_workspace_context
)

client = genai.Client(
    api_key=GEMINI_API_KEY
)

logger = logging.getLogger(__name__)


async def generate_workspace_answer(
    db,
    workspace_id: int,
    query: str,
):
    logger.debug(
        "generating_workspace_answer",
        extra={"workspace_id": workspace_id, "query": query},
    )

    context = await build_workspace_context(
        db=db,
        workspace_id=workspace_id,
        query=query,
    )

    prompt = f"""
You are Rework AI.

Answer questions using the workspace memories,
retrieved messages, and workspace context.

If relevant information exists in memory,
use it.

If information comes from retrieved messages,
use it.

If context is incomplete, answer normally
and clearly indicate uncertainty.

WORKSPACE CONTEXT:

{context}

USER QUESTION:

{query}
"""

    response = await client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    answer = response.text

    logger.debug(
        "workspace_answer_generated",
        extra={"workspace_id": workspace_id},
    )

    return answer


async def generate_web_search_answer(
    query: str,
):
    logger.debug("generating_web_search_answer", extra={"query": query})

    prompt = f"""
You are Rework AI, a collaborative team assistant.
A user has asked you to perform a web search.

Use the provided Google Search tool to find up-to-date and accurate information.
Answer the user's query clearly and concisely based on your search results.
Include URLs or references if helpful.

USER QUERY:
{query}
"""

    response = await client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={"tools": [{"google_search": {}}]}
    )

    answer = response.text
    logger.debug("web_search_answer_generated")

    return answer