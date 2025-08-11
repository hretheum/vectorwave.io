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
from datetime import datetime
import json

# Configure logging (structured JSON lines)
logger = logging.getLogger("harvester")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            payload: Dict[str, Any] = {
                "timestamp": datetime.utcnow().isoformat()+"Z",
                "level": record.levelname.lower(),
                "message": record.getMessage(),
                "logger": record.name,
            }
            # Attach extras if present
            for key in ("event", "data"):
                if hasattr(record, key):
                    payload[key] = getattr(record, key)
            return json.dumps(payload, ensure_ascii=False)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Trend Harvester service starting up...")
    # Initialize scheduler, database connections etc.
    app.state.last_run: Dict[str, Any] = {"status": "not_run_yet"}
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
    started_at = datetime.utcnow()
    items, errors = await engine.run()
    # per-source counts
    per_source: Dict[str, int] = {}
    for it in items:
        per_source[it.source] = per_source.get(it.source, 0) + 1
    saved = 0
    try:
        saved = await storage.save_items(items)
    except Exception as e:
        # Isolate Chroma failure, still return 200 with diagnostics
        logger.error("Chroma save failed", extra={"event": "chroma_save_error", "data": {"error": str(e)}})
    ended_at = datetime.utcnow()
    duration_ms = int((ended_at - started_at).total_seconds() * 1000)
    # Persist last run status in app state
    run_status = {
        "status": "completed",
        "started_at": started_at.isoformat()+"Z",
        "ended_at": ended_at.isoformat()+"Z",
        "duration_ms": duration_ms,
        "fetched": len(items),
        "saved": saved,
        "per_source": per_source,
        "source_errors": errors,
    }
    app.state.last_run = run_status
    logger.info("harvest_completed", extra={"event": "harvest_completed", "data": run_status})
    return run_status

@app.get("/harvest/status")
async def get_status():
    # Return last run snapshot
    return {"last_run": getattr(app.state, "last_run", {"status": "not_run_yet"})}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8043)
