"""Event handlers for processing inference logs."""

import json
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import crud

logger = logging.getLogger(__name__)


async def handle_inference_log(db: AsyncSession, payload: dict) -> None:
    """
    Process an inference log event and store it in the database.

    Args:
        db: Database session.
        payload: Parsed log payload dict.
    """
    try:
        # Convert conversation_id string to UUID if present
        conv_id = payload.get("conversation_id")
        if conv_id and isinstance(conv_id, str):
            conv_id = UUID(conv_id)

        await crud.create_inference_log(
            db,
            conversation_id=conv_id,
            session_id=payload.get("session_id", ""),
            model=payload.get("model", ""),
            provider=payload.get("provider", ""),
            latency_ms=payload.get("latency_ms", 0.0),
            input_tokens=payload.get("input_tokens", 0),
            output_tokens=payload.get("output_tokens", 0),
            total_tokens=payload.get("total_tokens", 0),
            status=payload.get("status", "success"),
            error_message=payload.get("error_message"),
            input_preview=payload.get("input_preview", ""),
            output_preview=payload.get("output_preview", ""),
            request_params=payload.get("request_params", {}),
            raw_metadata=payload.get("raw_metadata", {}),
        )
        logger.info("Stored inference log: model=%s status=%s", payload.get("model"), payload.get("status"))

    except Exception as e:
        logger.error("Failed to process inference log: %s", e, exc_info=True)
        raise


async def handle_error_log(db: AsyncSession, payload: dict) -> None:
    """Handle error-specific log events."""
    payload["status"] = "error"
    await handle_inference_log(db, payload)


# Handler registry
HANDLERS = {
    "inference_log": handle_inference_log,
    "error_log": handle_error_log,
}
