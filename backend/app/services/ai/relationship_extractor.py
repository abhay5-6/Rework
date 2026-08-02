import json
import logging

from google import genai

from app.core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
)

logger = logging.getLogger(__name__)

client = genai.Client(
    api_key=GEMINI_API_KEY
)


async def extract_relationship(

    source_text: str,

    target_text: str
):

    logger.debug(
        "extracting_relationship",
        extra={"source_len": len(source_text), "target_len": len(target_text)},
    )

    prompt = f"""
You are a memory relationship analyzer.

Determine whether two memories are related.

Possible relationships:

- RELATED_TO
- DEPENDS_ON
- CONTRADICTS
- IMPLEMENTS
- NONE

Respond ONLY in JSON:

{{
    "relationship": "RELATED_TO"
}}

Memory A:
{source_text}

Memory B:
{target_text}
"""

    try:

        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        raw_response = response.text.strip()

        parsed = json.loads(
            raw_response
        )

        relationship = parsed.get(
            "relationship"
        )

        if (
            not relationship or
            relationship == "NONE"
        ):
            return None

        logger.debug(
            "relationship_extracted",
            extra={"relationship": relationship},
        )

        return relationship

    except json.JSONDecodeError:

        logger.warning(
            "relationship_invalid_json"
        )

        return None

    except Exception:

        logger.exception(
            "relationship_extraction_failed"
        )

        return None