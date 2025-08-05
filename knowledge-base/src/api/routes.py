"""FastAPI Routes for Knowledge Base API"""

import os
import time
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog

from ..knowledge_engine import (
    CrewAIKnowledgeBase, 
    QueryParams, 
    QueryResponse, 
    QuerySource, 
    KnowledgeResult
)
from ..cache import CacheConfig
from ..storage import ChromaDocument

logger = structlog.get_logger()

# Global knowledge base instance
knowledge_base: Optional[CrewAIKnowledgeBase] = None


# Pydantic Models
class QueryRequest(BaseModel):
    """Query request model"""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    score_threshold: float = Field(default=0.35, ge=0.0, le=1.0, description="Minimum relevance score")
    sources: Optional[List[str]] = Field(default=None, description="Specific sources to search")
    use_cache: bool = Field(default=True, description="Use cache for faster responses")
    metadata_filters: Optional[Dict[str, Any]] = Field(default=None, description="Metadata filters")


class QueryResponseModel(BaseModel):
    """Query response model"""
    results: List[Dict[str, Any]]
    total_count: int
    query_time_ms: float
    from_cache: bool
    sources_used: List[str]
    query_params: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: float
    components: Dict[str, Any]
    stats: Dict[str, Any]


class SyncResponse(BaseModel):
    """Sync response model"""
    status: str
    message: str
    job_id: Optional[str] = None


# FastAPI app
app = FastAPI(
    title="CrewAI Knowledge Base API",
    description="Vector-based knowledge retrieval system for CrewAI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependencies
async def get_knowledge_base() -> CrewAIKnowledgeBase:
    """Get initialized knowledge base instance"""
    if knowledge_base is None:
        raise HTTPException(
            status_code=503,
            detail="Knowledge base not initialized"
        )
    return knowledge_base


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize knowledge base on startup"""
    global knowledge_base
    
    try:
        logger.info("Initializing knowledge base API")
        
        # Get configuration from environment variables
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        logger.info("Using configuration", 
                   chroma_host=chroma_host, 
                   chroma_port=chroma_port, 
                   redis_url=redis_url)
        
        # Create cache configuration
        cache_config = CacheConfig(
            memory_enabled=True,
            redis_enabled=True,
            memory_ttl=300,
            redis_ttl=3600
        )
        
        # Initialize knowledge base
        knowledge_base = CrewAIKnowledgeBase(
            cache_config=cache_config,
            chroma_host=chroma_host,
            chroma_port=chroma_port,
            redis_url=redis_url
        )
        
        await knowledge_base.initialize()
        
        logger.info("Knowledge base API initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize knowledge base API", error=str(e))
        # Don't raise - let the app start but mark as unhealthy


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "CrewAI Knowledge Base API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/api/v1/knowledge/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    start_time = time.time()
    
    try:
        kb = await get_knowledge_base()
        health_data = await kb.health_check()
        
        response_time = (time.time() - start_time) * 1000
        health_data["stats"]["response_time_ms"] = response_time
        
        return HealthResponse(**health_data)
        
    except HTTPException:
        # Knowledge base not initialized
        return HealthResponse(
            status="unhealthy",
            timestamp=time.time(),
            components={
                "cache": {"status": "unknown"},
                "vector_store": {"status": "unknown"}
            },
            stats={"error": "Knowledge base not initialized"}
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            timestamp=time.time(),
            components={
                "cache": {"status": "unknown"},
                "vector_store": {"status": "unknown"}
            },
            stats={"error": str(e)}
        )


@app.post("/api/v1/knowledge/query", response_model=QueryResponseModel)
async def query_knowledge(
    request: QueryRequest,
    kb: CrewAIKnowledgeBase = Depends(get_knowledge_base)
):
    """Query the knowledge base"""
    start_time = time.time()
    
    try:
        # Convert sources to QuerySource enum
        sources = None
        if request.sources:
            sources = [QuerySource(source) for source in request.sources if source in [s.value for s in QuerySource]]
        
        # Create query parameters
        params = QueryParams(
            query=request.query,
            limit=request.limit,
            score_threshold=request.score_threshold,
            sources=sources,
            use_cache=request.use_cache,
            metadata_filters=request.metadata_filters
        )
        
        # Execute query
        response = await kb.query(params)
        
        # Convert response to API format
        results = []
        for result in response.results:
            results.append({
                "content": result.content,
                "title": result.title,
                "source_type": result.source_type,
                "url": result.url,
                "metadata": result.metadata,
                "score": result.score,
                "source": result.source.value
            })
        
        query_time = (time.time() - start_time) * 1000
        
        return QueryResponseModel(
            results=results,
            total_count=response.total_count,
            query_time_ms=query_time,
            from_cache=response.from_cache,
            sources_used=[source.value for source in response.sources_used],
            query_params={
                "query": request.query,
                "limit": request.limit,
                "score_threshold": request.score_threshold,
                "use_cache": request.use_cache
            }
        )
        
    except Exception as e:
        logger.error("Query failed", error=str(e), query=request.query)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.post("/api/v1/knowledge/sync", response_model=SyncResponse)
async def sync_knowledge(
    source: Optional[str] = Query(None, description="Specific source to sync"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    kb: CrewAIKnowledgeBase = Depends(get_knowledge_base)
):
    """Trigger knowledge base synchronization"""
    try:
        # For now, return a placeholder response
        # In a full implementation, this would trigger actual sync
        return SyncResponse(
            status="accepted",
            message=f"Sync initiated for source: {source or 'all'}",
            job_id=None
        )
        
    except Exception as e:
        logger.error("Sync failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@app.get("/api/v1/knowledge/stats")
async def get_stats(kb: CrewAIKnowledgeBase = Depends(get_knowledge_base)):
    """Get knowledge base statistics"""
    try:
        stats = await kb.get_stats()
        return stats
        
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    # Placeholder for metrics
    return {"metrics": "not implemented yet"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
