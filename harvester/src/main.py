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
import asyncio as _asyncio
import logging
from datetime import datetime, timedelta
import json
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response, Query

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
    # Background scheduler: periodically run full cycle (fetch -> selective triage -> promote)
    interval_min = 30  # default every 30 minutes
    try:
        cron = settings.HARVEST_SCHEDULE_CRON or "*/30 * * * *"
        if cron.startswith("*/"):
            interval_min = int(cron.split()[0].replace("*/", ""))
    except Exception:
        interval_min = 30
    # Expose schedule in app state
    app.state.interval_min = interval_min
    app.state.next_run_at = (datetime.utcnow() + timedelta(minutes=interval_min)).isoformat() + "Z"

    async def _run_full_cycle():
        # 1) Fetch and save
        status = await trigger_harvest()  # type: ignore
        fetched = int(status.get("fetched", 0) or 0)
        # 2) Read candidates from raw_trends
        storage = StorageService(settings.CHROMADB_HOST, settings.CHROMADB_PORT, settings.CHROMADB_COLLECTION)
        candidates = []
        try:
            candidates = await storage.list_candidates(limit=min(max(fetched, 50), 500))
        except Exception:
            candidates = []
        # 3) Selective triage + promote for each candidate
        promoted = 0
        triage_errors = 0
        promoted_ids: list[str] = []
        async with httpx.AsyncClient(timeout=12.0) as _:
            for cand in candidates:
                summary = cand.get("document") or (cand.get("metadata") or {}).get("title") or ""
                if not summary:
                    continue
                try:
                    r = await selective_triage(summary=summary, content_type="POST")  # type: ignore
                    if r.get("decision") == "PROMOTE":
                        promoted += 1
                        promoted_ids.append(cand.get("id"))
                except Exception:
                    triage_errors += 1
        # 4) Update status promoted in raw_trends
        if promoted_ids:
            try:
                await storage.update_status(promoted_ids, status="promoted")
            except Exception:
                pass
        # Update last_run snapshot
        status.update({"promoted": promoted, "triage_errors": triage_errors, "promoted_ids_count": len(promoted_ids)})
        app.state.last_run = status
        logger.info("harvest_cycle_completed", extra={"event": "harvest_cycle_completed", "data": status})

    async def _loop():
        while True:
            try:
                await _run_full_cycle()
            except Exception:
                pass
            # Compute next run before sleeping
            app.state.next_run_at = (datetime.utcnow() + timedelta(minutes=interval_min)).isoformat() + "Z"
            await _asyncio.sleep(max(300, interval_min * 60))
    _asyncio.create_task(_loop())
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
HARVEST_EXT_CALLS = Counter(
    "harvest_external_calls_total",
    "External HTTP calls by service/endpoint/result",
    ["service", "endpoint", "result"],
    registry=REGISTRY,
)
HARVEST_EXT_ERRORS = Counter(
    "harvest_external_errors_total",
    "External HTTP errors by service/endpoint",
    ["service", "endpoint"],
    registry=REGISTRY,
)
HARVEST_EXT_LATENCY = Histogram(
    "harvest_external_call_seconds",
    "Latency of external HTTP calls",
    ["service", "endpoint"],
    registry=REGISTRY,
)

@app.get("/health")
async def health_check():
    # Probe dependencies best-effort
    deps = {
        "chromadb": {"url": f"http://{settings.CHROMADB_HOST}:{settings.CHROMADB_PORT}", "healthy": False},
        "editorial_service": {"url": settings.EDITORIAL_SERVICE_URL, "healthy": False},
        "topic_manager": {"url": settings.TOPIC_MANAGER_URL, "healthy": False},
    }
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            # Chroma heartbeat v1/v2
            try:
                r = await client.get(f"http://{settings.CHROMADB_HOST}:{settings.CHROMADB_PORT}/api/v1/heartbeat")
                deps["chromadb"]["healthy"] = (r.status_code == 200)
            except Exception:
                try:
                    r = await client.get(f"http://{settings.CHROMADB_HOST}:{settings.CHROMADB_PORT}/api/v2/heartbeat")
                    deps["chromadb"]["healthy"] = (r.status_code == 200)
                except Exception:
                    deps["chromadb"]["healthy"] = False
            # Editorial Service
            try:
                r2 = await client.get(f"{settings.EDITORIAL_SERVICE_URL}/health")
                deps["editorial_service"]["healthy"] = (r2.status_code == 200)
            except Exception:
                deps["editorial_service"]["healthy"] = False
            # Topic Manager
            try:
                r3 = await client.get(f"{settings.TOPIC_MANAGER_URL}/health")
                deps["topic_manager"]["healthy"] = (r3.status_code == 200)
            except Exception:
                deps["topic_manager"]["healthy"] = False
    except Exception:
        pass
    overall = all(v.get("healthy") for v in deps.values())
    return {
        "status": "healthy" if overall else "degraded",
        "dependencies": deps,
        "schedule": {
            "interval_minutes": getattr(app.state, "interval_min", None),
            "next_run_at": getattr(app.state, "next_run_at", None),
        },
        "sources": ["hacker-news", "arxiv", "dev-to", "newsdata-io", "product-hunt"],
    }

@app.post("/harvest/trigger")
async def trigger_harvest(limit: int = Query(None, ge=1, le=100)):
    engine = FetcherEngine()
    storage = StorageService(settings.CHROMADB_HOST, settings.CHROMADB_PORT, settings.CHROMADB_COLLECTION)
    started_at = datetime.utcnow()
    HARVEST_COUNTER.inc()
    with HARVEST_DURATION.time():
        effective_limit = int(limit or settings.HARVEST_FETCH_LIMIT)
        items, errors = await engine.run(limit=effective_limit)
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
        "limit": effective_limit,
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
    corr_id = f"triage-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        prof_score = 0.0
        try:
            with HARVEST_EXT_LATENCY.labels("editorial", "/profile/score").time():
                r = await client.post(editorial_url, json={"content_summary": summary}, headers={"X-Request-Id": corr_id})
            if r.status_code == 200:
                HARVEST_EXT_CALLS.labels("editorial", "/profile/score", "ok").inc()
                prof_score = float(r.json().get("profile_fit_score") or 0.0)
            else:
                HARVEST_EXT_CALLS.labels("editorial", "/profile/score", str(r.status_code)).inc()
        except Exception:
            HARVEST_EXT_ERRORS.labels("editorial", "/profile/score").inc()
        novelty_score = 0.0
        try:
            with HARVEST_EXT_LATENCY.labels("topic-manager", "/topics/novelty-check").time():
                r2 = await client.post(novelty_url, json={"title": summary, "summary": summary}, headers={**headers_tm, "X-Request-Id": corr_id})
            if r2.status_code == 200:
                HARVEST_EXT_CALLS.labels("topic-manager", "/topics/novelty-check", "ok").inc()
                novelty_score = float(r2.json().get("similarity_score") or 0.0)
                novelty_score = 1.0 - novelty_score
            else:
                HARVEST_EXT_CALLS.labels("topic-manager", "/topics/novelty-check", str(r2.status_code)).inc()
        except Exception:
            HARVEST_EXT_ERRORS.labels("topic-manager", "/topics/novelty-check").inc()
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
    corr_id = f"triage-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    async with httpx.AsyncClient(timeout=12.0) as client:
        prof_score = 0.0
        try:
            with HARVEST_EXT_LATENCY.labels("editorial", "/profile/score").time():
                r = await client.post(editorial_url, json={"content_summary": summary}, headers={"X-Request-Id": corr_id})
            if r.status_code == 200:
                HARVEST_EXT_CALLS.labels("editorial", "/profile/score", "ok").inc()
                prof_score = float(r.json().get("profile_fit_score") or 0.0)
            else:
                HARVEST_EXT_CALLS.labels("editorial", "/profile/score", str(r.status_code)).inc()
        except Exception:
            HARVEST_EXT_ERRORS.labels("editorial", "/profile/score").inc()
        novelty_sim = 0.0
        try:
            with HARVEST_EXT_LATENCY.labels("topic-manager", "/topics/novelty-check").time():
                r2 = await client.post(novelty_url, json={"title": summary, "summary": summary}, headers={**headers_tm, "X-Request-Id": corr_id})
            if r2.status_code == 200:
                HARVEST_EXT_CALLS.labels("topic-manager", "/topics/novelty-check", "ok").inc()
                novelty_sim = float(r2.json().get("similarity_score") or 0.0)
            else:
                HARVEST_EXT_CALLS.labels("topic-manager", "/topics/novelty-check", str(r2.status_code)).inc()
        except Exception:
            HARVEST_EXT_ERRORS.labels("topic-manager", "/topics/novelty-check").inc()
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
                with HARVEST_EXT_LATENCY.labels("topic-manager", "/topics/suggestion").time():
                    r3 = await client.post(suggest_url, json=sugg_payload, headers={**headers_tm, "Idempotency-Key": idem, "X-Request-Id": corr_id})
                if r3.status_code == 200:
                    HARVEST_EXT_CALLS.labels("topic-manager", "/topics/suggestion", "ok").inc()
                    result["suggestion_result"] = r3.json()
                else:
                    HARVEST_EXT_CALLS.labels("topic-manager", "/topics/suggestion", str(r3.status_code)).inc()
                    result["suggestion_error"] = {"status": r3.status_code, "body": r3.text}
            except Exception as e:
                HARVEST_EXT_ERRORS.labels("topic-manager", "/topics/suggestion").inc()
                result["suggestion_error"] = {"error": str(e)}
        return result

@app.get("/harvest/status")
async def get_status():
    # Return last run snapshot and next run
    return {
        "last_run": getattr(app.state, "last_run", {"status": "not_run_yet"}),
        "next_run_at": getattr(app.state, "next_run_at", None),
    }

@app.get("/metrics")
async def metrics() -> Response:
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8043)
