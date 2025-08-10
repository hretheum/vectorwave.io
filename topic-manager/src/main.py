from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Optional

app = FastAPI(title="Topic Manager", version="1.0.0")


class Topic(BaseModel):
    topic_id: Optional[str] = None
    title: str
    description: str
    keywords: List[str] = []
    content_type: str
    platform_assignment: Optional[Dict[str, bool]] = None


TOPICS: Dict[str, Topic] = {}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "topic-manager", "version": "1.0.0"}


@app.post("/topics/manual")
async def add_manual_topic(topic: Topic):
    topic_id = f"t_{len(TOPICS)+1:06d}"
    topic.topic_id = topic_id
    TOPICS[topic_id] = topic
    return {"status": "created", "topic_id": topic_id}


@app.get("/topics/{topic_id}")
async def get_topic(topic_id: str):
    t = TOPICS.get(topic_id)
    if not t:
        return {"error": "not_found"}
    return t


@app.get("/topics/suggestions")
async def get_topic_suggestions(limit: int = 10) -> Dict[str, List[Dict[str, str]]]:
    suggestions = [
        {
            "topic_id": f"sug_{i+1}",
            "title": f"AI trend #{i+1}",
            "description": "Auto-generated suggestion",
            "suggested_platforms": ["linkedin", "twitter"],
            "engagement_prediction": 0.6 + (i * 0.01),
        }
        for i in range(min(limit, 10))
    ]
    return {"suggestions": suggestions}
