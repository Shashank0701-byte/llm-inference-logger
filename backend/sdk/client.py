"""
LLM Inference Client - wraps LiteLLM to capture metadata.

Supports both regular and streaming completions with automatic
logging of latency, token usage, and request metadata.
"""

import time
import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional

import litellm

from backend.sdk.models import InferenceLog, InferenceResult
from backend.sdk.logger import LogPublisher
from backend.sdk.pii import PIIRedactor
from backend.sdk.metadata import extract_provider


class InferenceClient:
    """Lightweight wrapper around LLM calls that captures inference metadata."""

    def __init__(self, publisher: Optional[LogPublisher] = None, redactor: Optional[PIIRedactor] = None):
        self.publisher = publisher or LogPublisher()
        self.redactor = redactor or PIIRedactor()

    async def complete(
        self,
        messages: list[dict],
        model: str,
        conversation_id: Optional[str] = None,
        session_id: str = "",
        **kwargs,
    ) -> InferenceResult:
        """
        Send a completion request and capture inference metadata.

        Args:
            messages: Chat messages in OpenAI format.
            model: Model identifier (e.g., 'gpt-4.1', 'claude-sonnet-4-20250514').
            conversation_id: Optional conversation ID for grouping.
            session_id: Optional session identifier.
            **kwargs: Additional params passed to LiteLLM.

        Returns:
            InferenceResult with response content and metadata.
        """
        start = time.monotonic()
        log = InferenceLog(
            conversation_id=conversation_id,
            session_id=session_id,
            model=model,
            provider=extract_provider(model),
            request_params=kwargs,
        )

        try:
            response = await litellm.acompletion(model=model, messages=messages, **kwargs)
            latency_ms = (time.monotonic() - start) * 1000

            content = response.choices[0].message.content or ""
            usage = response.usage

            log.latency_ms = latency_ms
            log.input_tokens = usage.prompt_tokens if usage else 0
            log.output_tokens = usage.completion_tokens if usage else 0
            log.total_tokens = usage.total_tokens if usage else 0
            log.status = "success"
            log.input_preview = self.redactor.redact(str(messages[-1].get("content", ""))[:500])
            log.output_preview = self.redactor.redact(content[:500])

            await self.publisher.publish(log)

            return InferenceResult(
                content=content,
                model=model,
                provider=log.provider,
                input_tokens=log.input_tokens,
                output_tokens=log.output_tokens,
                total_tokens=log.total_tokens,
                latency_ms=latency_ms,
                log=log,
            )

        except Exception as e:
            latency_ms = (time.monotonic() - start) * 1000
            log.latency_ms = latency_ms
            log.status = "error"
            log.error_message = str(e)
            await self.publisher.publish(log)
            raise

    async def stream(
        self,
        messages: list[dict],
        model: str,
        conversation_id: Optional[str] = None,
        session_id: str = "",
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a completion response, yielding content chunks.
        Logs metadata after stream completes.
        """
        start = time.monotonic()
        full_content = ""
        log = InferenceLog(
            conversation_id=conversation_id,
            session_id=session_id,
            model=model,
            provider=extract_provider(model),
            request_params=kwargs,
        )

        try:
            response = await litellm.acompletion(
                model=model, messages=messages, stream=True, **kwargs
            )

            async for chunk in response:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    full_content += delta.content
                    yield delta.content

            latency_ms = (time.monotonic() - start) * 1000
            log.latency_ms = latency_ms
            log.status = "success"
            log.input_preview = self.redactor.redact(str(messages[-1].get("content", ""))[:500])
            log.output_preview = self.redactor.redact(full_content[:500])

            await self.publisher.publish(log)

        except Exception as e:
            latency_ms = (time.monotonic() - start) * 1000
            log.latency_ms = latency_ms
            log.status = "error"
            log.error_message = str(e)
            await self.publisher.publish(log)
            raise
