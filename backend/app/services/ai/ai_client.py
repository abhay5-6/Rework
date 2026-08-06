import asyncio
import logging
import os
import sys
from typing import Any

from app.core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    settings
)
from app.services.ai.context_builder import (
    build_workspace_context
)

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


async def generate_workspace_answer(
    db,
    workspace_id: int,
    query: str,
) -> str:
    logger.debug(
        "generating_workspace_answer",
        extra={"workspace_id": workspace_id, "query": query},
    )

    if not settings.ai_enabled or _is_test_mode():
        return "AI features are currently unavailable or disabled in this environment."

    try:
        client = _get_client()
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

        async def _call_gemini():
            response = await client.aio.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            return response.text

        answer = await asyncio.wait_for(_call_gemini(), timeout=settings.ai_timeout_seconds)
        logger.debug("workspace_answer_generated", extra={"workspace_id": workspace_id})
        return answer
    except Exception as exc:
        logger.warning("AI workspace answer generation failed or timed out", extra={"error": str(exc)})
        return "AI assistant is currently offline or unreachable. Please try again later."


async def generate_web_search_answer(
    query: str,
) -> str:
    logger.debug("generating_web_search_answer", extra={"query": query})

    if not settings.ai_enabled or _is_test_mode():
        return "AI search features are currently unavailable or disabled in this environment."

    try:
        client = _get_client()
        prompt = f"""
You are Rework AI, a collaborative team assistant.
A user has asked you to perform a web search.

Use the provided Google Search tool to find up-to-date and accurate information.
Answer the user's query clearly and concisely based on your search results.
Include URLs or references if helpful.

USER QUERY:
{query}
"""

        async def _call_search():
            response = await client.aio.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={"tools": [{"google_search": {}}]}
            )
            return response.text

        answer = await asyncio.wait_for(_call_search(), timeout=settings.ai_timeout_seconds)
        logger.debug("web_search_answer_generated")
        return answer
    except Exception as exc:
        logger.warning("AI web search generation failed or timed out", extra={"error": str(exc)})
        return "AI web search is currently offline or unreachable. Please try again later."