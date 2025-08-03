"""CrewAI Knowledge Engine - Main Query Interface"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import structlog

from .cache import CacheManager, CacheConfig, MemoryCache, RedisCache
from .storage import ChromaClient, ChromaDocument, SearchResult

logger = structlog.get_logger()


class QuerySource(Enum):
    """Available query sources"""
    CACHE = "cache"
    VECTOR = "vector"
    MARKDOWN = "markdown"
    WEB = "web"


@dataclass
class QueryParams:
    """Query parameters"""
    query: str
    limit: int = 10
    score_threshold: float = 0.35
    sources: Optional[List[QuerySource]] = None
    use_cache: bool = True
    metadata_filters: Optional[Dict[str, Any]] = None


@dataclass
class KnowledgeResult:
    """Knowledge query result"""
    content: str
    title: str
    source_type: str
    url: Optional[str]
    metadata: Dict[str, Any]
    score: float
    source: QuerySource


@dataclass
class QueryResponse:
    """Complete query response"""
    results: List[KnowledgeResult]
    total_count: int
    query_time_ms: float
    from_cache: bool
    sources_used: List[QuerySource]
    query_params: QueryParams


class CrewAIKnowledgeBase:
    """Main knowledge base interface with 4-layer fallback strategy"""
    
    def __init__(
        self,
        cache_config: Optional[CacheConfig] = None,
        chroma_host: str = "localhost",
        chroma_port: int = 8000,
        redis_url: str = "redis://localhost:6379"
    ):
        # Configuration
        self.cache_config = cache_config or CacheConfig()
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.redis_url = redis_url
        
        # Components
        self.cache_manager: Optional[CacheManager] = None
        self.vector_store: Optional[ChromaClient] = None
        
        # Statistics
        self._stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "vector_hits": 0,
            "markdown_hits": 0,
            "web_hits": 0,
            "avg_query_time_ms": 0.0,
            "error_count": 0
        }
        
        # Health status
        self._health = {
            "status": "initializing",
            "cache": "unknown",
            "vector_store": "unknown",
            "last_check": None
        }
    
    async def initialize(self) -> None:
        """Initialize all components"""
        try:
            logger.info("Initializing CrewAI Knowledge Base")
            
            # Initialize cache manager
            await self._initialize_cache()
            
            # Initialize vector store
            await self._initialize_vector_store()
            
            # Update health status
            self._health["status"] = "healthy"
            self._health["last_check"] = time.time()
            
            logger.info(
                "CrewAI Knowledge Base initialized successfully",
                cache_enabled=self.cache_manager is not None,
                vector_store_enabled=self.vector_store is not None
            )
            
        except Exception as e:
            self._health["status"] = "unhealthy"
            logger.error("Failed to initialize knowledge base", error=str(e))
            raise
    
    async def _initialize_cache(self) -> None:
        """Initialize cache components"""
        try:
            # Create cache instances
            memory_cache = None
            redis_cache = None
            
            if self.cache_config.memory_enabled:
                memory_cache = MemoryCache(
                    default_ttl_seconds=self.cache_config.memory_ttl
                )
            
            if self.cache_config.redis_enabled:
                redis_cache = RedisCache(
                    redis_url=self.redis_url,
                    default_ttl_seconds=self.cache_config.redis_ttl
                )
            
            # Initialize cache manager
            self.cache_manager = CacheManager(self.cache_config)
            await self.cache_manager.initialize(memory_cache, redis_cache)
            
            self._health["cache"] = "healthy"
            logger.info("Cache system initialized")
            
        except Exception as e:
            self._health["cache"] = "unhealthy"
            logger.error("Failed to initialize cache", error=str(e))
            # Don't raise - cache is optional
    
    async def _initialize_vector_store(self) -> None:
        """Initialize vector store"""
        try:
            self.vector_store = ChromaClient(
                host=self.chroma_host,
                port=self.chroma_port
            )
            await self.vector_store.initialize()
            
            self._health["vector_store"] = "healthy"
            logger.info("Vector store initialized")
            
        except Exception as e:
            self._health["vector_store"] = "unhealthy"
            logger.error("Failed to initialize vector store", error=str(e))
            # Don't raise - we can fallback to other sources
    
    async def query(self, params: QueryParams) -> QueryResponse:
        """Execute query with 4-layer fallback strategy"""
        start_time = time.time()
        
        try:
            self._stats["total_queries"] += 1
            
            logger.info(
                "Executing knowledge query",
                query=params.query[:100],  # Truncate for logging
                sources=params.sources,
                use_cache=params.use_cache
            )
            
            # Determine query strategy
            sources_to_try = params.sources or [
                QuerySource.CACHE,
                QuerySource.VECTOR,
                QuerySource.MARKDOWN,
                QuerySource.WEB
            ]
            
            results = []
            sources_used = []
            from_cache = False
            
            # Execute fallback strategy
            for source in sources_to_try:
                if source == QuerySource.CACHE and params.use_cache:
                    cache_results = await self._query_cache(params)
                    if cache_results:
                        results = cache_results
                        sources_used.append(QuerySource.CACHE)
                        from_cache = True
                        self._stats["cache_hits"] += 1
                        break
                
                elif source == QuerySource.VECTOR:
                    vector_results = await self._query_vector_store(params)
                    if vector_results:
                        results.extend(vector_results)
                        sources_used.append(QuerySource.VECTOR)
                        self._stats["vector_hits"] += 1
                        
                        # If we have good results, stop here
                        if len(results) >= params.limit:
                            results = results[:params.limit]
                            break
                
                elif source == QuerySource.MARKDOWN:
                    markdown_results = await self._query_markdown(params)
                    if markdown_results:
                        results.extend(markdown_results)
                        sources_used.append(QuerySource.MARKDOWN)
                        self._stats["markdown_hits"] += 1
                        
                        if len(results) >= params.limit:
                            results = results[:params.limit]
                            break
                
                elif source == QuerySource.WEB:
                    web_results = await self._query_web(params)
                    if web_results:
                        results.extend(web_results)
                        sources_used.append(QuerySource.WEB)
                        self._stats["web_hits"] += 1
                        break
            
            # Deduplicate and sort results
            results = self._deduplicate_results(results)
            results = self._sort_results(results)
            
            # Limit results
            if len(results) > params.limit:
                results = results[:params.limit]
            
            # Cache results if not from cache
            if not from_cache and results and self.cache_manager:
                await self._cache_results(params, results)
            
            # Calculate response time
            query_time_ms = (time.time() - start_time) * 1000
            self._update_avg_query_time(query_time_ms)
            
            response = QueryResponse(
                results=results,
                total_count=len(results),
                query_time_ms=query_time_ms,
                from_cache=from_cache,
                sources_used=sources_used,
                query_params=params
            )
            
            logger.info(
                "Query completed",
                query=params.query[:50],
                results_count=len(results),
                query_time_ms=round(query_time_ms, 2),
                from_cache=from_cache,
                sources_used=[s.value for s in sources_used]
            )
            
            return response
            
        except Exception as e:
            self._stats["error_count"] += 1
            logger.error(
                "Query execution failed",
                query=params.query[:50],
                error=str(e)
            )
            raise
    
    async def _query_cache(self, params: QueryParams) -> Optional[List[KnowledgeResult]]:
        """Query L1/L2 cache"""
        if not self.cache_manager:
            return None
        
        try:
            cached_results = await self.cache_manager.get_query_cache(
                params.query,
                {
                    "limit": params.limit,
                    "score_threshold": params.score_threshold,
                    "metadata_filters": params.metadata_filters
                }
            )
            
            if cached_results:
                logger.debug("Cache hit for query", query=params.query[:50])
                return [KnowledgeResult(**result) for result in cached_results]
            
            return None
            
        except Exception as e:
            logger.error("Cache query error", error=str(e))
            return None
    
    async def _query_vector_store(self, params: QueryParams) -> Optional[List[KnowledgeResult]]:
        """Query vector store (Chroma DB)"""
        if not self.vector_store:
            return None
        
        try:
            search_results = await self.vector_store.search(
                query=params.query,
                limit=params.limit,
                score_threshold=params.score_threshold,
                where=params.metadata_filters
            )
            
            results = []
            for search_result in search_results:
                doc = search_result.document
                
                result = KnowledgeResult(
                    content=doc.content,
                    title=doc.metadata.get("title", "Untitled"),
                    source_type=doc.metadata.get("source_type", "vector"),
                    url=doc.metadata.get("source_url"),
                    metadata=doc.metadata,
                    score=search_result.score,
                    source=QuerySource.VECTOR
                )
                results.append(result)
            
            logger.debug(
                "Vector store query completed",
                query=params.query[:50],
                results_count=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error("Vector store query error", error=str(e))
            return None
    
    async def _query_markdown(self, params: QueryParams) -> Optional[List[KnowledgeResult]]:
        """Query local markdown files (placeholder)"""
        # TODO: Implement markdown file search
        logger.debug("Markdown query not yet implemented")
        return None
    
    async def _query_web(self, params: QueryParams) -> Optional[List[KnowledgeResult]]:
        """Query web sources (placeholder)"""
        # TODO: Implement web API search
        logger.debug("Web query not yet implemented")
        return None
    
    def _deduplicate_results(self, results: List[KnowledgeResult]) -> List[KnowledgeResult]:
        """Remove duplicate results based on content similarity"""
        if not results:
            return results
        
        # Simple deduplication by title and source
        seen = set()
        deduplicated = []
        
        for result in results:
            key = (result.title, result.source_type)
            if key not in seen:
                seen.add(key)
                deduplicated.append(result)
        
        return deduplicated
    
    def _sort_results(self, results: List[KnowledgeResult]) -> List[KnowledgeResult]:
        """Sort results by relevance score"""
        return sorted(results, key=lambda x: x.score, reverse=True)
    
    async def _cache_results(self, params: QueryParams, results: List[KnowledgeResult]) -> None:
        """Cache query results"""
        if not self.cache_manager:
            return
        
        try:
            # Convert results to serializable format
            serializable_results = [
                {
                    "content": r.content,
                    "title": r.title,
                    "source_type": r.source_type,
                    "url": r.url,
                    "metadata": r.metadata,
                    "score": r.score,
                    "source": r.source.value
                }
                for r in results
            ]
            
            await self.cache_manager.set_query_cache(
                params.query,
                serializable_results,
                {
                    "limit": params.limit,
                    "score_threshold": params.score_threshold,
                    "metadata_filters": params.metadata_filters
                }
            )
            
        except Exception as e:
            logger.error("Failed to cache results", error=str(e))
    
    def _update_avg_query_time(self, query_time_ms: float) -> None:
        """Update average query time using exponential moving average"""
        alpha = 0.1  # Smoothing factor
        if self._stats["avg_query_time_ms"] == 0:
            self._stats["avg_query_time_ms"] = query_time_ms
        else:
            self._stats["avg_query_time_ms"] = (
                alpha * query_time_ms + 
                (1 - alpha) * self._stats["avg_query_time_ms"]
            )
    
    async def add_document(self, document: ChromaDocument) -> bool:
        """Add document to knowledge base"""
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return False
        
        try:
            await self.vector_store.add_documents([document])
            
            # Invalidate related cache entries
            if self.cache_manager:
                await self.cache_manager.invalidate_pattern("*", "queries")
            
            logger.info("Document added to knowledge base", doc_id=document.id)
            return True
            
        except Exception as e:
            logger.error("Failed to add document", doc_id=document.id, error=str(e))
            return False
    
    async def update_document(self, document: ChromaDocument) -> bool:
        """Update document in knowledge base"""
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return False
        
        try:
            await self.vector_store.update_document(document)
            
            # Invalidate related cache entries
            if self.cache_manager:
                await self.cache_manager.invalidate_pattern("*", "queries")
            
            logger.info("Document updated in knowledge base", doc_id=document.id)
            return True
            
        except Exception as e:
            logger.error("Failed to update document", doc_id=document.id, error=str(e))
            return False
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete document from knowledge base"""
        if not self.vector_store:
            logger.error("Vector store not initialized")
            return False
        
        try:
            await self.vector_store.delete_document(doc_id)
            
            # Invalidate related cache entries
            if self.cache_manager:
                await self.cache_manager.invalidate_pattern("*", "queries")
            
            logger.info("Document deleted from knowledge base", doc_id=doc_id)
            return True
            
        except Exception as e:
            logger.error("Failed to delete document", doc_id=doc_id, error=str(e))
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        stats = {
            "knowledge_base": self._stats.copy(),
            "health": self._health.copy(),
            "cache": None,
            "vector_store": None
        }
        
        try:
            if self.cache_manager:
                stats["cache"] = await self.cache_manager.get_stats()
            
            if self.vector_store:
                stats["vector_store"] = await self.vector_store.get_collection_stats()
            
            return stats
            
        except Exception as e:
            logger.error("Failed to get stats", error=str(e))
            return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health = {
            "status": "healthy",
            "timestamp": time.time(),
            "components": {
                "cache": None,
                "vector_store": None
            },
            "stats": self._stats
        }
        
        try:
            # Check cache health
            if self.cache_manager:
                cache_health = await self.cache_manager.health_check()
                health["components"]["cache"] = cache_health
                if cache_health["status"] != "healthy":
                    health["status"] = "degraded"
            
            # Check vector store health
            if self.vector_store:
                vector_health = await self.vector_store.health_check()
                health["components"]["vector_store"] = vector_health
                if vector_health["status"] != "healthy":
                    health["status"] = "degraded"
            
            # Update internal health status
            self._health["status"] = health["status"]
            self._health["last_check"] = health["timestamp"]
            
            return health
            
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def close(self) -> None:
        """Close all connections and cleanup"""
        try:
            if self.cache_manager:
                await self.cache_manager.close()
            
            if self.vector_store:
                await self.vector_store.close()
            
            logger.info("CrewAI Knowledge Base closed")
            
        except Exception as e:
            logger.error("Error closing knowledge base", error=str(e))