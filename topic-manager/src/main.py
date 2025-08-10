from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any

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
try:
    from repository import SQLiteTopicRepository, TopicModel
    import os
    DB_PATH = os.getenv("TOPIC_MANAGER_DB", ":memory:")
    REPO = SQLiteTopicRepository(DB_PATH)
except Exception:
    REPO = None


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "topic-manager", "version": "1.0.0"}


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


@app.get("/topics/{topic_id}")
async def get_topic(topic_id: str):
    t = TOPICS.get(topic_id) or (REPO.get(topic_id) if REPO else None)
    if not t:
        return {"error": "not_found"}
    return t


@app.put("/topics/{topic_id}")
async def update_topic(topic_id: str, topic: Topic):
    if topic_id not in TOPICS and not (REPO and REPO.get(topic_id)):
        return {"error": "not_found"}
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
    return {"error": "not_found"}


@app.get("/topics")
async def list_topics(limit: int = Query(20, ge=1, le=200), offset: int = Query(0, ge=0), q: Optional[str] = None, content_type: Optional[str] = None):
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
            for t in REPO.list(limit=limit, offset=offset, q=q, content_type=content_type)
        ]
    else:
        if q:
            ql = q.lower()
            items = [t for t in items if ql in t.title.lower() or ql in t.description.lower() or any(ql in k.lower() for k in t.keywords)]
        if content_type:
            items = [t for t in items if t.content_type.lower() == content_type.lower()]
        items = items[offset: offset + limit]
    return {"items": [i.model_dump() for i in items], "count": len(items)}
