import logging

from datetime import (
    datetime,
    timezone,
)

logger = logging.getLogger(__name__)


def calculate_decay_factor(
    memory
):
    logger.debug(
        "calculating_decay_factor",
        extra={"memory_id": memory.id},
    )

    days_since_access = (

        datetime.now(timezone.utc)

        -

        memory.last_accessed_at
    ).days

    decay = max(

        0.3,

        1.0 - (
            days_since_access
            * 0.01
        )
    )

    return decay