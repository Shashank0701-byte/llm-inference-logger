"""Conversation CRUD endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.engine import get_db
from backend.db import crud
from backend.db.schemas import (
    ConversationCreate,
    ConversationUpdate,
    ConversationOut,
    ConversationDetail,
    MessageOut,
)

router = APIRouter()


@router.get("/conversations", response_model=list[ConversationOut])
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all conversations, newest first."""
    convs = await crud.list_conversations(db, skip=skip, limit=limit)
    results = []
    for c in convs:
        results.append(ConversationOut(
            id=c.id,
            title=c.title,
            status=c.status,
            provider=c.provider,
            model=c.model,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=len(c.messages) if hasattr(c, "messages") and c.messages else 0,
        ))
    return results


@router.post("/conversations", response_model=ConversationOut)
async def create_conversation(
    body: ConversationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation."""
    conv = await crud.create_conversation(
        db, title=body.title, provider=body.provider, model=body.model
    )
    return ConversationOut(
        id=conv.id,
        title=conv.title,
        status=conv.status,
        provider=conv.provider,
        model=conv.model,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=0,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with all its messages."""
    conv = await crud.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        status=conv.status,
        provider=conv.provider,
        model=conv.model,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=len(conv.messages),
        messages=[
            MessageOut(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                token_count=m.token_count,
                created_at=m.created_at,
            )
            for m in sorted(conv.messages, key=lambda m: m.created_at)
        ],
    )


@router.patch("/conversations/{conversation_id}", response_model=ConversationOut)
async def update_conversation(
    conversation_id: UUID,
    body: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a conversation — cancel or resume it."""
    conv = await crud.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if body.status:
        conv = await crud.update_conversation_status(db, conversation_id, body.status)

    return ConversationOut(
        id=conv.id,
        title=conv.title,
        status=conv.status,
        provider=conv.provider,
        model=conv.model,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
    )
