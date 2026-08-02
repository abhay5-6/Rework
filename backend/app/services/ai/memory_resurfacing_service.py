import logging

logger = logging.getLogger(__name__)


def calculate_resurfacing_boost(

    similarity,

    memory
):
    logger.debug(
        "calculating_resurfacing_boost",
        extra={"memory_id": memory.id, "similarity": similarity},
    )

    if similarity < 0.8:
        return 1.0

    if memory.importance_score >= 4:

        return 1.3

    if memory.access_count >= 10:

        return 1.2

    return 1.0
