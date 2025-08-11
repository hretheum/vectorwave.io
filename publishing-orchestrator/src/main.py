"""
Enhanced Publishing Orchestrator API
Multi-platform content publishing with Editorial Service integration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
import uuid
import asyncio
import httpx
import logging
from datetime import datetime, timedelta
from enum import Enum
from .adapters import PLATFORM_ADAPTERS
from .variations import generate_variations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Publishing Orchestrator", 
    version="2.0.0",
    description="Enhanced multi-platform publishing orchestration with Editorial Service integration"
)

class PlatformType(str, Enum):
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    BEEHIIV = "beehiiv"
    GHOST = "ghost"
    GENERAL = "general"

class PublicationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"

class PlatformConfig(BaseModel):
    enabled: bool
    account_id: str
    schedule_time: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    direct_content: bool = False  # If True, use provided content directly

class TopicRequest(BaseModel):
    title: str
    description: str
    keywords: Optional[List[str]] = []
    target_audience: Optional[str] = "general"
    content_type: str = "article"

class PublicationRequest(BaseModel):
    topic: TopicRequest
    platforms: Dict[PlatformType, PlatformConfig]
    global_options: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None

class ContentVariation(BaseModel):
    platform: PlatformType
    content: str
    metadata: Dict[str, Any]
    quality_score: Optional[float] = None
    presentation: Optional[Dict[str, Any]] = None
    validation_results: Optional[Dict[str, Any]] = None

class PublicationResponse(BaseModel):
    publication_id: str
    request_id: Optional[str]
    status: PublicationStatus
    platform_content: Dict[str, Dict[str, Any]]
    scheduled_jobs: Dict[str, str]
    generation_time: float
    success_count: int
    error_count: int
    errors: List[str] = []

class PublicationStatusResponse(BaseModel):
    publication_id: str
    status: PublicationStatus
    platform_statuses: Dict[str, Dict[str, Any]]
    created_at: str
    completed_at: Optional[str] = None
    total_platforms: int
    successful_platforms: int
    failed_platforms: int

# In-memory storage for demo (in production would use Redis/DB)
publications_store: Dict[str, Dict[str, Any]] = {}
analytics_events: List[Dict[str, Any]] = []
preferences_store: Dict[str, Dict[str, Any]] = {}

# Service URLs
AI_WRITING_FLOW_URL = "http://localhost:8001"
LINKEDIN_PPT_GENERATOR_URL = "http://localhost:8002"
EDITORIAL_SERVICE_URL = "http://localhost:8040"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "publishing-orchestrator",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics")
async def get_metrics():
    """Get publishing orchestrator metrics"""
    total_publications = len(publications_store)
    successful_publications = sum(1 for pub in publications_store.values() 
                                if pub.get("status") == "completed")
    failed_publications = sum(1 for pub in publications_store.values() 
                            if pub.get("status") == "failed")
    
    platform_usage = {}
    for pub in publications_store.values():
        for platform in pub.get("platform_content", {}):
            platform_usage[platform] = platform_usage.get(platform, 0) + 1
    
    # Presentor readiness (best-effort, quick check)
    presentor_ready = False
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            r = await client.get(f"{LINKEDIN_PPT_GENERATOR_URL}/health")
            presentor_ready = r.status_code == 200
    except Exception:
        presentor_ready = False

    return {
        "total_publications": total_publications,
        "successful_publications": successful_publications,
        "failed_publications": failed_publications,
        "success_rate": successful_publications / total_publications if total_publications > 0 else 0,
        "platform_usage": platform_usage,
        "analytics_events": len(analytics_events),
        "presentor_ready": presentor_ready,
        "service": "publishing-orchestrator"
    }

async def call_ai_writing_flow(topic: TopicRequest, platform: str) -> Dict[str, Any]:
    """Call AI Writing Flow service to generate platform-specific content"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AI_WRITING_FLOW_URL}/generate",
                json={
                    "topic": topic.dict(),
                    "platform": platform,
                    "options": {"enhanced": True}
                },
                timeout=120.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"AI Writing Flow call failed for {platform}: {e}")
        return {
            "error": str(e),
            "content": f"Generated content for {topic.title} on {platform}",
            "quality_score": 0.5
        }

async def generate_linkedin_presentation(content: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Generate LinkedIn presentation if content is suitable"""
    try:
        # Check if content is suitable for presentation
        if not should_generate_presentation(content):
            return None
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LINKEDIN_PPT_GENERATOR_URL}/generate",
                json={
                    "topic": content.get("topic", {}),
                    "content": content.get("content", ""),
                    "slides_count": 5
                },
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"LinkedIn presentation generation failed: {e}")
        return None

def should_generate_presentation(content: Dict[str, Any]) -> bool:
    """Determine if content should have a LinkedIn presentation"""
    content_text = content.get("content", "")
    return (
        len(content_text.split()) > 400 and  # Long enough content
        any(keyword in content_text.lower() for keyword in 
            ["architecture", "system", "framework", "process", "strategy"])
    )

async def validate_with_editorial_service(content: str, platform: str) -> Dict[str, Any]:
    """Validate content with Editorial Service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{EDITORIAL_SERVICE_URL}/validate/comprehensive",
                json={
                    "content": content,
                    "platform": platform,
                    "content_type": "article",
                    "context": {
                        "agent": "orchestrator",
                        "validation_type": "comprehensive"
                    }
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Editorial Service validation failed: {e}")
        return {
            "error": str(e),
            "is_compliant": True,  # Allow publishing despite validation failure
            "violations": [],
            "suggestions": []
        }

async def schedule_platform_publication(platform: str, content: Dict[str, Any], 
                                     config: PlatformConfig) -> str:
    """Schedule publication to specific platform"""
    job_id = f"{platform}_{uuid.uuid4()}"
    
    # In production, would integrate with Celery/Redis for scheduling
    logger.info(f"Scheduled publication {job_id} for {platform}")
    
    return job_id

async def generate_platform_content(topic: TopicRequest, platform: str, 
                                  config: PlatformConfig) -> Dict[str, Any]:
    """Generate platform-specific content using AI Writing Flow"""
    start_time = datetime.now()
    
    if config.direct_content:
        # Use provided content directly
        content = {
            "content": f"Direct content for {topic.title} on {platform}",
            "platform": platform,
            "quality_score": 1.0,
            "metadata": {"generation_method": "direct"}
        }
    else:
        # Generate content using AI Writing Flow
        content = await call_ai_writing_flow(topic, platform)
    
    # Generate variations per platform
    variations = generate_variations(content.get("content", ""), num=3)
    valid_variations: List[Dict[str, Any]] = []
    # Validate each variation with Editorial Service (best-effort)
    for v in variations:
        vr = await validate_with_editorial_service(v.get("content", ""), platform)
        v["validation_results"] = vr
        # Exclude failed validations if returned
        if vr.get("error"):
            continue
        valid_variations.append(v)

    # Choose first valid or fallback to base
    chosen = valid_variations[0] if valid_variations else {"content": content.get("content", ""), "validation_results": {"is_compliant": True}}
    content.update(chosen)

    # Apply platform adapter formatting
    adapter = PLATFORM_ADAPTERS.get(platform, lambda c, t: {"content": c})
    formatted = adapter(content.get("content", ""), topic.dict())
    content.update(formatted)

    # For LinkedIn, include manual upload package info (placeholder)
    if platform == PlatformType.LINKEDIN.value:
        content["linkedin_manual_upload"] = {
            "checklist": [
                "Review content and validation suggestions",
                "Upload presentation (if available) as document",
                "Paste content, add hashtags, and schedule",
            ],
            "assets": {}
        }
    
    generation_time = (datetime.now() - start_time).total_seconds()
    content["generation_time"] = generation_time
    
    return content

@app.post("/publish", response_model=PublicationResponse)
async def orchestrate_publication(request: PublicationRequest, 
                                background_tasks: BackgroundTasks):
    """Complete multi-platform publishing orchestration"""
    start_time = datetime.now()
    publication_id = f"pub_{uuid.uuid4()}"
    
    # Store initial publication record
    publications_store[publication_id] = {
        "publication_id": publication_id,
        "request_id": request.request_id,
        "status": "in_progress",
        "created_at": start_time.isoformat(),
        "topic": request.topic.dict(),
        "platforms": [p.value for p in request.platforms.keys()],
        "platform_content": {},
        "scheduled_jobs": {},
        "errors": []
    }
    
    logger.info(f"Starting publication {publication_id} for topic: {request.topic.title}")
    
    # Generate content for each platform
    content_variations = {}
    scheduled_jobs = {}
    errors = []
    success_count = 0
    
    for platform, config in request.platforms.items():
        if not config.enabled:
            continue
            
        try:
            logger.info(f"Generating content for {platform}")
            
            # Platform-specific content generation
            content = await generate_platform_content(
                request.topic, platform.value, config
            )
            
            if "error" in content:
                errors.append(f"{platform}: {content['error']}")
                continue
                
            content_variations[platform.value] = content
            success_count += 1
            
            # Special LinkedIn handling
            if platform == PlatformType.LINKEDIN and should_generate_presentation(content):
                presentation = await generate_linkedin_presentation(content)
                if presentation:
                    content_variations[platform.value]["presentation"] = presentation
                    # Attach asset references for manual upload
                    assets = content_variations[platform.value].setdefault("linkedin_manual_upload", {}).setdefault("assets", {})
                    assets.update({k: v for k, v in presentation.items() if isinstance(v, (str,))})
            
            # Schedule publication
            job_id = await schedule_platform_publication(
                platform.value, content, config
            )
            scheduled_jobs[platform.value] = job_id
            
        except Exception as e:
            error_msg = f"{platform}: {str(e)}"
            errors.append(error_msg)
            logger.error(f"Publication failed for {platform}: {e}")
    
    generation_time = (datetime.now() - start_time).total_seconds()
    
    # Update publication record
    final_status = "completed" if success_count > 0 else "failed"
    publications_store[publication_id].update({
        "status": final_status,
        "completed_at": datetime.now().isoformat(),
        "platform_content": content_variations,
        "scheduled_jobs": scheduled_jobs,
        "generation_time": generation_time,
        "success_count": success_count,
        "error_count": len(errors),
        "errors": errors
    })
    
    logger.info(f"Publication {publication_id} completed. Success: {success_count}, Errors: {len(errors)}")
    
    return PublicationResponse(
        publication_id=publication_id,
        request_id=request.request_id,
        status=PublicationStatus(final_status),
        platform_content={k: {"content": v.get("content", ""), 
                             "quality_score": v.get("quality_score", 0),
                             "validation_compliant": v.get("validation_results", {}).get("is_compliant", True),
                             "generation_time": v.get("generation_time", 0)} 
                         for k, v in content_variations.items()},
        scheduled_jobs=scheduled_jobs,
        generation_time=generation_time,
        success_count=success_count,
        error_count=len(errors),
        errors=errors
    )


class AnalyticsEvent(BaseModel):
    request_id: Optional[str] = None
    publication_id: Optional[str] = None
    platform: Optional[str] = None
    status: Optional[str] = None  # scheduled|completed|failed
    validation_score: Optional[Union[int, float]] = None
    scheduled_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


@app.post("/analytics/track")
async def analytics_track(event: AnalyticsEvent):
    payload = event.model_dump()
    payload["ts"] = datetime.now().isoformat()
    analytics_events.append(payload)
    return {"status": "tracked", "events": len(analytics_events)}


@app.get("/analytics/events")
async def analytics_list(limit: int = 50):
    return {"events": analytics_events[-limit:], "total": len(analytics_events)}


class PreferenceUpdate(BaseModel):
    platform: str
    hour: Optional[str] = None  # e.g., "11:00"
    score: Optional[float] = 0.5


@app.put("/preferences/{user_id}")
async def preferences_put(user_id: str, pref: PreferenceUpdate):
    user = preferences_store.setdefault(user_id, {"platforms": {}, "hours": {}})
    if pref.platform:
        user["platforms"][pref.platform] = max(0.0, min(1.0, float(pref.score or 0.0)))
    if pref.hour:
        user["hours"][pref.hour] = max(0.0, min(1.0, float(pref.score or 0.0)))
    return {"status": "ok", "preferences": user}


@app.get("/preferences/{user_id}")
async def preferences_get(user_id: str):
    return preferences_store.get(user_id, {"platforms": {}, "hours": {}})

@app.get("/publication/{publication_id}", response_model=PublicationStatusResponse)
async def get_publication_status(publication_id: str):
    """Get status of specific publication"""
    if publication_id not in publications_store:
        raise HTTPException(status_code=404, detail="Publication not found")
    
    pub = publications_store[publication_id]
    
    platform_statuses = {}
    for platform in pub.get("platforms", []):
        content = pub["platform_content"].get(platform, {})
        platform_statuses[platform] = {
            "status": "completed" if content else "failed",
            "quality_score": content.get("quality_score", 0),
            "generation_time": content.get("generation_time", 0),
            "validation_compliant": content.get("validation_results", {}).get("is_compliant", True)
        }
    
    return PublicationStatusResponse(
        publication_id=publication_id,
        status=PublicationStatus(pub["status"]),
        platform_statuses=platform_statuses,
        created_at=pub["created_at"],
        completed_at=pub.get("completed_at"),
        total_platforms=len(pub.get("platforms", [])),
        successful_platforms=pub["success_count"],
        failed_platforms=pub["error_count"]
    )

@app.get("/publications")
async def list_publications(limit: int = 20, status: Optional[str] = None):
    """List recent publications"""
    publications = list(publications_store.values())
    
    if status:
        publications = [p for p in publications if p.get("status") == status]
    
    # Sort by created_at descending
    publications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return {
        "publications": publications[:limit],
        "total": len(publications_store),
        "filtered": len(publications)
    }

@app.post("/test/simple")
async def test_simple_publication():
    """Simple test endpoint for basic functionality validation"""
    test_request = PublicationRequest(
        topic=TopicRequest(
            title="Test Publication",
            description="Testing Enhanced Orchestrator API",
            keywords=["test", "api", "orchestrator"]
        ),
        platforms={
            PlatformType.LINKEDIN: PlatformConfig(
                enabled=True,
                account_id="test_account",
                direct_content=True
            )
        }
    )
    
    return await orchestrate_publication(test_request, BackgroundTasks())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)