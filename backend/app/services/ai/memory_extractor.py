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


async def extract_memory_from_text(
    text: str
):

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
- technical discussions
- bugs
- fixes
- learnings
- progress updates
- meeting notes
- recurring interests
- implementation details

Return ONLY valid JSON or null.

Schema:

{{
  "memory_type": "knowledge",
  "domain": "general",
  "importance_score": 3,
  "tags": [],
  "content": "memory text",
  "assignee": null
}}

If the message describes an action item or a to-do, set memory_type to "task" and if a person is mentioned to do it, set "assignee" to their name (otherwise null).

Allowed memory_type values:

- knowledge
- decision
- task
- goal
- plan
- bug
- fix
- requirement
- preference
- architecture
- learning
- fact
- meeting_note

Allowed domain values:

- general
- backend
- frontend
- database
- ai
- authentication
- deployment
- devops
- testing
- product
- business

Rules:

- importance_score must be integer 1-5
- preserve important context
- content should be concise but complete
- tags must be an array of strings
- do not nest objects
- do not explain anything
- output only JSON or null
- if the message contains any reusable future information, create a memory

Message:

{text}
"""

    logger.info(
        "memory_extractor_started"
    )

    try:

        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        raw_response = response.text.strip()

        raw_response = (
            raw_response
            .replace("```json", "")
            .replace("```", "")
            .strip()
        )

        logger.debug(
            "raw_memory_response",
            extra={"response": raw_response},
        )

        if (
            raw_response.lower()
            == "null"
        ):
            return None

        parsed = json.loads(
            raw_response
        )

        parsed.setdefault(
            "memory_type",
            "knowledge"
        )

        parsed.setdefault(
            "domain",
            "general"
        )

        parsed.setdefault(
            "importance_score",
            3
        )

        parsed.setdefault(
            "tags",
            []
        )

        parsed.setdefault(
            "content",
            ""
        )
        
        parsed.setdefault(
            "assignee",
            None
        )

        try:
            parsed["importance_score"] = int(
                parsed["importance_score"]
            )
        except Exception:
            parsed["importance_score"] = 3

        parsed["importance_score"] = max(
            1,
            min(
                5,
                parsed["importance_score"]
            )
        )

        parsed["content"] = str(
            parsed["content"]
        ).strip()

        if not isinstance(
            parsed["tags"],
            list
        ):
            parsed["tags"] = []

        if not parsed["content"]:
            return None

        logger.info(
            "memory_extractor_finished"
        )

        return parsed

    except json.JSONDecodeError:

        logger.warning(
            "memory_extractor_invalid_json"
        )

        return None

    except Exception:

        logger.exception(
            "memory_extraction_failed"
        )

        return None