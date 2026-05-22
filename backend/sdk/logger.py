"""
Async log publisher - sends inference logs to the event bus (Redis Streams).
"""

from backend.sdk.models import InferenceLog
from backend.events.publisher import publisher as event_publisher


class LogPublisher:
    """Publishes inference logs via the shared event publisher."""

    async def publish(self, log: InferenceLog) -> str:
        """
        Publish an inference log to the Redis Stream.

        Returns the stream message ID.
        """
        msg_id = await event_publisher.publish(
            event_type="inference_log",
            payload=log.model_dump(),
        )
        return msg_id

    async def publish_batch(self, logs: list[InferenceLog]) -> list[str]:
        """Publish multiple logs in a pipeline."""
        events = [("inference_log", log.model_dump()) for log in logs]
        return await event_publisher.publish_batch(events)
