import logging
import json
import asyncio
from typing import Callable, Awaitable
from redis import asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisPubSubManager:
    """
    Manages Redis Pub/Sub connections for WebSocket broadcasting across multiple instances.
    """
    def __init__(self):
        self.redis_url = settings.redis_url
        self.redis: aioredis.Redis | None = None
        self.pubsub: aioredis.client.PubSub | None = None
        self._listener_task: asyncio.Task | None = None
        self.channel_name = "workspace_events"

    async def connect(self):
        """Establish connection to Redis."""
        logger.info(f"Connecting to Redis at {self.redis_url}")
        try:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe(self.channel_name)
            logger.info("Successfully connected to Redis Pub/Sub")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}. Running without Redis Pub/Sub.")
            self.redis = None
            self.pubsub = None

    async def disconnect(self):
        """Close connection to Redis."""
        logger.info("Disconnecting from Redis")
        if self._listener_task:
            self._listener_task.cancel()
        if self.pubsub:
            await self.pubsub.unsubscribe(self.channel_name)
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()

    async def publish(self, workspace_id: int, message: dict):
        """Publish a message to the Redis channel."""
        if not self.redis:
            logger.warning("Redis is not connected. Cannot publish.")
            return
            
        payload = {
            "workspace_id": workspace_id,
            "message": message
        }
        try:
            await self.redis.publish(self.channel_name, json.dumps(payload))
        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")

    async def listen(self, callback: Callable[[int, dict], Awaitable[None]]):
        """Listen to the Redis channel and trigger the callback."""
        if not self.pubsub:
            logger.warning("Redis Pub/Sub is not connected. Not listening.")
            return
            
        logger.info(f"Started listening to Redis channel: {self.channel_name}")
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        workspace_id = data.get("workspace_id")
                        msg_payload = data.get("message")
                        
                        if workspace_id and msg_payload:
                            await callback(workspace_id, msg_payload)
                    except json.JSONDecodeError:
                        logger.error(f"Received invalid JSON from Redis: {message['data']}")
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
        except asyncio.CancelledError:
            logger.info("Redis listener task cancelled")
        except Exception as e:
            logger.error(f"Redis listener encountered an error: {e}")

redis_manager = RedisPubSubManager()
