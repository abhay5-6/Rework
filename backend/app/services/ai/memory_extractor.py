import json
import logging
import os
import sys
from typing import Any

from app.core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    settings
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


async def extract_memory_from_text(
    text: str
):
    if _is_test_mode() or not settings.ai_enabled:
        return []

    client = _get_client()

    prompt = f"""
Extract reusable long-term knowledge from this message.

Create a memory whenever the message contains ANY potentially useful future information, including:

- decisions
- plans
- goals
- facts
- preferences
- agreements
- requirements
- project knowledge
- architecture choices

DO NOT create memories for:
- general chit chat ("hey", "thanks")
- ephemeral status ("BRB", "done with lunch")
- temporary coordination ("are you there?")

FORMAT REQUIREMENT:
Return ONLY valid JSON matching this schema:
[
  {{
    "content": "clear standalone statement of fact",
    "importance": 1-5,
    "tags": ["tag1", "tag2"]
  }}
]

Message text:
{text}
"""

    response = await client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    try:
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        memories = json.loads(raw_text.strip())
        if isinstance(memories, list):
            return memories
        return []
    except Exception as exc:
        logger.warning("Failed to parse extracted memories from Gemini output", extra={"error": str(exc)})
        return []