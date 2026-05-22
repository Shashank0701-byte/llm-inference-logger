"""
FastAPI application entry point.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.db.engine import init_db
from backend.api import chat, conversations, ingestion, dashboard
from backend.events.consumer import consume

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # Startup
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    await init_db()
    logger.info("Database initialized")

    # Start event consumer as a background task
    consumer_task = asyncio.create_task(consume())
    logger.info("Event consumer started as background task")

    yield

    # Shutdown
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        logger.info("Event consumer stopped")


app = FastAPI(
    title="LLM Inference Logger",
    description="Lightweight inference logging and ingestion system for LLM applications",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(conversations.router, prefix="/api", tags=["Conversations"])
app.include_router(ingestion.router, prefix="/api", tags=["Ingestion"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "providers": settings.available_providers,
    }
