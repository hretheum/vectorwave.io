"""
Topic Manager HTTP Client
Provides comprehensive interface to Topic Manager for dynamic topic discovery
Aligned with Vector Wave topic intelligence architecture
"""

import httpx
from typing import Dict, List, Optional, Any
import logging
import asyncio
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class TopicManagerClient:
    """
    HTTP client for Topic Manager communication
    Handles topic suggestions, research triggers, and auto-scraping
    """
    
    def __init__(self, base_url: str = "http://localhost:8041", timeout: float = 30.0):
        """
        Initialize Topic Manager client
        
        Args:
            base_url: Topic Manager base URL (default: http://localhost:8041)
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=50)
        )
        self._circuit_breaker_open = False
        self._failure_count = 0
        self._failure_threshold = 3
        self._last_failure_time = None
        self._recovery_timeout = 60  # seconds
        
    async def __aenter__(self):
        """Async context manager entry"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
        
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def _check_circuit_breaker(self):
        """Check if circuit breaker should be open or closed"""
        if not self._circuit_breaker_open:
            return True
            
        if self._last_failure_time:
            time_since_failure = (datetime.utcnow() - self._last_failure_time).total_seconds()
            if time_since_failure > self._recovery_timeout:
                logger.info("Topic Manager circuit breaker recovery timeout reached")
                self._circuit_breaker_open = False
                self._failure_count = 0
                return True
                
        return False
    
    async def _handle_failure(self, error: Exception):
        """Handle request failure and update circuit breaker state"""
        self._failure_count += 1
        self._last_failure_time = datetime.utcnow()
        
        if self._failure_count >= self._failure_threshold:
            self._circuit_breaker_open = True
            logger.error(f"Topic Manager circuit breaker opened after {self._failure_count} failures")
            
    async def _handle_success(self):
        """Handle successful request"""
        if self._failure_count > 0:
            self._failure_count = 0
            logger.info("Topic Manager request successful, resetting failure count")
    
    async def health_check(self) -> Dict:
        """
        Check Topic Manager health
        
        Returns:
            Dict with health status information
        """
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            await self._handle_success()
            return response.json()
        except httpx.HTTPError as e:
            await self._handle_failure(e)
            logger.error(f"Topic Manager health check failed: {e}")
            raise
    
    async def get_topic_suggestions(self,
                                   limit: int = 10,
                                   content_type: Optional[str] = None,
                                   domain: Optional[str] = None,
                                   platform: Optional[str] = None,
                                   trending_only: bool = False,
                                   min_engagement_score: float = 0.6) -> Dict:
        """
        Get AI-powered topic suggestions
        
        Args:
            limit: Number of suggestions to return
            content_type: Filter by content type (TUTORIAL, DEEP_DIVE, etc.)
            domain: Filter by domain (technology, AI, etc.)
            platform: Filter for specific platform suitability
            trending_only: Only return trending topics
            min_engagement_score: Minimum engagement prediction score
            
        Returns:
            Dict with topic suggestions and metadata
        """
        if not await self._check_circuit_breaker():
            raise Exception("Circuit breaker is open - Topic Manager unavailable")
            
        params = {
            "limit": limit,
            "trending_only": trending_only,
            "min_engagement_score": min_engagement_score
        }
        
        if content_type:
            params["content_type"] = content_type
        if domain:
            params["domain"] = domain
        if platform:
            params["platform"] = platform
        
        try:
            response = await self.client.get(
                f"{self.base_url}/topics/suggestions",
                params=params
            )
            response.raise_for_status()
            await self._handle_success()
            return response.json()
            
        except httpx.HTTPError as e:
            await self._handle_failure(e)
            logger.error(f"Topic suggestions request failed: {e}")
            raise
    
    async def add_manual_topic(self,
                              title: str,
                              description: str,
                              keywords: List[str],
                              content_type: str = "TUTORIAL",
                              domain: Optional[str] = None,
                              complexity_level: str = "intermediate",
                              target_audience: List[str] = None,
                              platform_preferences: Optional[Dict[str, bool]] = None) -> Dict:
        """
        Add manually curated topic with AI-powered platform assignment
        
        Args:
            title: Topic title
            description: Detailed description
            keywords: List of relevant keywords
            content_type: Type of content (TUTORIAL, DEEP_DIVE, etc.)
            domain: Topic domain
            complexity_level: Complexity (beginner, intermediate, advanced)
            target_audience: List of target audiences
            platform_preferences: Platform preferences
            
        Returns:
            Dict with topic creation result and platform assignments
        """
        if not await self._check_circuit_breaker():
            raise Exception("Circuit breaker is open - Topic Manager unavailable")
            
        payload = {
            "title": title,
            "description": description,
            "keywords": keywords,
            "content_type": content_type,
            "complexity_level": complexity_level,
            "target_audience": target_audience or [],
        }
        
        if domain:
            payload["domain"] = domain
        if platform_preferences:
            payload["platform_preferences"] = platform_preferences
        
        try:
            response = await self.client.post(
                f"{self.base_url}/topics/manual",
                json=payload
            )
            response.raise_for_status()
            await self._handle_success()
            return response.json()
            
        except httpx.HTTPError as e:
            await self._handle_failure(e)
            logger.error(f"Manual topic creation failed: {e}")
            raise
    
    async def trigger_research_discovery(self,
                                        agent: str = "research",
                                        domain: Optional[str] = None,
                                        keywords: List[str] = None) -> Dict:
        """
        Trigger research-driven topic discovery
        
        Args:
            agent: Name of the requesting agent
            domain: Domain to focus research on
            keywords: Keywords to guide research
            
        Returns:
            Dict with research trigger confirmation and potential topics
        """
        if not await self._check_circuit_breaker():
            raise Exception("Circuit breaker is open - Topic Manager unavailable")
            
        payload = {
            "agent": agent,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if domain:
            payload["domain"] = domain
        if keywords:
            payload["keywords"] = keywords
        
        try:
            response = await self.client.post(
                f"{self.base_url}/topics/research-trigger",
                json=payload
            )
            response.raise_for_status()
            await self._handle_success()
            return response.json()
            
        except httpx.HTTPError as e:
            await self._handle_failure(e)
            logger.error(f"Research trigger failed: {e}")
            raise
    
    async def trigger_auto_scraping(self,
                                   sources: List[str] = None,
                                   domains: List[str] = None,
                                   limit: int = 10) -> Dict:
        """
        Trigger automatic topic scraping from external sources
        
        Args:
            sources: Specific sources to scrape
            domains: Domains to focus on
            limit: Maximum topics to scrape
            
        Returns:
            Dict with scraping status and discovered topics
        """
        if not await self._check_circuit_breaker():
            raise Exception("Circuit breaker is open - Topic Manager unavailable")
            
        payload = {
            "limit": limit,
            "triggered_by": "research_crew",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if sources:
            payload["sources"] = sources
        if domains:
            payload["domains"] = domains
        
        try:
            response = await self.client.post(
                f"{self.base_url}/topics/scrape",
                json=payload
            )
            response.raise_for_status()
            await self._handle_success()
            return response.json()
            
        except httpx.HTTPError as e:
            await self._handle_failure(e)
            logger.error(f"Auto-scraping trigger failed: {e}")
            raise
    
    async def get_topic_relevance_score(self,
                                       topic_id: str,
                                       context: Dict[str, Any]) -> Dict:
        """
        Get relevance score for a specific topic given context
        
        Args:
            topic_id: ID of the topic to score
            context: Context for relevance scoring
            
        Returns:
            Dict with relevance score and reasoning
        """
        if not await self._check_circuit_breaker():
            raise Exception("Circuit breaker is open - Topic Manager unavailable")
            
        payload = {
            "topic_id": topic_id,
            "context": context,
            "scoring_agent": "research_crew"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/topics/relevance-score",
                json=payload
            )
            response.raise_for_status()
            await self._handle_success()
            return response.json()
            
        except httpx.HTTPError as e:
            await self._handle_failure(e)
            logger.error(f"Relevance scoring failed: {e}")
            raise
    
    async def search_topics(self,
                           query: str,
                           filters: Optional[Dict] = None,
                           limit: int = 20,
                           include_metadata: bool = True) -> Dict:
        """
        Search topics in the database
        
        Args:
            query: Search query
            filters: Additional filters
            limit: Maximum results
            include_metadata: Include topic metadata
            
        Returns:
            Dict with search results
        """
        if not await self._check_circuit_breaker():
            raise Exception("Circuit breaker is open - Topic Manager unavailable")
            
        params = {
            "query": query,
            "limit": limit,
            "include_metadata": include_metadata
        }
        
        if filters:
            params.update(filters)
        
        try:
            response = await self.client.get(
                f"{self.base_url}/topics/search",
                params=params
            )
            response.raise_for_status()
            await self._handle_success()
            return response.json()
            
        except httpx.HTTPError as e:
            await self._handle_failure(e)
            logger.error(f"Topic search failed: {e}")
            raise
    
    async def get_trending_topics(self,
                                 time_window: str = "24h",
                                 limit: int = 10) -> Dict:
        """
        Get currently trending topics
        
        Args:
            time_window: Time window for trending analysis
            limit: Maximum topics to return
            
        Returns:
            Dict with trending topics
        """
        params = {
            "time_window": time_window,
            "limit": limit
        }
        
        try:
            response = await self.client.get(
                f"{self.base_url}/topics/trending",
                params=params
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Trending topics request failed: {e}")
            raise


# Convenience functions
async def create_topic_manager_client(base_url: str = "http://localhost:8041") -> TopicManagerClient:
    """
    Create and return a Topic Manager client
    
    Args:
        base_url: Topic Manager base URL
        
    Returns:
        Configured TopicManagerClient instance
    """
    client = TopicManagerClient(base_url=base_url)
    
    # Verify connection
    try:
        await client.health_check()
        logger.info(f"Successfully connected to Topic Manager at {base_url}")
    except Exception as e:
        logger.warning(f"Topic Manager at {base_url} is not available: {e}")
    
    return client