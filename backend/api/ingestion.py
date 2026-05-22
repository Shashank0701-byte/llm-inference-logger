"""Log ingestion endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/ingest", status_code=202)
async def ingest_log():
    """Receive and process an inference log payload."""
    # TODO: Implement
    return {"status": "accepted"}
