"""Dashboard analytics endpoints."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.engine import get_db
from backend.db.models import InferenceLogRecord
from backend.db import crud
from backend.db.schemas import (
    MetricsOut,
    TimeseriesPoint,
    DashboardOut,
    InferenceLogOut,
)

router = APIRouter()


@router.get("/dashboard/metrics", response_model=MetricsOut)
async def get_metrics(
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregate metrics over the last N hours."""
    data = await crud.get_dashboard_metrics(db, hours=hours)
    return MetricsOut(**data)


@router.get("/dashboard/timeseries")
async def get_timeseries(
    hours: int = Query(24, ge=1, le=720),
    bucket_minutes: int = Query(15, ge=1, le=60),
    db: AsyncSession = Depends(get_db),
):
    """
    Get latency, throughput, and error rate timeseries.

    Data is bucketed into intervals of `bucket_minutes`.
    """
    since = datetime.utcnow() - timedelta(hours=hours)

    # Fetch all logs in the window
    stmt = (
        select(InferenceLogRecord)
        .where(InferenceLogRecord.created_at >= since)
        .order_by(InferenceLogRecord.created_at)
    )
    result = await db.execute(stmt)
    logs = list(result.scalars().all())

    # Bucket logs into time intervals
    latency_series = []
    throughput_series = []
    error_series = []

    if not logs:
        return {
            "latency_series": [],
            "throughput_series": [],
            "error_series": [],
        }

    # Build buckets
    bucket_delta = timedelta(minutes=bucket_minutes)
    current_bucket = since
    end_time = datetime.utcnow()

    while current_bucket < end_time:
        bucket_end = current_bucket + bucket_delta
        bucket_label = current_bucket.strftime("%Y-%m-%d %H:%M")

        bucket_logs = [
            l for l in logs
            if current_bucket <= l.created_at < bucket_end
        ]

        count = len(bucket_logs)
        errors = sum(1 for l in bucket_logs if l.status == "error")
        avg_latency = (
            sum(l.latency_ms for l in bucket_logs) / count
            if count > 0
            else 0.0
        )

        latency_series.append(TimeseriesPoint(
            timestamp=bucket_label, value=round(avg_latency, 2)
        ))
        throughput_series.append(TimeseriesPoint(
            timestamp=bucket_label, value=count
        ))
        error_series.append(TimeseriesPoint(
            timestamp=bucket_label, value=errors
        ))

        current_bucket = bucket_end

    return {
        "latency_series": latency_series,
        "throughput_series": throughput_series,
        "error_series": error_series,
    }


@router.get("/dashboard/logs", response_model=list[InferenceLogOut])
async def get_recent_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get recent inference logs for the log table."""
    logs = await crud.get_recent_logs(db, skip=skip, limit=limit)
    return [InferenceLogOut.model_validate(l) for l in logs]


@router.get("/dashboard/providers")
async def get_provider_breakdown(
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
):
    """Get request count breakdown by provider."""
    since = datetime.utcnow() - timedelta(hours=hours)
    stmt = (
        select(
            InferenceLogRecord.provider,
            func.count(InferenceLogRecord.id).label("count"),
            func.coalesce(func.avg(InferenceLogRecord.latency_ms), 0).label("avg_latency"),
            func.coalesce(func.sum(InferenceLogRecord.total_tokens), 0).label("total_tokens"),
        )
        .where(InferenceLogRecord.created_at >= since)
        .group_by(InferenceLogRecord.provider)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "provider": r.provider,
            "count": r.count,
            "avg_latency_ms": round(float(r.avg_latency), 2),
            "total_tokens": int(r.total_tokens),
        }
        for r in rows
    ]
