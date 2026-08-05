import logging
from arq.connections import RedisSettings
from app.core.config import settings
from app.services.ai.auto_memory_service import process_memory_background

# Configure basic logging for the worker process
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def startup(ctx):
    """Run on worker startup"""
    logger.info("Worker starting up...")

async def shutdown(ctx):
    """Run on worker shutdown"""
    logger.info("Worker shutting down...")

async def run_process_memory_background(ctx, workspace_id: int, user_id: int, message_id: int, message_content: str):
    """Wrapper function to execute process_memory_background from ARQ context."""
    logger.info(f"Worker processing memory for workspace {workspace_id}, message {message_id}")
    try:
        await process_memory_background(workspace_id, user_id, message_id, message_content)
    except Exception as e:
        logger.error(f"Error in background task for message {message_id}: {e}")

# Parse REDIS_URL to get host and port for ARQ (e.g. redis://redis:6379/0)
# Simple parser, usually redis_url looks like redis://host:port/db
try:
    from urllib.parse import urlparse
    url = urlparse(settings.redis_url)
    redis_settings = RedisSettings(
        host=url.hostname or 'localhost',
        port=url.port or 6379,
        database=int(url.path.strip('/')) if url.path and url.path.strip('/') else 0,
        password=url.password
    )
except Exception:
    logger.warning("Failed to parse REDIS_URL for ARQ, falling back to defaults")
    redis_settings = RedisSettings()

class WorkerSettings:
    """
    ARQ settings for the worker.
    """
    functions = [run_process_memory_background]
    redis_settings = redis_settings
    on_startup = startup
    on_shutdown = shutdown
