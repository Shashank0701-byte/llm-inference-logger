"""Dashboard analytics endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard/metrics")
async def get_metrics():
    """Get latency, throughput, and error metrics."""
    # TODO: Implement
    return {"latency": {}, "throughput": {}, "errors": {}}


@router.get("/dashboard/logs")
async def get_recent_logs():
    """Get recent inference logs."""
    # TODO: Implement
    return []
