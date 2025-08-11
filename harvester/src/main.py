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
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

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

# Prometheus metrics
REGISTRY = CollectorRegistry()
HARVEST_COUNTER = Counter("harvest_runs_total", "Total harvest runs", registry=REGISTRY)
HARVEST_ITEMS = Counter("harvest_items_total", "Total items fetched", ["source"], registry=REGISTRY)
HARVEST_SAVED = Counter("harvest_saved_total", "Total items saved to Chroma", registry=REGISTRY)
HARVEST_DURATION = Histogram("harvest_duration_seconds", "Harvest duration in seconds", registry=REGISTRY)
HARVEST_ERRORS = Counter("harvest_source_errors_total", "Total source errors", ["source"], registry=REGISTRY)

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
    HARVEST_COUNTER.inc()
    with HARVEST_DURATION.time():
        items, errors = await engine.run()
    # per-source counts
    per_source: Dict[str, int] = {}
    for it in items:
        per_source[it.source] = per_source.get(it.source, 0) + 1
        HARVEST_ITEMS.labels(it.source).inc()
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
    # Metrics for saved and source errors
    HARVEST_SAVED.inc(saved)
    for src, err in errors.items():
        HARVEST_ERRORS.labels(src).inc()
    return run_status

@app.post("/triage/selective-preview")
async def selective_preview(summary: str) -> Dict[str, Any]:
    """Lightweight selective triage preview: calls profile score and novelty check, returns decision only.

    This does not create topics. It’s a dry-run to verify Phase 2 contracts.
    """
    # Editorial profile score
    editorial_url = f"{settings.EDITORIAL_SERVICE_URL}/profile/score"
    novelty_url = f"{settings.TOPIC_MANAGER_URL}/topics/novelty-check"
    headers_tm = {}
    if settings.TOPIC_MANAGER_TOKEN:
        headers_tm["Authorization"] = f"Bearer {settings.TOPIC_MANAGER_TOKEN}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        prof_score = 0.0
        try:
            r = await client.post(editorial_url, json={"content_summary": summary})
            if r.status_code == 200:
                prof_score = float(r.json().get("profile_fit_score") or 0.0)
        except Exception:
            pass
        novelty_score = 0.0
        try:
            r2 = await client.post(novelty_url, json={"title": summary, "summary": summary}, headers=headers_tm)
            if r2.status_code == 200:
                novelty_score = float(r2.json().get("similarity_score") or 0.0)
                # Convert to novelty (the endpoint returns similarity vs existing)
                novelty_score = 1.0 - novelty_score
        except Exception:
            pass
    pth = settings.SELECTIVE_PROFILE_THRESHOLD
    nth = settings.SELECTIVE_NOVELTY_THRESHOLD
    decision = "PROMOTE" if (prof_score >= pth and novelty_score >= nth) else "REJECT"
    return {"profile_fit_score": prof_score, "novelty_score": novelty_score, "decision": decision}

@app.post("/triage/selective")
async def selective_triage(summary: str, content_type: str = "POST") -> Dict[str, Any]:
    """Full selective triage: scoring + novelty + optional suggestion create with Idempotency-Key.

    Returns decision and, on PROMOTE, the created/duplicate topic info.
    """
    editorial_url = f"{settings.EDITORIAL_SERVICE_URL}/profile/score"
    novelty_url = f"{settings.TOPIC_MANAGER_URL}/topics/novelty-check"
    suggest_url = f"{settings.TOPIC_MANAGER_URL}/topics/suggestion"
    headers_tm = {}
    if settings.TOPIC_MANAGER_TOKEN:
        headers_tm["Authorization"] = f"Bearer {settings.TOPIC_MANAGER_TOKEN}"
    async with httpx.AsyncClient(timeout=12.0) as client:
        prof_score = 0.0
        try:
            r = await client.post(editorial_url, json={"content_summary": summary})
            if r.status_code == 200:
                prof_score = float(r.json().get("profile_fit_score") or 0.0)
        except Exception:
            pass
        novelty_sim = 0.0
        try:
            r2 = await client.post(novelty_url, json={"title": summary, "summary": summary}, headers=headers_tm)
            if r2.status_code == 200:
                novelty_sim = float(r2.json().get("similarity_score") or 0.0)
        except Exception:
            pass
        novelty_score = 1.0 - novelty_sim
        pth = settings.SELECTIVE_PROFILE_THRESHOLD
        nth = settings.SELECTIVE_NOVELTY_THRESHOLD
        decision = "PROMOTE" if (prof_score >= pth and novelty_score >= nth) else "REJECT"
        result: Dict[str, Any] = {"profile_fit_score": prof_score, "novelty_score": novelty_score, "decision": decision}
        if decision == "PROMOTE":
            # Promote with idempotency
            idem = f"triage_{hash(summary) & 0xffffffff:x}"
            sugg_payload = {
                "title": summary,
                "summary": summary,
                "keywords": ["ai", "trend"],
                "content_type": content_type,
            }
            try:
                r3 = await client.post(suggest_url, json=sugg_payload, headers={**headers_tm, "Idempotency-Key": idem})
                if r3.status_code == 200:
                    result["suggestion_result"] = r3.json()
                else:
                    result["suggestion_error"] = {"status": r3.status_code, "body": r3.text}
            except Exception as e:
                result["suggestion_error"] = {"error": str(e)}
        return result

@app.get("/harvest/status")
async def get_status():
    # Return last run snapshot
    return {"last_run": getattr(app.state, "last_run", {"status": "not_run_yet"})}

@app.get("/metrics")
async def metrics() -> Response:
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8043)
