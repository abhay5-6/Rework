import logging

from google import genai

from app.core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
)

from app.services.ai.context_builder import (
    build_room_context
)

client = genai.Client(
    api_key=GEMINI_API_KEY
)

logger = logging.getLogger(__name__)


async def generate_room_answer(
    db,
    room_id: int,
    query: str,
):
    logger.debug(
        "generating_room_answer",
        extra={"room_id": room_id, "query": query},
    )

    context = await build_room_context(
        db=db,
        room_id=room_id,
        query=query,
    )

    prompt = f"""
You are Rework AI.

Answer questions using the room memories,
retrieved messages, and room context.

If relevant information exists in memory,
use it.

If information comes from retrieved messages,
use it.

If context is incomplete, answer normally
and clearly indicate uncertainty.

ROOM CONTEXT:

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
        "room_answer_generated",
        extra={"room_id": room_id},
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