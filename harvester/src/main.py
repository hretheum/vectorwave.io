# Placeholder for main application logic
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from .config import settings
from .fetcher import FetcherEngine
from .storage import StorageService
from .models import RawTrendItem
import httpx
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Trend Harvester service starting up...")
    # Initialize scheduler, database connections etc.
    yield
    # Shutdown logic
    logger.info("Trend Harvester service shutting down...")

app = FastAPI(
    title="Trend Harvester Service",
    description="Service for automated ingestion and triage of AI trends.",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    # Lightweight health with static dependencies info
    return {
        "status": "healthy",
        "dependencies": {
            "chromadb": f"{settings.CHROMADB_HOST}:{settings.CHROMADB_PORT}",
            "editorial_service": settings.EDITORIAL_SERVICE_URL,
            "topic_manager": settings.TOPIC_MANAGER_URL,
            "sources": ["hacker-news", "arxiv", "dev-to", "newsdata-io"],
        },
    }

@app.post("/harvest/trigger")
async def trigger_harvest():
    engine = FetcherEngine()
    storage = StorageService(settings.CHROMADB_HOST, settings.CHROMADB_PORT, settings.CHROMADB_COLLECTION)
    items, errors = await engine.run()
    saved = 0
    try:
        saved = await storage.save_items(items)
    except Exception as e:
        # Isolate Chroma failure, still return 200 with diagnostics
        logger.error("Chroma save failed: %s", e)
    return {"status": "ok", "fetched": len(items), "saved": saved, "source_errors": errors}

@app.get("/harvest/status")
async def get_status():
    # This would return the actual status from a state manager
    return {"last_run": {"status": "not_run_yet"}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8043)
