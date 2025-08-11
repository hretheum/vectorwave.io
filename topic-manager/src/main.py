from fastapi import FastAPI, Query, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import asyncio

app = FastAPI(title="Topic Manager", version="1.0.0")


class Topic(BaseModel):
    topic_id: Optional[str] = None
    title: str
    description: str
    keywords: List[str] = []
    content_type: str
    platform_assignment: Optional[Dict[str, bool]] = None
class Suggestion(BaseModel):
    topic_id: str
    title: str
    description: str
    suggested_platforms: List[str]
    engagement_prediction: float



TOPICS: Dict[str, Topic] = {}
DB_PATH: Optional[str] = None
REPO = None
try:
    from repository import SQLiteTopicRepository, TopicModel
    import os
    DB_PATH = os.getenv("TOPIC_MANAGER_DB", ":memory:")
    REPO = SQLiteTopicRepository(DB_PATH)
except Exception:
    REPO = None


class ErrorResponse(BaseModel):
    code: str
    detail: Any


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content=ErrorResponse(code="validation_error", detail=exc.errors()).model_dump())


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    # Normalize error envelope
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        payload = detail
    else:
        # Map common codes
        default_code = "not_found" if exc.status_code == 404 else "http_error"
        payload = ErrorResponse(code=default_code, detail=detail).model_dump()
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.get("/health")
async def health():
    db_connected = False
    if REPO is not None:
        try:
            _ = REPO.list(limit=1, offset=0)
            db_connected = True
        except Exception:
            db_connected = False
    return {
        "status": "healthy",
        "service": "topic-manager",
        "version": "1.0.0",
        "db_connected": db_connected,
        "db_path": DB_PATH or "N/A",
    }


@app.post("/topics/manual")
async def add_manual_topic(topic: Topic):
    topic_id = f"t_{len(TOPICS)+1:06d}"
    topic.topic_id = topic_id
    TOPICS[topic_id] = topic
    if REPO:
        REPO.create(TopicModel(topic_id=topic_id, title=topic.title, description=topic.description, keywords=topic.keywords, content_type=topic.content_type))
    return {"status": "created", "topic_id": topic_id}


@app.get("/topics/suggestions")
async def get_topic_suggestions(limit: int = 10) -> Dict[str, List[Suggestion]]:
    suggestions = [
        Suggestion(**{
            "topic_id": f"sug_{i+1}",
            "title": f"AI trend #{i+1}",
            "description": "Auto-generated suggestion",
            "suggested_platforms": ["linkedin", "twitter"],
            "engagement_prediction": 0.6 + (i * 0.01),
        })
        for i in range(min(limit, 10))
    ]
    return {"suggestions": suggestions}


@app.post("/topics/scrape")
async def trigger_auto_scraping(limit: int = 5) -> Dict[str, Any]:
    """Trigger automated topic discovery via simple built-in stub.

    In Phase 2, use a lightweight in-process stub that simulates scraping and
    stores results in the repository when available.
    """
    # Lazy import to avoid hard dependency when unused
    try:
        from scrapers.hackernews_stub import HackerNewsTopicScraperStub  # type: ignore
    except Exception:
        HackerNewsTopicScraperStub = None  # type: ignore

    discovered: List[Dict[str, Any]] = []
    if HackerNewsTopicScraperStub is not None:
        scraper = HackerNewsTopicScraperStub()
        # Simulate async scraping
        topics = await scraper.scrape_topics()  # type: ignore
        for t in topics[: max(1, min(limit, 20))]:
            topic_id = f"t_{len(TOPICS)+1:06d}"
            model = Topic(
                topic_id=topic_id,
                title=t.get("title", "Untitled"),
                description=t.get("description", ""),
                keywords=t.get("keywords", []),
                content_type=t.get("content_type", "POST"),
            )
            TOPICS[topic_id] = model
            if REPO:
                REPO.create(
                    TopicModel(
                        topic_id=topic_id,
                        title=model.title,
                        description=model.description,
                        keywords=model.keywords,
                        content_type=model.content_type,
                    )
                )
            discovered.append({"topic_id": topic_id, "title": model.title})
    else:
        # Fallback: seed with a couple of deterministic items
        seed = [
            {"title": "AI Trends 2025", "description": "Latest AI trends.", "keywords": ["ai", "trends"], "content_type": "POST"},
            {"title": "Open Source LLMs", "description": "Review of OSS LLMs.", "keywords": ["oss", "llm"], "content_type": "ARTICLE"},
        ]
        for t in seed[: max(1, min(limit, 20))]:
            topic_id = f"t_{len(TOPICS)+1:06d}"
            model = Topic(topic_id=topic_id, **t)
            TOPICS[topic_id] = model
            if REPO:
                REPO.create(
                    TopicModel(
                        topic_id=topic_id,
                        title=model.title,
                        description=model.description,
                        keywords=model.keywords,
                        content_type=model.content_type,
                    )
                )
            discovered.append({"topic_id": topic_id, "title": model.title})

    return {"scraped_topics": len(discovered), "items": discovered}

@app.get("/topics/{topic_id}")
async def get_topic(topic_id: str):
    t = TOPICS.get(topic_id) or (REPO.get(topic_id) if REPO else None)
    if not t:
        raise HTTPException(status_code=404, detail="not_found")
    return t


@app.put("/topics/{topic_id}")
async def update_topic(topic_id: str, topic: Topic):
    if topic_id not in TOPICS and not (REPO and REPO.get(topic_id)):
        raise HTTPException(status_code=404, detail="not_found")
    # Preserve ID
    topic.topic_id = topic_id
    TOPICS[topic_id] = topic
    if REPO:
        REPO.update(TopicModel(topic_id=topic_id, title=topic.title, description=topic.description, keywords=topic.keywords, content_type=topic.content_type))
    return {"status": "updated", "topic_id": topic_id}


@app.delete("/topics/{topic_id}")
async def delete_topic(topic_id: str):
    if topic_id in TOPICS:
        del TOPICS[topic_id]
        if REPO:
            REPO.delete(topic_id)
        return {"status": "deleted", "topic_id": topic_id}
    if REPO and REPO.delete(topic_id):
        return {"status": "deleted", "topic_id": topic_id}
    raise HTTPException(status_code=404, detail="not_found")


@app.get("/topics")
async def list_topics(limit: int = Query(20, ge=1, le=200), offset: int = Query(0, ge=0), q: Optional[str] = None, content_type: Optional[str] = None, sort_by: Optional[str] = Query(None, pattern="^(topic_id|title|content_type)$"), order: str = Query("asc", pattern="^(asc|desc)$")):
    # Combine in-memory and repo for now; in future switch to repo-only when persistence enabled
    items = list(TOPICS.values())
    if REPO:
        items = [
            Topic(
                topic_id=t.topic_id,
                title=t.title,
                description=t.description,
                keywords=t.keywords,
                content_type=t.content_type,
                platform_assignment=None,
            )
            for t in REPO.list(limit=limit, offset=offset, q=q, content_type=content_type, sort_by=sort_by, order=order)
        ]
        total = REPO.count(q=q, content_type=content_type)
    else:
        if q:
            ql = q.lower()
            items = [t for t in items if ql in t.title.lower() or ql in t.description.lower() or any(ql in k.lower() for k in t.keywords)]
        if content_type:
            items = [t for t in items if t.content_type.lower() == content_type.lower()]
        total = len(items)
        items = items[offset: offset + limit]
    return {"items": [i.model_dump() for i in items], "count": len(items), "total": total, "limit": limit, "offset": offset}
