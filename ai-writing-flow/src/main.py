"""
AI Writing Flow Service - Human-assisted content generation with CrewAI checkpoints
"""
import os
import time
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import structlog
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
request_count = Counter(
    'aiwf_requests_total',
    'Total AI Writing Flow requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'aiwf_request_duration_seconds',
    'AI Writing Flow request duration',
    ['method', 'endpoint']
)

generation_count = Counter(
    'aiwf_generation_total',
    'Total content generations',
    ['checkpoint', 'status']
)

editorial_validation_duration = Histogram(
    'aiwf_editorial_validation_duration_seconds',
    'Editorial Service validation call duration'
)

# Application state
app_state = {
    "startup_time": None,
    "editorial_client": None,
    "health_status": "starting",
}

# --- Request/Response Models ---
class TopicInput(BaseModel):
    title: str
    description: str
    viral_score: Optional[float] = 0.0
    content_type: Optional[str] = "STANDALONE"
    content_ownership: Optional[str] = "ORIGINAL"
    editorial_recommendations: Optional[List[str]] = []

class GenerateRequest(BaseModel):
    topic: TopicInput
    platform: Optional[str] = "linkedin"
    mode: Optional[str] = "selective"  # selective or comprehensive
    checkpoints_enabled: Optional[bool] = True
    skip_research: Optional[bool] = False
    user_id: Optional[str] = None

class GenerateResponse(BaseModel):
    content_id: str
    status: str
    content: Optional[str] = None
    checkpoints_passed: Dict[str, bool] = {}
    validation_results: Dict[str, Any] = {}
    platform_variants: Dict[str, str] = {}
    metadata: Optional[Dict[str, Any]] = None
    processing_time_ms: float
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    uptime_seconds: float
    dependencies: Dict[str, Any]
    timestamp: datetime

# --- Editorial Service Client ---
class EditorialServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)
        self._healthy = False
        
    async def health_check(self) -> Dict[str, Any]:
        """Check Editorial Service health"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                self._healthy = data.get("status") == "healthy"
                return {"status": "healthy", "details": data}
            return {"status": "unhealthy", "code": response.status_code}
        except Exception as e:
            self._healthy = False
            return {"status": "unavailable", "error": str(e)}
    
    async def validate_selective(self, content: str, checkpoint: str, platform: str = None) -> Dict[str, Any]:
        """Call Editorial Service selective validation"""
        try:
            start = time.time()
            payload = {
                "content": content,
                "mode": "selective",
                "checkpoint": checkpoint,
                "platform": platform
            }
            response = await self.client.post(
                f"{self.base_url}/validate/selective",
                json=payload
            )
            
            duration = time.time() - start
            editorial_validation_duration.observe(duration)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning("Editorial validation failed", 
                             status_code=response.status_code,
                             checkpoint=checkpoint)
                return None
        except Exception as e:
            logger.error("Editorial validation error", error=str(e))
            return None
    
    async def validate_comprehensive(self, content: str, platform: str = None) -> Dict[str, Any]:
        """Call Editorial Service comprehensive validation"""
        try:
            start = time.time()
            payload = {
                "content": content,
                "mode": "comprehensive",
                "platform": platform
            }
            response = await self.client.post(
                f"{self.base_url}/validate/comprehensive",
                json=payload
            )
            
            duration = time.time() - start
            editorial_validation_duration.observe(duration)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning("Editorial comprehensive validation failed", 
                             status_code=response.status_code)
                return None
        except Exception as e:
            logger.error("Editorial comprehensive validation error", error=str(e))
            return None

# --- Content Generation Logic ---
async def generate_content_with_checkpoints(
    topic: TopicInput,
    editorial_client: EditorialServiceClient,
    platform: str = "linkedin",
    checkpoints_enabled: bool = True,
    skip_research: bool = False
) -> Dict[str, Any]:
    """
    Generate content with AI Writing Flow checkpoints using selective validation
    """
    checkpoints_passed = {}
    validation_results = {}
    
    # Pre-writing checkpoint
    if checkpoints_enabled and editorial_client._healthy:
        pre_validation = await editorial_client.validate_selective(
            content=f"Planning to write about: {topic.title}. {topic.description}",
            checkpoint="pre-writing",
            platform=platform
        )
        if pre_validation:
            validation_results["pre-writing"] = pre_validation
            checkpoints_passed["pre-writing"] = pre_validation.get("rule_count", 0) >= 3
            generation_count.labels(checkpoint="pre-writing", 
                                  status="pass" if checkpoints_passed["pre-writing"] else "fail").inc()
    
    # Research phase (can be skipped for ORIGINAL content)
    research_content = ""
    if not skip_research and topic.content_ownership == "EXTERNAL":
        # Simulate research agent work
        research_content = f"Research findings for {topic.title}: Industry trends, key insights, expert opinions..."
        logger.info("Research phase completed", topic=topic.title)
    
    # Mid-writing checkpoint
    draft_content = f"""
    # {topic.title}
    
    {topic.description}
    
    {research_content}
    
    ## Key Points
    - Innovation in the field
    - Market trends and analysis
    - Future predictions
    
    ## Conclusion
    This content explores the latest developments and provides actionable insights.
    """
    
    if checkpoints_enabled and editorial_client._healthy:
        mid_validation = await editorial_client.validate_selective(
            content=draft_content[:500],  # Send excerpt for validation
            checkpoint="mid-writing",
            platform=platform
        )
        if mid_validation:
            validation_results["mid-writing"] = mid_validation
            checkpoints_passed["mid-writing"] = mid_validation.get("rule_count", 0) >= 3
            generation_count.labels(checkpoint="mid-writing",
                                  status="pass" if checkpoints_passed["mid-writing"] else "fail").inc()
    
    # Style and quality refinement
    final_content = draft_content  # In real implementation, this would go through style crew
    
    # Post-writing checkpoint
    if checkpoints_enabled and editorial_client._healthy:
        post_validation = await editorial_client.validate_selective(
            content=final_content,
            checkpoint="post-writing",
            platform=platform
        )
        if post_validation:
            validation_results["post-writing"] = post_validation
            checkpoints_passed["post-writing"] = post_validation.get("rule_count", 0) >= 3
            generation_count.labels(checkpoint="post-writing",
                                  status="pass" if checkpoints_passed["post-writing"] else "fail").inc()
    
    # Platform variants
    platform_variants = {
        "linkedin": final_content,
        "twitter": final_content[:280] + "...",  # Simplified for demo
        "medium": final_content
    }
    
    return {
        "content": final_content,
        "checkpoints_passed": checkpoints_passed,
        "validation_results": validation_results,
        "platform_variants": platform_variants
    }

# --- FastAPI Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app_state["startup_time"] = time.time()
    logger.info("Starting AI Writing Flow Service", version="1.0.0")
    
    # Initialize Editorial Service client
    editorial_url = os.getenv('EDITORIAL_SERVICE_URL', 'http://editorial-service:8040')
    app_state["editorial_client"] = EditorialServiceClient(editorial_url)
    
    # Check Editorial Service health
    health_result = await app_state["editorial_client"].health_check()
    if health_result["status"] == "healthy":
        logger.info("Editorial Service connection established", url=editorial_url)
        app_state["health_status"] = "healthy"
    else:
        logger.warning("Editorial Service unavailable, running in degraded mode", 
                      result=health_result)
        app_state["health_status"] = "degraded"
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Writing Flow Service")
    if app_state["editorial_client"]:
        await app_state["editorial_client"].client.aclose()

# --- FastAPI Application ---
app = FastAPI(
    title="AI Writing Flow Service",
    description="Human-assisted content generation with CrewAI checkpoints",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('CORS_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# --- Endpoints ---
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - app_state["startup_time"] if app_state["startup_time"] else 0
    
    # Check Editorial Service
    editorial_health = {"status": "unavailable"}
    if app_state["editorial_client"]:
        editorial_health = await app_state["editorial_client"].health_check()
    
    # Determine overall status
    if editorial_health["status"] == "healthy":
        status = "healthy"
    else:
        status = "degraded"  # Can still function without Editorial Service
    
    return HealthResponse(
        status=status,
        service="ai-writing-flow",
        version="1.0.0",
        environment=os.getenv('ENVIRONMENT', 'development'),
        uptime_seconds=uptime,
        dependencies={
            "editorial_service": editorial_health
        },
        timestamp=datetime.utcnow()
    )

@app.post("/generate", response_model=GenerateResponse)
async def generate_content(request: GenerateRequest):
    """
    Generate content with AI Writing Flow
    Supports both selective (with checkpoints) and comprehensive validation
    """
    start_time = time.time()
    content_id = f"aiwf_{int(time.time())}_{request.topic.title[:10].replace(' ', '_')}"
    
    try:
        # Get editorial client
        editorial_client = app_state["editorial_client"]
        
        if request.mode == "selective" or request.checkpoints_enabled:
            # Generate with checkpoints (selective validation)
            result = await generate_content_with_checkpoints(
                topic=request.topic,
                editorial_client=editorial_client,
                platform=request.platform,
                checkpoints_enabled=request.checkpoints_enabled,
                skip_research=request.skip_research
            )
        else:
            # Simple generation with comprehensive validation at the end
            content = f"# {request.topic.title}\n\n{request.topic.description}\n\n[Content generated without checkpoints]"
            
            validation = None
            if editorial_client and editorial_client._healthy:
                validation = await editorial_client.validate_comprehensive(
                    content=content,
                    platform=request.platform
                )
            
            result = {
                "content": content,
                "checkpoints_passed": {},
                "validation_results": {"comprehensive": validation} if validation else {},
                "platform_variants": {request.platform: content}
            }
        
        processing_time = (time.time() - start_time) * 1000
        
        return GenerateResponse(
            content_id=content_id,
            status="completed",
            content=result["content"],
            checkpoints_passed=result["checkpoints_passed"],
            validation_results=result["validation_results"],
            platform_variants=result["platform_variants"],
            metadata={
                "topic": request.topic.dict(),
                "mode": request.mode,
                "user_id": request.user_id
            },
            processing_time_ms=processing_time,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error("Content generation failed", error=str(e), topic=request.topic.title)
        processing_time = (time.time() - start_time) * 1000
        
        return GenerateResponse(
            content_id=content_id,
            status="failed",
            content=None,
            metadata={"error": str(e)},
            processing_time_ms=processing_time,
            timestamp=datetime.utcnow()
        )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "ai-writing-flow",
        "version": "1.0.0",
        "status": app_state["health_status"],
        "endpoints": {
            "health": "/health",
            "generate": "/generate",
            "metrics": "/metrics"
        }
    }

# --- Main entry point ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv('SERVICE_PORT', '8003')),
        log_level=os.getenv('LOG_LEVEL', 'info').lower()
    )