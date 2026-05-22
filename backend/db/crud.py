"""Database CRUD operations."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.db.models import Conversation, Message, InferenceLogRecord


# ── Conversations ──────────────────────────────────────────────

async def create_conversation(
    db: AsyncSession,
    title: str = "New Conversation",
    provider: str = "",
    model: str = "",
) -> Conversation:
    conv = Conversation(title=title, provider=provider, model=model)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


async def get_conversation(db: AsyncSession, conv_id: UUID) -> Optional[Conversation]:
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conv_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_conversations(
    db: AsyncSession, skip: int = 0, limit: int = 50
) -> list[Conversation]:
    stmt = (
        select(Conversation)
        .order_by(desc(Conversation.updated_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_conversation_status(
    db: AsyncSession, conv_id: UUID, status: str
) -> Optional[Conversation]:
    stmt = (
        update(Conversation)
        .where(Conversation.id == conv_id)
        .values(status=status, updated_at=datetime.utcnow())
        .returning(Conversation)
    )
    result = await db.execute(stmt)
    await db.commit()
    row = result.scalar_one_or_none()
    return row


# ── Messages ───────────────────────────────────────────────────

async def add_message(
    db: AsyncSession,
    conversation_id: UUID,
    role: str,
    content: str,
    token_count: int = 0,
) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        token_count=token_count,
    )
    db.add(msg)
    # Also bump conversation updated_at
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(updated_at=datetime.utcnow())
    )
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_recent_messages(
    db: AsyncSession, conversation_id: UUID, limit: int = 20
) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ── Inference Logs ─────────────────────────────────────────────

async def create_inference_log(db: AsyncSession, **kwargs) -> InferenceLogRecord:
    log = InferenceLogRecord(**kwargs)
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def get_recent_logs(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[InferenceLogRecord]:
    stmt = (
        select(InferenceLogRecord)
        .order_by(desc(InferenceLogRecord.created_at))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_dashboard_metrics(
    db: AsyncSession, hours: int = 24
) -> dict:
    """Aggregate metrics for the dashboard over the last N hours."""
    since = datetime.utcnow() - timedelta(hours=hours)
    base = select(InferenceLogRecord).where(InferenceLogRecord.created_at >= since)

    # Total counts
    count_stmt = select(
        func.count(InferenceLogRecord.id).label("total"),
        func.count(InferenceLogRecord.id).filter(InferenceLogRecord.status == "success").label("success"),
        func.count(InferenceLogRecord.id).filter(InferenceLogRecord.status == "error").label("errors"),
        func.coalesce(func.avg(InferenceLogRecord.latency_ms), 0).label("avg_latency"),
        func.coalesce(func.sum(InferenceLogRecord.total_tokens), 0).label("total_tokens"),
    ).where(InferenceLogRecord.created_at >= since)

    result = await db.execute(count_stmt)
    row = result.one()

    # Per-provider breakdown
    provider_stmt = (
        select(
            InferenceLogRecord.provider,
            func.count(InferenceLogRecord.id),
        )
        .where(InferenceLogRecord.created_at >= since)
        .group_by(InferenceLogRecord.provider)
    )
    provider_result = await db.execute(provider_stmt)
    by_provider = {r[0]: r[1] for r in provider_result.all()}

    # Per-model breakdown
    model_stmt = (
        select(
            InferenceLogRecord.model,
            func.count(InferenceLogRecord.id),
        )
        .where(InferenceLogRecord.created_at >= since)
        .group_by(InferenceLogRecord.model)
    )
    model_result = await db.execute(model_stmt)
    by_model = {r[0]: r[1] for r in model_result.all()}

    return {
        "total_requests": row.total,
        "success_count": row.success,
        "error_count": row.errors,
        "avg_latency_ms": round(float(row.avg_latency), 2),
        "total_tokens": int(row.total_tokens),
        "requests_by_provider": by_provider,
        "requests_by_model": by_model,
    }
