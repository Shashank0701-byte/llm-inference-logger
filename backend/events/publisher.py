"""Publish events to Redis Streams."""

import json
from typing import Optional

import redis.asyncio as aioredis

from backend.config import settings


class EventPublisher:
    """Publishes structured events to Redis Streams."""

    STREAM = "inference_logs"

    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self._redis = redis_client

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    async def publish(self, event_type: str, payload: dict) -> str:
        """
        Publish a single event to the stream.

        Returns the stream message ID.
        """
        r = await self._get_redis()
        data = {
            "event_type": event_type,
            "payload": json.dumps(payload, default=str),
        }
        msg_id = await r.xadd(self.STREAM, data)
        return msg_id

    async def publish_batch(self, events: list[tuple[str, dict]]) -> list[str]:
        """Publish multiple events in a pipeline."""
        r = await self._get_redis()
        pipe = r.pipeline()
        for event_type, payload in events:
            data = {
                "event_type": event_type,
                "payload": json.dumps(payload, default=str),
            }
            pipe.xadd(self.STREAM, data)
        return await pipe.execute()

    async def close(self):
        if self._redis:
            await self._redis.close()


# Shared singleton
publisher = EventPublisher()
