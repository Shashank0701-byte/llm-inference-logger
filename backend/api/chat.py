"""Chat endpoints - REST + SSE streaming."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/chat")
async def send_message():
    """Send a message and get a response."""
    # TODO: Implement
    return {"message": "not implemented"}


@router.post("/chat/stream")
async def stream_message():
    """Send a message and stream the response via SSE."""
    # TODO: Implement
    return {"message": "not implemented"}
