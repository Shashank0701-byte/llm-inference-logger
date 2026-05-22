# Architecture Notes

## Ingestion Flow

1. User sends a chat message via the frontend
2. Backend API calls the SDK wrapper (`InferenceClient`)
3. SDK calls LiteLLM → LLM provider, captures latency/tokens/status
4. SDK applies PII redaction to input/output previews
5. SDK publishes the log event to Redis Streams (fire-and-forget)
6. Event worker consumes from the stream, stores in PostgreSQL
7. Dashboard queries PostgreSQL for aggregated metrics

## Logging Strategy

- **Near real-time**: Logs are published asynchronously via Redis Streams so they don't block the chat response
- **PII-safe**: Input/output previews are redacted before leaving the SDK
- **Structured**: All logs follow the `InferenceLog` Pydantic schema for consistency

## Scaling Considerations

- **Redis Streams consumer groups** allow horizontal scaling of event workers
- **Async everywhere**: FastAPI + asyncpg + aioredis for non-blocking I/O
- **Database indexes** on `(conversation_id, created_at)` and `(provider, status)` for fast dashboard queries

## Failure Handling

- SDK publish failures are caught silently — chat continues even if logging fails
- Redis consumer uses acknowledgment — unacked messages are re-delivered
- Dead letter handling after 3 failed processing attempts

## Schema Design Decisions

- **JSONB** for `request_params` and `raw_metadata` — flexible, provider-specific fields
- **Separate `messages` and `inference_logs`** — clean separation of chat data vs. observability data
- **Soft-delete** via `status` field on conversations — no data loss

## Tradeoffs

- **LiteLLM over raw SDKs**: Trades some control for instant multi-provider support
- **Redis Streams over Kafka**: Simpler ops, sufficient at this scale, same consumer group semantics
- **Denormalized previews**: Duplicates data but eliminates joins for the most common query
