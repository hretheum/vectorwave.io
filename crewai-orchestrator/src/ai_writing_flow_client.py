"""
AI Writing Flow HTTP Client
Handles communication with AI Writing Flow service for content generation
"""

import os
import logging
import time
from typing import Dict, Any, Optional
from enum import Enum

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class AIWritingFlowStatus(Enum):
    """AI Writing Flow service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class AIWritingFlowClient:
    """HTTP client for AI Writing Flow service"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("AI_WRITING_FLOW_URL", "http://ai-writing-flow:8003")
        self.timeout = httpx.Timeout(30.0, connect=5.0)
        self.health_status = AIWritingFlowStatus.UNKNOWN
        self.last_health_check = 0
        self.health_check_interval = 30  # seconds
        
    async def check_health(self) -> AIWritingFlowStatus:
        """Check AI Writing Flow service health"""
        current_time = time.time()
        
        # Use cached health status if recent
        if current_time - self.last_health_check < self.health_check_interval:
            return self.health_status
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "unknown")
                    
                    if status == "healthy":
                        self.health_status = AIWritingFlowStatus.HEALTHY
                    elif status == "degraded":
                        self.health_status = AIWritingFlowStatus.DEGRADED
                    else:
                        self.health_status = AIWritingFlowStatus.UNHEALTHY
                else:
                    self.health_status = AIWritingFlowStatus.UNHEALTHY
                    
        except Exception as e:
            logger.warning(f"AI Writing Flow health check failed: {e}")
            self.health_status = AIWritingFlowStatus.UNHEALTHY
            
        self.last_health_check = current_time
        return self.health_status
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.RequestError)
    )
    async def generate_content(
        self, 
        topic_title: str,
        topic_description: str,
        platform: str = "general",
        viral_score: float = 7.5
    ) -> Dict[str, Any]:
        """Generate content using AI Writing Flow pipeline"""
        
        # Health gate - check service health first
        health = await self.check_health()
        if health == AIWritingFlowStatus.UNHEALTHY:
            raise Exception("AI Writing Flow service is unhealthy")
            
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    json={
                        "topic_title": topic_title,
                        "topic_description": topic_description,
                        "platform": platform,
                        "viral_score": viral_score
                    }
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"AI Writing Flow generate failed with status {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"AI Writing Flow generate failed: {e}")
            raise
            
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.RequestError)
    )
    async def process_content(
        self,
        content: str,
        platform: str = "general",
        topic: Optional[Dict[str, Any]] = None,
        validation_mode: str = "selective"
    ) -> Dict[str, Any]:
        """Process existing content through AI Writing Flow pipeline"""
        
        # Health gate
        health = await self.check_health()
        if health == AIWritingFlowStatus.UNHEALTHY:
            raise Exception("AI Writing Flow service is unhealthy")
            
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/process",
                    json={
                        "content": content,
                        "platform": platform,
                        "topic": topic,
                        "validation_mode": validation_mode
                    }
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"AI Writing Flow process failed with status {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"AI Writing Flow process failed: {e}")
            raise