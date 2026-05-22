"""
Consume events from Redis Streams and process them.

Runs as a standalone worker process or as a background task in FastAPI.
Uses Redis consumer groups for reliable, at-least-once delivery.
"""

import asyncio
import json
import logging
import sys

import redis.asyncio as aioredis

from backend.config import settings
from backend.db.engine import async_session
from backend.events.handlers import HANDLERS

logger = logging.getLogger(__name__)

STREAM = "inference_logs"
GROUP = "log_processors"
CONSUMER = "worker-1"
MAX_RETRIES = 3


async def ensure_consumer_group(r: aioredis.Redis) -> None:
    """Create the consumer group if it doesn't exist."""
    try:
        await r.xgroup_create(STREAM, GROUP, id="0", mkstream=True)
        logger.info("Created consumer group '%s' on stream '%s'", GROUP, STREAM)
    except aioredis.ResponseError as e:
        if "BUSYGROUP" in str(e):
            pass  # Group already exists
        else:
            raise


async def process_message(msg_id: str, data: dict) -> bool:
    """
    Process a single stream message.

    Returns True if processed successfully, False otherwise.
    """
    event_type = data.get("event_type", "inference_log")
    payload_str = data.get("payload", "{}")

    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in message %s", msg_id)
        return False

    handler = HANDLERS.get(event_type)
    if not handler:
        logger.warning("No handler for event_type='%s', skipping", event_type)
        return True  # Ack it so we don't reprocess

    async with async_session() as db:
        await handler(db, payload)

    return True


async def consume(block_ms: int = 5000) -> None:
    """
    Main consumer loop. Reads from the Redis Stream using consumer groups,
    processes messages, and acknowledges them.
    """
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    await ensure_consumer_group(r)

    logger.info("Consumer started. Listening on stream '%s'...", STREAM)

    try:
        while True:
            # Read new messages for this consumer
            messages = await r.xreadgroup(
                GROUP, CONSUMER,
                {STREAM: ">"},
                count=10,
                block=block_ms,
            )

            if not messages:
                continue

            for stream_name, entries in messages:
                for msg_id, data in entries:
                    try:
                        success = await process_message(msg_id, data)
                        if success:
                            await r.xack(STREAM, GROUP, msg_id)
                        else:
                            logger.warning("Message %s failed, will be retried", msg_id)
                    except Exception as e:
                        logger.error("Error processing %s: %s", msg_id, e, exc_info=True)

    except asyncio.CancelledError:
        logger.info("Consumer shutting down...")
    finally:
        await r.close()


# Entry point for running as a standalone worker: python -m backend.events.consumer
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(consume())
