"""Log ingestion endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.engine import get_db
from backend.db.schemas import IngestPayload, InferenceLogOut
from backend.events.publisher import publisher

router = APIRouter()


@router.post("/ingest", status_code=202)
async def ingest_log(payload: IngestPayload):
    """
    Receive an inference log payload and publish it to the event bus.

    Returns 202 Accepted — processing happens asynchronously via the event worker.
    """
    await publisher.publish(
        event_type="inference_log",
        payload=payload.model_dump(),
    )
    return {"status": "accepted", "message": "Log queued for processing"}


@router.post("/ingest/batch", status_code=202)
async def ingest_batch(payloads: list[IngestPayload]):
    """Ingest multiple log entries at once."""
    if len(payloads) > 100:
        raise HTTPException(status_code=400, detail="Batch size cannot exceed 100")

    events = [("inference_log", p.model_dump()) for p in payloads]
    await publisher.publish_batch(events)
    return {"status": "accepted", "count": len(payloads)}
