"""FastAPI Routes for Knowledge Base API"""

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


class StatsResponse(BaseModel):
    """Statistics response"""
    knowledge_base: Dict[str, Any]
    cache: Optional[Dict[str, Any]]
    vector_store: Optional[Dict[str, Any]]
    health: Dict[str, Any]


class AddDocumentRequest(BaseModel):
    """Add document request"""
    content: str = Field(..., min_length=1, description="Document content")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    id: Optional[str] = Field(default=None, description="Document ID (auto-generated if not provided)")


class SyncRequest(BaseModel):
    """Sync request model"""
    sources: Optional[List[str]] = Field(default=None, description="Sources to sync")
    force: bool = Field(default=False, description="Force full resync")


# FastAPI App
app = FastAPI(
    title="Vector Wave Knowledge Base API",
    description="Hybrydowa baza wiedzy CrewAI z wielowarstwową architekturą cache + vector store",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency for getting knowledge base instance
def get_knowledge_base() -> CrewAIKnowledgeBase:
    """Get knowledge base dependency"""
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
            chroma_host="localhost",
            chroma_port=8000,
            redis_url="redis://localhost:6379"
        )
        
        await knowledge_base.initialize()
        
        logger.info("Knowledge base API initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize knowledge base API", error=str(e))
        # Don't raise - let the app start but mark as unhealthy


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global knowledge_base
    
    if knowledge_base:
        try:
            await knowledge_base.close()
            logger.info("Knowledge base closed")
        except Exception as e:
            logger.error("Error closing knowledge base", error=str(e))


# API Routes
@app.get("/", summary="Root endpoint")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Vector Wave Knowledge Base API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "query": "/api/v1/knowledge/query",
            "health": "/api/v1/knowledge/health",
            "stats": "/api/v1/knowledge/stats",
            "docs": "/docs"
        }
    }


@app.post(
    "/api/v1/knowledge/query",
    response_model=QueryResponseModel,
    summary="Query knowledge base",
    description="Search the knowledge base using multi-layer fallback strategy"
)
async def query_knowledge(
    request: QueryRequest,
    kb: CrewAIKnowledgeBase = Depends(get_knowledge_base)
) -> QueryResponseModel:
    """Query the knowledge base"""
    try:
        # Convert sources to QuerySource enum
        sources = None
        if request.sources:
            try:
                sources = [QuerySource(source) for source in request.sources]
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid source: {str(e)}"
                )
        
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
        
        # Convert response to API model
        return QueryResponseModel(
            results=[
                {
                    "content": result.content,
                    "title": result.title,
                    "source_type": result.source_type,
                    "url": result.url,
                    "metadata": result.metadata,
                    "score": result.score,
                    "source": result.source.value
                }
                for result in response.results
            ],
            total_count=response.total_count,
            query_time_ms=response.query_time_ms,
            from_cache=response.from_cache,
            sources_used=[source.value for source in response.sources_used],
            query_params={
                "query": params.query,
                "limit": params.limit,
                "score_threshold": params.score_threshold,
                "use_cache": params.use_cache
            }
        )
        
    except Exception as e:
        logger.error("Query failed", query=request.query[:50], error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Query execution failed: {str(e)}"
        )


@app.get(
    "/api/v1/knowledge/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of all knowledge base components"
)
async def health_check(
    kb: CrewAIKnowledgeBase = Depends(get_knowledge_base)
) -> HealthResponse:
    """Perform comprehensive health check"""
    try:
        health = await kb.health_check()
        return HealthResponse(**health)
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            timestamp=time.time(),
            components={},
            stats={},
        )


@app.get(
    "/api/v1/knowledge/stats",
    response_model=StatsResponse,
    summary="Get statistics",
    description="Get comprehensive statistics for the knowledge base"
)
async def get_stats(
    kb: CrewAIKnowledgeBase = Depends(get_knowledge_base)
) -> StatsResponse:
    """Get knowledge base statistics"""
    try:
        stats = await kb.get_stats()
        return StatsResponse(**stats)
        
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )


@app.post(
    "/api/v1/knowledge/documents",
    summary="Add document",
    description="Add a new document to the knowledge base"
)
async def add_document(
    request: AddDocumentRequest,
    kb: CrewAIKnowledgeBase = Depends(get_knowledge_base)
):
    """Add a document to the knowledge base"""
    try:
        import uuid
        
        # Generate ID if not provided
        doc_id = request.id or str(uuid.uuid4())
        
        # Create document
        document = ChromaDocument(
            id=doc_id,
            content=request.content,
            metadata=request.metadata
        )
        
        # Add to knowledge base
        success = await kb.add_document(document)
        
        if success:
            return {
                "status": "success",
                "document_id": doc_id,
                "message": "Document added successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to add document"
            )
            
    except Exception as e:
        logger.error("Failed to add document", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add document: {str(e)}"
        )


@app.delete(
    "/api/v1/knowledge/documents/{document_id}",
    summary="Delete document",
    description="Delete a document from the knowledge base"
)
async def delete_document(
    document_id: str,
    kb: CrewAIKnowledgeBase = Depends(get_knowledge_base)
):
    """Delete a document from the knowledge base"""
    try:
        success = await kb.delete_document(document_id)
        
        if success:
            return {
                "status": "success",
                "document_id": document_id,
                "message": "Document deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Document not found or could not be deleted"
            )
            
    except Exception as e:
        logger.error("Failed to delete document", doc_id=document_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@app.post(
    "/api/v1/knowledge/sync",
    summary="Trigger sync",
    description="Trigger manual synchronization of knowledge sources"
)
async def trigger_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    kb: CrewAIKnowledgeBase = Depends(get_knowledge_base)
):
    """Trigger manual synchronization (placeholder)"""
    # This is a placeholder - sync functionality would be implemented
    # in the sync module and called as a background task
    
    sync_job_id = f"sync_{int(time.time())}"
    
    # Add background task (placeholder)
    # background_tasks.add_task(perform_sync, request.sources, request.force)
    
    return {
        "status": "accepted",
        "sync_job_id": sync_job_id,
        "message": "Sync job queued (placeholder implementation)",
        "sources": request.sources or ["all"],
        "force": request.force
    }


@app.get(
    "/api/v1/knowledge/search",
    summary="Simple search endpoint",
    description="Simple GET-based search endpoint"
)
async def search_knowledge(
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=10, ge=1, le=100, description="Result limit"),
    threshold: float = Query(default=0.35, ge=0.0, le=1.0, description="Score threshold"),
    kb: CrewAIKnowledgeBase = Depends(get_knowledge_base)
):
    """Simple search endpoint for quick queries"""
    try:
        params = QueryParams(
            query=q,
            limit=limit,
            score_threshold=threshold,
            use_cache=True
        )
        
        response = await kb.query(params)
        
        # Return simplified response
        return {
            "query": q,
            "results": [
                {
                    "title": result.title,
                    "content": result.content[:200] + "..." if len(result.content) > 200 else result.content,
                    "score": round(result.score, 3),
                    "url": result.url
                }
                for result in response.results
            ],
            "total": response.total_count,
            "from_cache": response.from_cache,
            "query_time_ms": round(response.query_time_ms, 2)
        }
        
    except Exception as e:
        logger.error("Search failed", query=q, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


# Metrics endpoint for Prometheus
@app.get("/metrics", summary="Prometheus metrics")
async def metrics():
    """Prometheus metrics endpoint (placeholder)"""
    # This would integrate with prometheus_client to expose metrics
    return {"message": "Metrics endpoint placeholder"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)