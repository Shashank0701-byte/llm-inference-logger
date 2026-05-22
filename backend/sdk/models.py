"""
Pydantic models for inference log payloads and SDK data structures.
"""

from datetime import datetime
from typing import Optional, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class InferenceLog(BaseModel):
    """Schema for a single inference log entry."""

    id: UUID = Field(default_factory=uuid4)
    conversation_id: Optional[UUID] = None
    session_id: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model: str = ""
    provider: str = ""
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    status: Literal["success", "error"] = "success"
    error_message: Optional[str] = None
    input_preview: str = ""
    output_preview: str = ""
    request_params: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InferenceResult(BaseModel):
    """Result returned from an inference call, including response and metadata."""

    content: str = ""
    model: str = ""
    provider: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    log: Optional[InferenceLog] = None
