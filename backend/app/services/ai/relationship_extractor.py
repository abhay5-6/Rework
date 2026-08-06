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


async def extract_relationship(
    source_text: str,
    target_text: str
):
    if _is_test_mode() or not settings.ai_enabled:
        return None

    client = _get_client()

    prompt = f"""
Analyze the relationship between Memory A and Memory B.

Memory A: {source_text}
Memory B: {target_text}

Determine if there is a meaningful semantic relationship between them.
Types of relationships:
- relates_to (general connection)
- contradicts (opposing facts)
- updates (newer info superseding older info)
- depends_on (prerequisite)

Return ONLY valid JSON matching this schema:
{{
  "has_relationship": true/false,
  "relationship_type": "relates_to" | "contradicts" | "updates" | "depends_on",
  "confidence": 0.0 to 1.0
}}
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

        result = json.loads(raw_text.strip())
        if isinstance(result, dict) and result.get("has_relationship"):
            return result
        return None
    except Exception as exc:
        logger.warning("Failed to extract relationship from Gemini response", extra={"error": str(exc)})
        return None