"""
Gamma.app API Client
Handles communication with Gamma.app Generate API
"""

import logging
import aiohttp
import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime
import json

from models import GammaAPIResponse, GammaConnectionTest, ServiceStatus

logger = logging.getLogger(__name__)


class GammaAPIClient:
    """
    Gamma.app API client with rate limiting and error handling
    
    API Documentation: https://developers.gamma.app/docs/how-does-the-generations-api-work
    """
    
    def __init__(self, api_key: Optional[str] = None, demo_mode: bool = False):
        self.api_key = api_key
        self.demo_mode = demo_mode
        self.base_url = "https://api.gamma.app/v1"
        
        # Rate limiting (50 generations per month in Beta)
        self.monthly_limit = 50
        self.current_usage = 0
        self.rate_limit_reset = None
        
        # Request tracking
        self.request_count = 0
        self.total_cost = 0.0
        
        # Session for connection pooling
        self.session = None
        
        logger.info(f"🎨 Gamma API Client initialized (demo_mode: {demo_mode})")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Vector-Wave-Gamma-Client/1.0"
            }
            
            if self.api_key and not self.demo_mode:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120)  # 2 minute timeout
            )
        
        return self.session
    
    async def test_connection(self) -> GammaConnectionTest:
        """Test connection to Gamma.app API"""
        start_time = time.time()
        
        if self.demo_mode:
            # Demo mode - simulate successful connection
            await asyncio.sleep(0.5)  # Simulate network delay
            
            return GammaConnectionTest(
                connected=True,
                response_time_ms=(time.time() - start_time) * 1000,
                api_version="v1.0-demo",
                limits={
                    "total": self.monthly_limit,
                    "used": self.current_usage,
                    "remaining": self.monthly_limit - self.current_usage
                }
            )
        
        try:
            session = await self._get_session()
            
            # Test endpoint (using API status/limits endpoint if available)
            async with session.get(f"{self.base_url}/limits") as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    
                    return GammaConnectionTest(
                        connected=True,
                        response_time_ms=response_time,
                        api_version=data.get("version", "v1.0"),
                        limits=data.get("limits", {})
                    )
                else:
                    error_text = await response.text()
                    return GammaConnectionTest(
                        connected=False,
                        response_time_ms=response_time,
                        api_version="unknown",
                        limits={},
                        error=f"HTTP {response.status}: {error_text}"
                    )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Gamma API connection test failed: {e}")
            
            return GammaConnectionTest(
                connected=False,
                response_time_ms=response_time,
                api_version="unknown",
                limits={},
                error=str(e)
            )
    
    async def get_status(self) -> ServiceStatus:
        """Get current API status and usage"""
        
        if self.demo_mode:
            return ServiceStatus(
                status="demo_mode",
                remaining_calls=self.monthly_limit - self.current_usage,
                monthly_usage=self.current_usage,
                rate_limit_reset=datetime(2025, 2, 1)
            )
        
        try:
            session = await self._get_session()
            
            async with session.get(f"{self.base_url}/status") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return ServiceStatus(
                        status=data.get("status", "unknown"),
                        remaining_calls=data.get("remaining_calls", 0),
                        monthly_usage=data.get("monthly_usage", 0),
                        rate_limit_reset=datetime.fromisoformat(data.get("rate_limit_reset", "2025-02-01T00:00:00Z"))
                    )
                else:
                    # Fallback status
                    return ServiceStatus(
                        status="api_error",
                        remaining_calls=0,
                        monthly_usage=self.current_usage
                    )
        
        except Exception as e:
            logger.error(f"Failed to get Gamma API status: {e}")
            return ServiceStatus(
                status="connection_error",
                remaining_calls=0,
                monthly_usage=self.current_usage
            )
    
    async def generate_presentation(self, request_data: Dict[str, Any]) -> GammaAPIResponse:
        """Generate presentation using Gamma.app API"""
        
        start_time = time.time()
        
        # Check rate limits
        if self.current_usage >= self.monthly_limit:
            return GammaAPIResponse(
                success=False,
                error_code="RATE_LIMIT_EXCEEDED",
                error_message=f"Monthly limit of {self.monthly_limit} generations exceeded"
            )
        
        if self.demo_mode:
            # Demo mode - simulate presentation generation
            await asyncio.sleep(2.0)  # Simulate processing time
            
            processing_time = (time.time() - start_time) * 1000
            
            # Simulate successful generation
            self.current_usage += 1
            self.request_count += 1
            
            demo_cost = 0.50  # Demo cost per generation
            self.total_cost += demo_cost
            
            presentation_id = f"gamma_demo_{int(time.time())}"
            
            return GammaAPIResponse(
                success=True,
                presentation_id=presentation_id,
                preview_url=f"https://gamma.app/docs/{presentation_id}",
                download_urls={
                    "pdf": f"https://gamma.app/download/{presentation_id}.pdf",
                    "pptx": f"https://gamma.app/download/{presentation_id}.pptx"
                },
                slides_count=request_data.get("slides_count", 8),
                processing_time_ms=processing_time,
                cost=demo_cost
            )
        
        try:
            session = await self._get_session()
            
            # Prepare request data for Gamma API
            gamma_request = self._prepare_gamma_request(request_data)
            
            logger.info(f"🎨 Sending generation request to Gamma.app: {request_data['topic']['title']}")
            
            async with session.post(
                f"{self.base_url}/generations",
                json=gamma_request
            ) as response:
                
                processing_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Update usage tracking
                    self.current_usage += 1
                    self.request_count += 1
                    
                    # Calculate cost (estimated)
                    estimated_cost = 0.50  # Placeholder cost per generation
                    self.total_cost += estimated_cost
                    
                    return GammaAPIResponse(
                        success=True,
                        presentation_id=data.get("id"),
                        preview_url=data.get("preview_url"),
                        download_urls=data.get("download_urls", {}),
                        slides_count=data.get("slides_count"),
                        processing_time_ms=processing_time,
                        cost=estimated_cost
                    )
                
                else:
                    error_data = await response.json() if response.headers.get("content-type") == "application/json" else {}
                    
                    return GammaAPIResponse(
                        success=False,
                        processing_time_ms=processing_time,
                        error_code=error_data.get("error", "API_ERROR"),
                        error_message=error_data.get("message", f"HTTP {response.status}")
                    )
        
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Gamma API generation failed: {e}")
            
            return GammaAPIResponse(
                success=False,
                processing_time_ms=processing_time,
                error_code="REQUEST_FAILED",
                error_message=str(e)
            )
    
    def _prepare_gamma_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare request data for Gamma.app API format"""
        
        topic = request_data.get("topic", {})
        
        # Build prompt from topic information
        prompt_parts = [topic.get("title", "")]
        
        if topic.get("description"):
            prompt_parts.append(f"Description: {topic['description']}")
        
        if topic.get("keywords"):
            keywords_str = ", ".join(topic["keywords"])
            prompt_parts.append(f"Keywords: {keywords_str}")
        
        if topic.get("target_audience"):
            prompt_parts.append(f"Target audience: {topic['target_audience']}")
        
        prompt = ". ".join(prompt_parts)
        
        # Add custom instructions if provided
        custom_instructions = request_data.get("custom_instructions")
        if custom_instructions:
            prompt += f". Additional instructions: {custom_instructions}"
        
        return {
            "text": prompt,
            "type": "presentation",
            "theme": request_data.get("theme", "business"),
            "language": request_data.get("language", "en"),
            "slides_count": request_data.get("slides_count", 8)
        }
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("🔌 Gamma API client session closed")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_requests": self.request_count,
            "current_monthly_usage": self.current_usage,
            "monthly_limit": self.monthly_limit,
            "remaining_calls": self.monthly_limit - self.current_usage,
            "total_cost": self.total_cost,
            "average_cost_per_request": self.total_cost / max(1, self.request_count)
        }