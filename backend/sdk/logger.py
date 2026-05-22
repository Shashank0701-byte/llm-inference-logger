"""
Async log publisher - sends inference logs to the event bus (Redis Streams).
"""

import json
from typing import Optional

from backend.sdk.models import InferenceLog


class LogPublisher:
    """Publishes inference logs to Redis Streams for async processing."""

    def __init__(self, redis_client=None, stream_name: str = "inference_logs"):
        self._redis = redis_client
        self.stream_name = stream_name

    async def _get_redis(self):
        """Lazy-initialize Redis connection."""
        if self._redis is None:
            import redis.asyncio as aioredis
            from backend.config import settings
            self._redis = aioredis.from_url(settings.redis_url)
        return self._redis

    async def publish(self, log: InferenceLog) -> str:
        """
        Publish an inference log to the Redis Stream.

        Returns:
            The stream message ID.
        """
        r = await self._get_redis()
        data = {"payload": log.model_dump_json()}
        message_id = await r.xadd(self.stream_name, data)
        return message_id

    async def publish_batch(self, logs: list[InferenceLog]) -> list[str]:
        """Publish multiple logs in a pipeline for throughput."""
        r = await self._get_redis()
        pipe = r.pipeline()
        for log in logs:
            data = {"payload": log.model_dump_json()}
            pipe.xadd(self.stream_name, data)
        results = await pipe.execute()
        return results
