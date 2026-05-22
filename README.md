# LLM Inference Logger

A lightweight inference logging and ingestion system for LLM applications.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐     ┌────────────┐
│  Frontend    │────▶│  Backend API  │────▶│  SDK / Wrapper │────▶│ LLM Providers│
│  (Next.js)   │     │  (FastAPI)    │     │  (LiteLLM)     │     │ (Multi)      │
└─────────────┘     └──────┬───────┘     └───────┬────────┘     └────────────┘
                           │                      │
                           │              ┌───────▼────────┐
                           │              │  Redis Streams  │
                           │              │  (Event Bus)    │
                           │              └───────┬────────┘
                           │                      │
                           │              ┌───────▼────────┐
                           └─────────────▶│  PostgreSQL     │
                                          │  (Storage)      │
                                          └────────────────┘
```

## Components

1. **Chatbot Application** - Multi-turn chat with streaming, multi-provider support
2. **Lightweight SDK** - Wraps LLM calls, captures metadata, redacts PII
3. **Ingestion Pipeline** - Event-driven log processing via Redis Streams
4. **Database Storage** - PostgreSQL with conversations, messages, and inference logs

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your API keys

# 2. Run with Docker Compose
docker-compose up --build
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI |
| Frontend | Next.js 14 |
| Database | PostgreSQL |
| Event Bus | Redis Streams |
| LLM | LiteLLM (multi-provider) |
| Containers | Docker Compose |

## Project Structure

```
├── backend/
│   ├── api/          # REST + SSE endpoints
│   ├── sdk/          # LLM wrapper, PII redaction, logging
│   ├── events/       # Redis Streams publisher/consumer
│   └── db/           # SQLAlchemy models, CRUD
├── frontend/         # Next.js app
├── k8s/              # Kubernetes manifests
├── docker-compose.yml
└── README.md
```

## License

MIT
