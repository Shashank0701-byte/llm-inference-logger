"""Pydantic response schemas for API serialization."""

from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field


# --- Conversation Schemas ---

class ConversationCreate(BaseModel):
    title: str = "New Conversation"
    provider: str = ""
    model: str = ""


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[Literal["active", "cancelled", "completed"]] = None


class MessageOut(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    token_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: UUID
    title: str
    status: str
    provider: str
    model: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class ConversationDetail(ConversationOut):
    messages: list[MessageOut] = []


# --- Chat Schemas ---

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None
    model: str = ""
    provider: str = ""


class ChatResponse(BaseModel):
    content: str
    conversation_id: UUID
    model: str
    provider: str
    latency_ms: float
    input_tokens: int
    output_tokens: int


# --- Ingestion Schemas ---

class IngestPayload(BaseModel):
    conversation_id: Optional[UUID] = None
    session_id: str = ""
    model: str
    provider: str
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    status: Literal["success", "error"] = "success"
    error_message: Optional[str] = None
    input_preview: str = ""
    output_preview: str = ""
    request_params: dict = Field(default_factory=dict)


class InferenceLogOut(BaseModel):
    id: UUID
    conversation_id: Optional[UUID]
    session_id: str
    model: str
    provider: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    status: str
    error_message: Optional[str]
    input_preview: str
    output_preview: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Dashboard Schemas ---

class MetricsOut(BaseModel):
    total_requests: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    total_tokens: int = 0
    requests_by_provider: dict = Field(default_factory=dict)
    requests_by_model: dict = Field(default_factory=dict)


class TimeseriesPoint(BaseModel):
    timestamp: str
    value: float


class DashboardOut(BaseModel):
    metrics: MetricsOut
    latency_series: list[TimeseriesPoint] = []
    throughput_series: list[TimeseriesPoint] = []
    error_series: list[TimeseriesPoint] = []
