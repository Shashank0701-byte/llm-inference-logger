"""Conversation CRUD endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/conversations")
async def list_conversations():
    """List all conversations."""
    # TODO: Implement
    return []


@router.post("/conversations")
async def create_conversation():
    """Create a new conversation."""
    # TODO: Implement
    return {"message": "not implemented"}


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a conversation with its messages."""
    # TODO: Implement
    return {"message": "not implemented"}


@router.patch("/conversations/{conversation_id}")
async def update_conversation(conversation_id: str):
    """Update conversation status (cancel/resume)."""
    # TODO: Implement
    return {"message": "not implemented"}
