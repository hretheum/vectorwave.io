from fastapi import FastAPI, Query, HTTPException, Header, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any, Tuple
import asyncio
import os
from dotenv import load_dotenv
import asyncio as _asyncio
from .infrastructure.chromadb_client import ChromaDBHTTPClient
from .infrastructure.embeddings import resolve_provider

# Load env once at startup (safe if missing)
load_dotenv()

async def _background_reindex_task():
    cron = os.getenv("INDEX_REINDEX_CRON", "*/10 * * * *")
    interval_min = 10
    try:
        if cron.startswith("*/"):
            interval_min = int(cron.split()[0].replace("*/", ""))
    except Exception:
        interval_min = 10
    while True:
        try:
            await topics_index_reindex(limit=200, reset=False, repo=app.state.repo)  # type: ignore
        except Exception:
            pass
        await _asyncio.sleep(max(60, interval_min * 60))

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
class NoveltyCheckRequest(BaseModel):
    title: str
    normalized_title: Optional[str] = None
    summary: Optional[str] = None
    keywords: List[str] = []
    source_url: Optional[str] = None
    published_at: Optional[str] = None
    dedupe_keys: Optional[List[str]] = None


class NoveltyCheckResponse(BaseModel):
    decision: str  # DUPLICATE | NOVEL
    similarity_score: float
    nearest: List[Dict[str, Any]]
    threshold: float


class SuggestionSource(BaseModel):
    url: Optional[str] = None
    origin: Optional[str] = None  # hn|arxiv|github|rss|manual


class TriageScores(BaseModel):
    score: Optional[float] = None
    editorial_fit: Optional[float] = None
    novelty_score: Optional[float] = None


class SuggestionIngestRequest(BaseModel):
    title: str
    summary: Optional[str] = None
    keywords: List[str] = []
    content_type: str
    source: Optional[SuggestionSource] = None
    triage: Optional[TriageScores] = None
    dedupe_keys: Optional[List[str]] = None


class SuggestionIngestResponse(BaseModel):
    status: str  # created|updated|duplicate
    topic_id: Optional[str] = None
    existing_topic_id: Optional[str] = None


# --- Vector Topics Index (skeleton for Post Week 9) ---
class TopicsIndexInfo(BaseModel):
    collection: str = "topics_index"
    ready: bool = False
    total_indexed: int = 0
    chromadb_status: Optional[Dict[str, Any]] = None
    # New diagnostic fields
    total_topics: int = 0
    last_indexed: int = 0
    index_coverage: float = 0.0
    chroma_reported_count: Optional[int] = None

class TopicsSearchResponse(BaseModel):
    query: str
    items: List[Dict[str, Any]]
    count: int
    took_ms: float

class TopicsIndexVerifyResponse(BaseModel):
    sampled_ids: List[str]
    present: int
    missing: int
    sample_size: int
    details: Optional[Dict[str, Any]] = None


class TopicRepository:
    def __init__(self) -> None:
        self._topics: Dict[str, Topic] = {}
        self._idempotency: Dict[str, str] = {}

    def list(
        self,
        limit: int = 100,
        offset: int = 0,
        q: Optional[str] = None,
        content_type: Optional[str] = None,
        title_contains: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: str = "asc",
    ) -> List[Topic]:
        items = list(self._topics.values())
        if q:
            ql = q.lower()
            items = [
                t
                for t in items
                if ql in t.title.lower()
                or ql in t.description.lower()
                or any(ql in k.lower() for k in t.keywords)
            ]
        if content_type:
            items = [t for t in items if t.content_type.lower() == content_type.lower()]
        if title_contains:
            sub = title_contains.lower()
            items = [t for t in items if sub in t.title.lower()]
        reverse = order.lower() == "desc"
        if sort_by in {"topic_id", "title", "content_type"}:
            items.sort(key=lambda t: getattr(t, sort_by), reverse=reverse)
        return items[offset : offset + limit]

    def count(self, q: Optional[str] = None, content_type: Optional[str] = None) -> int:
        return len(self.list(limit=10 ** 9, offset=0, q=q, content_type=content_type))

    def get(self, topic_id: str) -> Optional[Topic]:
        return self._topics.get(topic_id)

    def save(self, topic: Topic) -> str:
        if not topic.topic_id:
            topic.topic_id = f"t_{len(self._topics)+1:06d}"
        self._topics[topic.topic_id] = topic
        return topic.topic_id

    def delete(self, topic_id: str) -> bool:
        return self._topics.pop(topic_id, None) is not None

    def check_idempotency(self, key: str) -> Optional[str]:
        return self._idempotency.get(key)

    def store_idempotency(self, key: str, topic_id: str) -> None:
        self._idempotency[key] = topic_id


def get_repo() -> TopicRepository:
    return app.state.repo


@app.on_event("startup")
async def _startup() -> None:
    app.state.repo = TopicRepository()
    _asyncio.create_task(_background_reindex_task())

_CHROMA = None
_INDEX_COLLECTION = "topics_index"
_EMBEDDINGS = None
_LAST_INDEXED = 0

async def _get_chroma():
    global _CHROMA
    if _CHROMA is None:
        try:
            _CHROMA = ChromaDBHTTPClient(
                host=os.getenv("CHROMADB_HOST", "chromadb"),
                port=int(os.getenv("CHROMADB_PORT", "8000")),
            )
        except Exception:
            _CHROMA = None
    return _CHROMA

async def _get_embeddings():
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        try:
            _EMBEDDINGS = resolve_provider()
        except Exception:
            _EMBEDDINGS = None
    return _EMBEDDINGS

def _cheap_embedding(text: str, dim: int = 64) -> List[float]:
    # Deterministic, cheap bag-of-chars embedding (for environments without real embedding provider)
    vec = [0.0] * dim
    if not text:
        return vec
    for i, ch in enumerate(text.lower()):
        vec[(i + ord(ch)) % dim] += 1.0
    # L2 normalize
    norm = sum(v * v for v in vec) ** 0.5 or 1.0
    return [v / norm for v in vec]

@app.get("/topics/index/info")
async def topics_index_info(repo: TopicRepository = Depends(get_repo)) -> TopicsIndexInfo:
    chroma = await _get_chroma()
    status: Optional[Dict[str, Any]] = None
    total = 0
    ready = False
    total_topics = repo.count()
    reported_count: Optional[int] = None
    if chroma is not None:
        status = await chroma.heartbeat()
        if status.get("status") == "healthy":
            # Ensure collection exists; then try count
            ready = await chroma.ensure_collection(_INDEX_COLLECTION)
            if ready:
                c = await chroma.count(_INDEX_COLLECTION)
                # Some Chroma versions do not report count; treat 0 as unknown
                if isinstance(c, int) and c > 0:
                    total = c
                    reported_count = c
                else:
                    total = 0
                    reported_count = None
    index_coverage = (float(_LAST_INDEXED) / float(total_topics)) if total_topics > 0 else 0.0
    return TopicsIndexInfo(
        collection=_INDEX_COLLECTION,
        ready=ready,
        total_indexed=total,
        chromadb_status=status,
        total_topics=total_topics,
        last_indexed=_LAST_INDEXED,
        index_coverage=round(index_coverage, 4),
        chroma_reported_count=reported_count,
    )

@app.post("/topics/index/verify")
async def topics_index_verify(
    sample_size: int = Query(10, ge=1, le=100),
    repo: TopicRepository = Depends(get_repo),
) -> TopicsIndexVerifyResponse:
    ids = [t.topic_id for t in repo.list(limit=sample_size, offset=0)]
    chroma = await _get_chroma()
    if not chroma:
        raise HTTPException(status_code=503, detail={"code": "chromadb_unavailable", "detail": "Chroma client not initialized"})
    # Attempt fetch by IDs
    res = await chroma.get(_INDEX_COLLECTION, ids)
    found = 0
    try:
        got_ids = res.get("ids") or []
        if got_ids and isinstance(got_ids[0], list):
            got_ids = got_ids[0]
        found = len(got_ids)
    except Exception:
        found = 0
    return TopicsIndexVerifyResponse(
        sampled_ids=ids,
        present=found,
        missing=max(0, len(ids) - found),
        sample_size=len(ids),
        details={"raw": res} if res else None,
    )

@app.post("/topics/index/reindex")
async def topics_index_reindex(
    limit: int = 200,
    reset: bool = False,
    repo: TopicRepository = Depends(get_repo),
) -> Dict[str, Any]:
    chroma = await _get_chroma()
    if chroma is None:
        raise HTTPException(status_code=503, detail={"code": "chromadb_unavailable", "detail": "Chroma client not initialized"})
    status = await chroma.heartbeat()
    if status.get("status") != "healthy":
        raise HTTPException(status_code=503, detail={"code": "chromadb_unhealthy", "detail": status})
    if reset:
        await chroma.delete_collection(_INDEX_COLLECTION)
    ok = await chroma.ensure_collection(_INDEX_COLLECTION)
    if not ok:
        raise HTTPException(status_code=500, detail={"code": "chromadb_collection_error", "detail": "Cannot ensure topics_index"})

    # Collect topics from repository
    items: List[Topic] = repo.list(limit=limit, offset=0)

    if not items:
        return {"indexed": 0}

    ids = [t.topic_id or f"t_{i:06d}" for i, t in enumerate(items, start=1)]
    docs = [f"{t.title}\n{t.description}\n{' '.join(t.keywords)}" for t in items]
    metas = [
        {"topic_id": t.topic_id, "title": t.title, "content_type": t.content_type}
        for t in items
    ]
    provider = await _get_embeddings()
    if provider:
        try:
            embs = await provider.embed_texts(docs)
            if not isinstance(embs, list) or len(embs) != len(docs):
                embs = [_cheap_embedding(d) for d in docs]
        except Exception:
            embs = [_cheap_embedding(d) for d in docs]
    else:
        embs = [_cheap_embedding(d) for d in docs]
    added = await chroma.add(_INDEX_COLLECTION, ids=ids, documents=docs, metadatas=metas, embeddings=embs)
    if not added:
        raise HTTPException(status_code=500, detail={"code": "chromadb_add_failed", "detail": "Batch add failed"})
    # Track last indexed count for diagnostics
    global _LAST_INDEXED
    _LAST_INDEXED = len(ids)
    return {"indexed": len(ids)}

@app.get("/topics/search")
async def topics_search(
    q: str = Query(..., min_length=2),
    limit: int = Query(5, ge=1, le=50),
    content_type: Optional[str] = Query(None),
    title_contains: Optional[str] = Query(None),
) -> TopicsSearchResponse:
    chroma = await _get_chroma()
    if chroma is None:
        raise HTTPException(status_code=503, detail={"code": "chromadb_unavailable", "detail": "Chroma client not initialized"})
    ok = await chroma.ensure_collection(_INDEX_COLLECTION)
    if not ok:
        raise HTTPException(status_code=500, detail={"code": "chromadb_collection_error", "detail": "Cannot ensure topics_index"})
    start = asyncio.get_event_loop().time()
    provider = await _get_embeddings()
    if provider:
        try:
            qvec = await provider.embed_texts([q])
        except Exception:
            qvec = [_cheap_embedding(q)]
    else:
        qvec = [_cheap_embedding(q)]
    # Build metadata filter for Chroma (where)
    where: Optional[Dict[str, Any]] = None
    if content_type or title_contains:
        where = {}
        if content_type:
            where["content_type"] = content_type
        if title_contains:
            # Chroma v1 doesn't support substring on metadata; we filter post-query below
            pass
    res = await chroma.query(_INDEX_COLLECTION, query_embeddings=qvec, n_results=limit * 3, where=where)
    took_ms = round((asyncio.get_event_loop().time() - start) * 1000.0, 2)
    # Normalize response
    items: List[Dict[str, Any]] = []
    ids = (res or {}).get("ids") or []
    docs = (res or {}).get("documents") or []
    metas = (res or {}).get("metadatas") or []
    dists = (res or {}).get("distances") or []
    if ids and isinstance(ids[0], list):
        ids = ids[0]
    if docs and isinstance(docs[0], list):
        docs = docs[0]
    if metas and isinstance(metas[0], list):
        metas = metas[0]
    if dists and isinstance(dists[0], list):
        dists = dists[0]
    for i, tid in enumerate(ids):
        meta = metas[i] if i < len(metas) else None
        doc = docs[i] if i < len(docs) else None
        item = {
            "topic_id": tid,
            "distance": float(dists[i]) if i < len(dists) else None,
            "metadata": meta,
            "document": doc,
            "score": 1.0 - float(dists[i]) if i < len(dists) and isinstance(dists[i], (int, float)) else None,
        }
        # Post-filter for title_contains
        if title_contains and meta and isinstance(meta, dict):
            title = str(meta.get("title", ""))
            if title_contains.lower() not in title.lower():
                continue
        items.append(item)
        if len(items) >= limit:
            break
    return TopicsSearchResponse(query=q, items=items, count=len(items), took_ms=took_ms)

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
async def health(repo: TopicRepository = Depends(get_repo)):
    db_connected = True if repo is not None else False
    embeddings_ready = False
    embeddings_provider: Optional[str] = None
    try:
        prov = await _get_embeddings()
        if prov is not None:
            embeddings_ready = True
            embeddings_provider = prov.__class__.__name__
    except Exception:
        embeddings_ready = False
    chroma_status: Optional[Dict[str, Any]] = None
    try:
        chroma = await _get_chroma()
        if chroma is not None:
            chroma_status = await chroma.heartbeat()
    except Exception:
        chroma_status = {"status": "unknown"}
    return {
        "status": "healthy",
        "service": "topic-manager",
        "version": "1.0.0",
        "db_connected": db_connected,
        "db_path": "memory",
        "embeddings_ready": embeddings_ready,
        "embeddings_provider": embeddings_provider,
        "chromadb": chroma_status,
    }


@app.post("/topics/manual")
async def add_manual_topic(topic: Topic, repo: TopicRepository = Depends(get_repo)):
    topic_id = repo.save(topic)
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




def _auth_dependency(authorization: Optional[str] = Header(None)):
    token_expected = os.getenv("TOPIC_MANAGER_TOKEN")
    if token_expected:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail={"code": "unauthorized", "detail": "Missing bearer token"})
        provided = authorization.split(" ", 1)[1]
        if provided != token_expected:
            raise HTTPException(status_code=401, detail={"code": "unauthorized", "detail": "Invalid token"})
    return True


def _normalize(text: str) -> List[str]:
    return [t for t in (text or "").lower().replace("/", " ").replace("-", " ").split() if t]


def _title_similarity(a: str, b: str) -> float:
    a_tokens = set(_normalize(a))
    b_tokens = set(_normalize(b))
    if not a_tokens or not b_tokens:
        return 0.0
    inter = len(a_tokens & b_tokens)
    union = len(a_tokens | b_tokens)
    return inter / union if union else 0.0


def _find_nearest(title: str, limit: int = 3, repo: Optional[TopicRepository] = None) -> List[Tuple[str, float, str]]:
    repo = repo or app.state.repo
    pairs: List[Tuple[str, float, str]] = []
    for t in repo.list(limit=200, offset=0):
        sim = _title_similarity(title, t.title)
        if sim > 0:
            pairs.append((t.topic_id or "", sim, t.title))
    pairs.sort(key=lambda x: x[1], reverse=True)
    seen = set()
    nearest = []
    for tid, sim, ttl in pairs:
        if tid in seen:
            continue
        seen.add(tid)
        nearest.append((tid, sim, ttl))
        if len(nearest) >= limit:
            break
    return nearest


@app.post("/topics/novelty-check")
async def novelty_check(
    req: NoveltyCheckRequest,
    _: bool = Depends(_auth_dependency),
    repo: TopicRepository = Depends(get_repo),
) -> NoveltyCheckResponse:
    title = req.normalized_title or req.title
    threshold = float(os.getenv("NOVELTY_SIMILARITY_THRESHOLD", "0.85"))
    nearest = _find_nearest(title, limit=3, repo=repo)
    top_score = nearest[0][1] if nearest else 0.0
    decision = "DUPLICATE" if top_score >= threshold else "NOVEL"
    return NoveltyCheckResponse(
        decision=decision,
        similarity_score=top_score,
        nearest=[{"topic_id": tid, "score": score, "title": ttl} for tid, score, ttl in nearest],
        threshold=threshold,
    )


@app.post("/topics/suggestion")
async def ingest_suggestion(
    req: SuggestionIngestRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    _: bool = Depends(_auth_dependency),
    repo: TopicRepository = Depends(get_repo),
) -> SuggestionIngestResponse:
    if not idempotency_key:
        raise HTTPException(status_code=400, detail={"code": "missing_idempotency", "detail": "Idempotency-Key header required"})
    existing = repo.check_idempotency(idempotency_key)
    if existing:
        return SuggestionIngestResponse(status="duplicate", existing_topic_id=existing)

    # Simple dedupe by normalized title fallback
    norm_title = (req.summary or req.title).strip().lower()
    existing_id: Optional[str] = None
    for t in repo.list(limit=200, offset=0):
        if t.title.strip().lower() == norm_title or t.title.strip().lower() == req.title.strip().lower():
            existing_id = t.topic_id
            break

    if existing_id:
        repo.store_idempotency(idempotency_key, existing_id)
        return SuggestionIngestResponse(status="duplicate", existing_topic_id=existing_id)

    # Create new topic
    new_topic = Topic(
        topic_id=None,
        title=req.title,
        description=req.summary or "",
        keywords=req.keywords,
        content_type=req.content_type,
    )
    topic_id = repo.save(new_topic)
    repo.store_idempotency(idempotency_key, topic_id)

    # Best-effort: add to vector index if available
    try:
        chroma = await _get_chroma()
        provider = await _get_embeddings()
        if chroma:
            ok = await chroma.ensure_collection(_INDEX_COLLECTION)
            if ok:
                doc = f"{new_topic.title}\n{new_topic.description}\n{' '.join(new_topic.keywords)}"
                if provider:
                    try:
                        emb = await provider.embed_texts([doc])
                    except Exception:
                        emb = [_cheap_embedding(doc)]
                else:
                    emb = [_cheap_embedding(doc)]
                await chroma.add(_INDEX_COLLECTION, ids=[topic_id], documents=[doc], metadatas=[{"topic_id": topic_id, "title": new_topic.title}], embeddings=emb)
    except Exception:
        pass

    return SuggestionIngestResponse(status="created", topic_id=topic_id)

@app.get("/topics/{topic_id}")
async def get_topic(topic_id: str, repo: TopicRepository = Depends(get_repo)):
    t = repo.get(topic_id)
    if not t:
        raise HTTPException(status_code=404, detail="not_found")
    return t


@app.put("/topics/{topic_id}")
async def update_topic(topic_id: str, topic: Topic, repo: TopicRepository = Depends(get_repo)):
    if not repo.get(topic_id):
        raise HTTPException(status_code=404, detail="not_found")
    topic.topic_id = topic_id
    repo.save(topic)
    return {"status": "updated", "topic_id": topic_id}


@app.delete("/topics/{topic_id}")
async def delete_topic(topic_id: str, repo: TopicRepository = Depends(get_repo)):
    if repo.delete(topic_id):
        return {"status": "deleted", "topic_id": topic_id}
    raise HTTPException(status_code=404, detail="not_found")


@app.get("/topics")
async def list_topics(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: Optional[str] = None,
    content_type: Optional[str] = None,
    source: Optional[str] = None,
    title_contains: Optional[str] = None,
    sort_by: Optional[str] = Query(None, pattern="^(topic_id|title|content_type)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    repo: TopicRepository = Depends(get_repo),
):
    items = repo.list(
        limit=limit,
        offset=offset,
        q=q,
        content_type=content_type,
        title_contains=title_contains,
        sort_by=sort_by,
        order=order,
    )
    total = repo.count(q=q, content_type=content_type)
    return {"items": [i.model_dump() for i in items], "count": len(items), "total": total, "limit": limit, "offset": offset}
