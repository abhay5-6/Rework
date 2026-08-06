import asyncio
import logging
import os
import sys
from functools import partial
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_model_instance: Any = None
_model_lock = asyncio.Lock()


def _is_test_mode() -> bool:
    """Checks whether the application is running in automated test mode."""
    return (
        settings.ai_test_mode
        or os.getenv("AI_TEST_MODE", "").lower() in ("true", "1", "yes")
        or "pytest" in sys.modules
    )


async def _get_embedding_model():
    """Lazily loads the SentenceTransformer embedding model on-demand."""
    global _model_instance
    if _model_instance is not None:
        return _model_instance

    async with _model_lock:
        if _model_instance is None:
            logger.info("Lazy loading SentenceTransformer('all-MiniLM-L6-v2') embedding model")
            from sentence_transformers import SentenceTransformer
            loop = asyncio.get_running_loop()
            _model_instance = await loop.run_in_executor(
                None,
                lambda: SentenceTransformer("all-MiniLM-L6-v2")
            )
    return _model_instance


async def generate_embedding(text: str) -> list[float]:
    """
    Generates vector embedding for text content.
    Returns deterministic mock vector in test mode or when AI is disabled.
    
    Args:
        text: Input text string.
        
    Returns:
        List of float embedding dimensions.
    """
    if not settings.ai_enabled or _is_test_mode():
        logger.debug("Test mode or AI disabled: returning mock embedding stub")
        return [0.0] * settings.embedding_dimension

    logger.info("embedding_generation_started")
    try:
        model = await _get_embedding_model()
        loop = asyncio.get_running_loop()
        
        async def _encode():
            return await loop.run_in_executor(None, partial(model.encode, text))

        raw_embedding = await asyncio.wait_for(_encode(), timeout=settings.ai_timeout_seconds)
        embedding = raw_embedding.tolist()
        logger.info("embedding_generation_finished", extra={"dimensions": len(embedding)})
        return embedding
    except (asyncio.TimeoutError, Exception) as exc:
        logger.warning(
            "Embedding generation failed or timed out, returning fallback mock vector",
            extra={"error": str(exc)}
        )
        return [0.0] * settings.embedding_dimension