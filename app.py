from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="AI Writing Flow - Container First")

class ContentRequest(BaseModel):
    title: str
    content_type: str = "STANDARD"  # STANDARD, TECHNICAL, VIRAL
    platform: str = "LinkedIn"
    content_ownership: str = "EXTERNAL"  # EXTERNAL, ORIGINAL

@app.get("/")
def root():
    return {"status": "ok", "service": "ai-writing-flow"}

@app.get("/health")
def health():
    return {"status": "healthy", "container": "running"}

@app.post("/api/test-routing")
def test_routing(content: ContentRequest):
    """Test endpoint pokazujący że routing działa"""
    # Podstawowa logika routingu
    if content.content_ownership == "ORIGINAL":
        route = "skip_research_flow"
    elif content.content_type == "TECHNICAL":
        route = "technical_deep_dive_flow"
    elif content.content_type == "VIRAL":
        route = "viral_engagement_flow"
    else:
        route = "standard_editorial_flow"
    
    return {
        "status": "routed",
        "input": content.dict(),
        "route_decision": route,
        "skip_research": content.content_ownership == "ORIGINAL",
        "container_id": "ai-writing-flow-v1"
    }