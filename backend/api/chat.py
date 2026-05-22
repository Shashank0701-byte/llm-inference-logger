"""Chat endpoints - REST + SSE streaming."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db.engine import get_db
from backend.db import crud
from backend.db.schemas import ChatRequest, ChatResponse
from backend.sdk.client import InferenceClient

router = APIRouter()

# Shared inference client
_client = InferenceClient()


def _resolve_model(requested_model: str) -> str:
    """Pick the model to use — requested or default."""
    return requested_model if requested_model else settings.default_model


async def _get_or_create_conversation(
    db: AsyncSession,
    conversation_id: Optional[UUID],
    model: str,
    provider: str,
):
    """Fetch existing conversation or create a new one."""
    if conversation_id:
        conv = await crud.get_conversation(db, conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conv.status == "cancelled":
            raise HTTPException(status_code=400, detail="Conversation is cancelled")
        return conv
    return await crud.create_conversation(db, provider=provider, model=model)


async def _build_messages(db: AsyncSession, conversation_id: UUID) -> list[dict]:
    """Build the message list for the LLM from conversation history."""
    recent = await crud.get_recent_messages(
        db, conversation_id, limit=settings.context_window_size
    )
    return [{"role": m.role, "content": m.content} for m in recent]


@router.post("/chat", response_model=ChatResponse)
async def send_message(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send a message and get a complete response."""
    model = _resolve_model(req.model)

    conv = await _get_or_create_conversation(db, req.conversation_id, model, req.provider)

    # Save user message
    await crud.add_message(db, conv.id, role="user", content=req.message)

    # Build context
    messages = await _build_messages(db, conv.id)

    # Call LLM via SDK
    result = await _client.complete(
        messages=messages,
        model=model,
        conversation_id=str(conv.id),
    )

    # Save assistant message
    await crud.add_message(
        db, conv.id,
        role="assistant",
        content=result.content,
        token_count=result.output_tokens,
    )

    return ChatResponse(
        content=result.content,
        conversation_id=conv.id,
        model=result.model,
        provider=result.provider,
        latency_ms=result.latency_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )


@router.post("/chat/stream")
async def stream_message(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Send a message and stream the response via SSE."""
    model = _resolve_model(req.model)

    conv = await _get_or_create_conversation(db, req.conversation_id, model, req.provider)

    # Save user message
    await crud.add_message(db, conv.id, role="user", content=req.message)

    # Build context
    messages = await _build_messages(db, conv.id)

    async def event_stream():
        full_content = ""
        async for chunk in _client.stream(
            messages=messages,
            model=model,
            conversation_id=str(conv.id),
        ):
            full_content += chunk
            yield f"data: {chunk}\n\n"

        # Save the complete assistant message after streaming ends
        await crud.add_message(db, conv.id, role="assistant", content=full_content)

        # Send done signal
        yield f"data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/models")
async def list_available_models():
    """List available providers and their models."""
    available = {}
    if settings.openai_api_key:
        available["openai"] = ["gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "o4-mini"]
    if settings.anthropic_api_key:
        available["anthropic"] = ["claude-sonnet-4-20250514", "claude-haiku-4-20250514"]
    if settings.google_api_key:
        available["google"] = ["gemini/gemini-2.5-flash", "gemini/gemini-2.5-pro"]
    if settings.deepseek_api_key:
        available["deepseek"] = ["deepseek/deepseek-chat", "deepseek/deepseek-reasoner"]
    return {"providers": available}
