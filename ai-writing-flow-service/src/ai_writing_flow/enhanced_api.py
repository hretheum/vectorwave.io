#!/usr/bin/env python3
"""
Enhanced API Endpoints for AI Writing Flow
PHASE 4.5.3: AI WRITING FLOW INTEGRATION (Week 2)

Multi-platform content generation endpoints for Publisher Orchestrator integration.
Provides enhanced functionality for platform-specific content optimization.
"""

import os
import uuid
import time
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

# Import models and components
try:
    from ai_writing_flow.models import (
        MultiPlatformRequest, 
        MultiPlatformResponse,
        LinkedInPromptRequest,
        LinkedInPromptResponse, 
        ContentGenerationMetrics
    )
except ImportError:
    # Import directly from models.py file if models package import fails
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from models import (
        MultiPlatformRequest, 
        MultiPlatformResponse,
        LinkedInPromptRequest,
        LinkedInPromptResponse, 
        ContentGenerationMetrics
    )
# Import PlatformOptimizer conditionally
try:
    from ai_writing_flow.platform_optimizer import PlatformOptimizer, Topic, PlatformConfig
    PLATFORM_OPTIMIZER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️ PlatformOptimizer not available: {e}")
    PlatformOptimizer = None
    Topic = None  
    PlatformConfig = None
    PLATFORM_OPTIMIZER_AVAILABLE = False

logger = logging.getLogger(__name__)


class EnhancedAPIService:
    """Enhanced API service for multi-platform content generation"""
    
    def __init__(self):
        """Initialize enhanced API service"""
        
        # Initialize PlatformOptimizer (if available)
        if PLATFORM_OPTIMIZER_AVAILABLE:
            try:
                self.platform_optimizer = PlatformOptimizer()
                logger.info("✅ PlatformOptimizer initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize PlatformOptimizer: {e}")
                self.platform_optimizer = None
        else:
            logger.warning("⚠️ PlatformOptimizer not available - Enhanced API running in limited mode")
            self.platform_optimizer = None
            
        self.generation_metrics = ContentGenerationMetrics()
        self._active_requests: Dict[str, Dict[str, Any]] = {}
        
        logger.info("✅ Enhanced API service initialized")
    
    async def generate_multi_platform_content(
        self, 
        request: MultiPlatformRequest
    ) -> MultiPlatformResponse:
        """
        Generate content for multiple platforms simultaneously
        
        Enhanced endpoint for Publisher Orchestrator integration
        """
        
        start_time = time.time()
        request_id = request.request_id or str(uuid.uuid4())
        
        logger.info(f"🚀 Multi-platform generation request: {request_id}")
        logger.info(f"📋 Platforms: {list(request.platforms.keys())}")
        
        try:
            # Check if PlatformOptimizer is available
            if not self.platform_optimizer:
                raise HTTPException(
                    status_code=503,
                    detail="PlatformOptimizer service not available. AI Writing Flow V2 dependencies required."
                )
            
            # Track active request
            self._active_requests[request_id] = {
                "start_time": start_time,
                "platforms": list(request.platforms.keys()),
                "status": "processing"
            }
            
            # Convert request to internal format
            topic = Topic(
                title=request.topic.get("title", "Untitled"),
                description=request.topic.get("description", ""),
                keywords=request.topic.get("keywords", []),
                target_audience=request.topic.get("target_audience", "general")
            )
            
            # Convert platform configs
            platform_configs = {}
            for platform_name, config_data in request.platforms.items():
                platform_configs[platform_name] = PlatformConfig(
                    enabled=config_data.get("enabled", True),
                    direct_content=config_data.get("direct_content"),
                    custom_params=config_data.get("custom_params", {})
                )
            
            # Generate content for all platforms
            results = await self.platform_optimizer.generate_multi_platform(
                topic, platform_configs
            )
            
            # Process results
            platform_content = {}
            success_count = 0
            error_count = 0
            
            for platform, result in results.items():
                if isinstance(result, dict) and "error" in result:
                    platform_content[platform] = {"error": result["error"]}
                    error_count += 1
                else:
                    platform_content[platform] = {
                        "content": result.content,
                        "content_type": result.content_type,
                        "metadata": result.metadata,
                        "ready_for_presenton": result.ready_for_presenton,
                        "generation_time": result.generation_time,
                        "quality_score": result.quality_score
                    }
                    success_count += 1
            
            generation_time = time.time() - start_time
            
            # Update metrics
            self._update_metrics(platform_configs.keys(), success_count, error_count, generation_time)
            
            # Clean up active requests
            self._active_requests.pop(request_id, None)
            
            # Build response
            response = MultiPlatformResponse(
                request_id=request_id,
                platform_content=platform_content,
                generation_time=generation_time,
                success_count=success_count,
                error_count=error_count,
                metadata={
                    "topic": request.topic,
                    "total_platforms": len(platform_configs),
                    "timestamp": datetime.now().isoformat(),
                    "priority": request.priority
                }
            )
            
            logger.info(f"✅ Multi-platform generation complete: {request_id} ({generation_time:.2f}s)")
            logger.info(f"📊 Success: {success_count}, Errors: {error_count}")
            
            return response
            
        except Exception as e:
            # Clean up active requests
            self._active_requests.pop(request_id, None)
            
            logger.error(f"❌ Multi-platform generation failed: {request_id} - {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Multi-platform content generation failed: {str(e)}"
            )
    
    async def generate_linkedin_prompt(
        self, 
        request: LinkedInPromptRequest
    ) -> LinkedInPromptResponse:
        """
        Generate LinkedIn carousel prompt for Presenton integration
        
        Specialized endpoint for LinkedIn carousel presentations
        """
        
        start_time = time.time()
        
        logger.info(f"🎯 LinkedIn prompt generation: {request.topic.get('title', 'Untitled')}")
        
        try:
            # Check if PlatformOptimizer is available
            if not self.platform_optimizer:
                raise HTTPException(
                    status_code=503,
                    detail="PlatformOptimizer service not available. AI Writing Flow V2 dependencies required."
                )
            
            # Convert request to internal format
            topic = Topic(
                title=request.topic.get("title", "Untitled"),
                description=request.topic.get("description", ""),
                keywords=request.topic.get("keywords", []),
                target_audience=request.topic.get("target_audience", "professionals")
            )
            
            # Generate LinkedIn carousel prompt
            result = await self.platform_optimizer.generate_for_platform(
                topic=topic,
                platform="linkedin", 
                direct_content=False  # Always prompt mode for LinkedIn
            )
            
            generation_time = time.time() - start_time
            
            # Build response
            response = LinkedInPromptResponse(
                prompt=result.content,
                slides_count=request.slides_count,
                template_used=request.template,
                ready_for_presenton=True,
                generation_time=generation_time,
                metadata={
                    "topic": request.topic,
                    "enhanced_mode": request.enhanced_mode,
                    "quality_score": result.quality_score,
                    "timestamp": datetime.now().isoformat(),
                    "content_length": len(result.content),
                    "platform_metadata": result.metadata
                }
            )
            
            logger.info(f"✅ LinkedIn prompt generated: {len(result.content)} chars, quality: {result.quality_score:.2f}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ LinkedIn prompt generation failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"LinkedIn prompt generation failed: {str(e)}"
            )
    
    def _update_metrics(
        self, 
        platforms: List[str], 
        success_count: int, 
        error_count: int, 
        generation_time: float
    ):
        """Update generation metrics"""
        
        self.generation_metrics.total_requests += 1
        self.generation_metrics.successful_generations += success_count
        self.generation_metrics.failed_generations += error_count
        
        # Update average generation time
        total_gen_time = (
            self.generation_metrics.average_generation_time * 
            (self.generation_metrics.total_requests - 1) + 
            generation_time
        )
        self.generation_metrics.average_generation_time = total_gen_time / self.generation_metrics.total_requests
        
        # Update platform usage
        for platform in platforms:
            if platform not in self.generation_metrics.platform_usage:
                self.generation_metrics.platform_usage[platform] = 0
            self.generation_metrics.platform_usage[platform] += 1
    
    def get_metrics(self) -> ContentGenerationMetrics:
        """Get current generation metrics"""
        return self.generation_metrics
    
    def get_active_requests(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active requests"""
        return self._active_requests.copy()
    
    def get_supported_platforms(self) -> List[str]:
        """Get list of supported platforms"""
        if self.platform_optimizer:
            return self.platform_optimizer.get_supported_platforms()
        else:
            return []  # Return empty list when PlatformOptimizer not available
    
    def get_platform_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get platform configurations"""
        if self.platform_optimizer:
            return self.platform_optimizer.get_platform_configs()
        else:
            return {}  # Return empty dict when PlatformOptimizer not available


# Global service instance
enhanced_api_service = EnhancedAPIService()


# FastAPI app for enhanced endpoints
app = FastAPI(
    title="AI Writing Flow - Enhanced API",
    description="Multi-platform content generation for Publisher Orchestrator integration",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.post("/generate/multi-platform", response_model=MultiPlatformResponse)
async def generate_multi_platform_content(request: MultiPlatformRequest):
    """
    Generate content for multiple platforms simultaneously
    
    Enhanced endpoint for Publisher Orchestrator integration.
    Supports concurrent platform processing with error handling.
    """
    return await enhanced_api_service.generate_multi_platform_content(request)


@app.post("/generate/linkedin-prompt", response_model=LinkedInPromptResponse)  
async def generate_linkedin_prompt(request: LinkedInPromptRequest):
    """
    Generate LinkedIn carousel prompt for Presenton integration
    
    Specialized endpoint for creating presentation prompts
    that are ready for AI-powered presentation generation.
    """
    return await enhanced_api_service.generate_linkedin_prompt(request)


@app.get("/metrics", response_model=ContentGenerationMetrics)
async def get_generation_metrics():
    """Get current content generation metrics"""
    return enhanced_api_service.get_metrics()


@app.get("/platforms")
async def get_supported_platforms():
    """Get list of supported platforms and their configurations"""
    return {
        "supported_platforms": enhanced_api_service.get_supported_platforms(),
        "platform_configs": enhanced_api_service.get_platform_configs()
    }


@app.get("/active-requests")
async def get_active_requests():
    """Get currently active generation requests"""
    return {
        "active_requests": enhanced_api_service.get_active_requests(),
        "count": len(enhanced_api_service.get_active_requests())
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        platform_optimizer = enhanced_api_service.platform_optimizer
        ai_flow_available = platform_optimizer.ai_writing_flow is not None
        
        return {
            "status": "healthy",
            "service": "ai_writing_flow_enhanced",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "platform_optimizer": True,
                "ai_writing_flow": ai_flow_available,
                "supported_platforms": len(enhanced_api_service.get_supported_platforms())
            },
            "metrics": {
                "total_requests": enhanced_api_service.generation_metrics.total_requests,
                "active_requests": len(enhanced_api_service.get_active_requests())
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "AI Writing Flow - Enhanced API",
        "description": "Multi-platform content generation for Publisher Orchestrator integration",
        "version": "2.0.0",
        "endpoints": {
            "multi_platform": "/generate/multi-platform",
            "linkedin_prompt": "/generate/linkedin-prompt", 
            "metrics": "/metrics",
            "platforms": "/platforms",
            "health": "/health",
            "docs": "/docs"
        },
        "features": {
            "concurrent_generation": True,
            "platform_optimization": True,
            "presenton_integration": True,
            "quality_scoring": True,
            "error_handling": True
        }
    }


# Error handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "message": "Request validation failed"
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "status_code": exc.status_code,
            "detail": exc.detail
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("🚀 Starting AI Writing Flow Enhanced API...")
    logger.info(f"✅ Service ready with {len(enhanced_api_service.get_supported_platforms())} platforms")


# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 AI Writing Flow Enhanced API shutting down...")


if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))  # Different port than main service
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"🚀 Starting Enhanced API on {host}:{port}")
    
    uvicorn.run(
        "enhanced_api:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )