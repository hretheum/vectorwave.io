#!/usr/bin/env python3
"""
LinkedIn PPT Generator Service - Wrapper for Presenton
Task 3.2.1: LinkedIn PPT Generator Service

FastAPI service that provides LinkedIn-optimized presentation generation
by proxying requests to the Presenton service with LinkedIn-specific optimizations.
"""

import os
import logging
import time
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Response
import uvicorn

from models import LinkedInPPTRequest, LinkedInPPTResponse, HealthResponse
from presenton_client import PresentonClient, CircuitBreakerError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LinkedIn PPT Generator Service",
    description="LinkedIn-optimized presentation generator (Presenton wrapper)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global client instance
presenton_client = None

def get_presenton_client() -> PresentonClient:
    """Get or create global Presenton client instance"""
    global presenton_client
    if presenton_client is None:
        presenton_client = PresentonClient()
    return presenton_client

@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("🚀 Starting LinkedIn PPT Generator Service...")
    
    # Test Presenton connectivity
    client = get_presenton_client()
    try:
        await client.health_check()
        logger.info("✅ LinkedIn PPT Generator Service initialized - Presenton connected")
    except Exception as e:
        logger.warning(f"⚠️ Presenton not immediately available: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 LinkedIn PPT Generator Service shutting down...")

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with service information"""
    client = get_presenton_client()
    circuit_status = client.get_circuit_breaker_status()
    
    return {
        "service": "LinkedIn PPT Generator Service",
        "description": "LinkedIn-optimized presentation generator",
        "version": "1.0.0",
        "status": "operational" if not circuit_status["circuit_open"] else "degraded",
        "endpoints": {
            "health": "/health",
            "generate": "/generate-linkedin-ppt",
            "docs": "/docs"
        },
        "features": {
            "linkedin_optimization": True,
            "presenton_integration": True,
            "circuit_breaker": True,
            "automatic_retry": True
        },
        "presenton_url": client.base_url,
        "circuit_breaker_status": circuit_status
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    client = get_presenton_client()
    
    try:
        # Check Presenton availability
        presenton_health = await client.health_check()
        presenton_available = presenton_health.get("status") == "healthy"
        
        return HealthResponse(
            status="healthy" if presenton_available else "degraded",
            service="linkedin-ppt-generator",
            version="1.0.0",
            presenton_available=presenton_available,
            presenton_url=client.base_url
        )
        
    except CircuitBreakerError:
        return HealthResponse(
            status="degraded",
            service="linkedin-ppt-generator", 
            version="1.0.0",
            presenton_available=False,
            presenton_url=client.base_url,
            error="Circuit breaker is open"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="linkedin-ppt-generator",
            version="1.0.0",
            presenton_available=False,
            presenton_url=client.base_url,
            error=str(e)
        )

@app.post("/generate-linkedin-ppt", response_model=LinkedInPPTResponse)
async def generate_linkedin_presentation(request: LinkedInPPTRequest):
    """
    Generate LinkedIn-optimized presentation
    
    Takes LinkedIn-specific parameters and generates a presentation
    optimized for LinkedIn sharing via the Presenton service.
    """
    
    start_time = time.time()
    logger.info(f"🎯 LinkedIn PPT generation request: {request.topic_title}")
    logger.info(f"📊 Config: {request.slides_count} slides, template={request.template}")
    
    try:
        client = get_presenton_client()
        
        # Enhance prompt for LinkedIn optimization
        linkedin_prompt = _enhance_prompt_for_linkedin(
            request.topic_description,
            request.topic_title,
            request.target_audience,
            request.keywords,
            request.include_call_to_action
        )
        
        logger.info("🔄 Forwarding request to Presenton service...")
        
        # Forward to Presenton with enhanced prompt
        presenton_response = await client.generate_presentation(
            prompt=linkedin_prompt,
            slides_count=request.slides_count,
            template=request.template,
            topic_title=request.topic_title
        )
        
        generation_time = time.time() - start_time
        
        # Build LinkedIn-optimized response
        response = LinkedInPPTResponse(
            presentation_id=presenton_response["presentation_id"],
            pptx_url=f"http://presenton:8089{presenton_response['pptx_url']}",  # Proxy URL
            pdf_url=f"http://presenton:8089{presenton_response['pdf_url']}",    # Proxy URL
            pdf_path=presenton_response["pdf_path"],
            slide_count=presenton_response["slide_count"],
            generation_time=generation_time,
            template_used=presenton_response["template_used"],
            topic_title=presenton_response["topic_title"],
            linkedin_optimized=True,
            ready_for_linkedin=True
        )
        
        logger.info(f"✅ LinkedIn presentation generated: {response.presentation_id} ({generation_time:.2f}s)")
        return response
        
    except CircuitBreakerError as e:
        logger.error(f"❌ Circuit breaker open: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service temporarily unavailable",
                "message": "Presenton service circuit breaker is open",
                "retry_after": 60
            }
        )
        
    except Exception as e:
        logger.error(f"❌ LinkedIn presentation generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Presentation generation failed",
                "message": str(e),
                "service": "linkedin-ppt-generator"
            }
        )

def _enhance_prompt_for_linkedin(
    description: str,
    title: str,
    target_audience: str = None,
    keywords: list = None,
    include_cta: bool = True
) -> str:
    """Enhance prompt with LinkedIn-specific optimizations"""
    
    prompt_parts = [
        f"Create a professional LinkedIn-ready presentation about: {title}",
        f"\nDescription: {description}",
        "\nLinkedIn Optimization Requirements:",
        "- Professional business tone suitable for LinkedIn audience",
        "- Clear value proposition on first slide",
        "- Data-driven insights and actionable takeaways",
        "- Visual hierarchy optimized for social media sharing",
        "- Concise bullet points (max 5 per slide)",
        "- Strong conclusion with clear next steps"
    ]
    
    if target_audience:
        prompt_parts.append(f"- Target audience: {target_audience}")
    
    if keywords:
        prompt_parts.append(f"- Include these keywords naturally: {', '.join(keywords)}")
    
    if include_cta:
        prompt_parts.append("- Include a call-to-action slide encouraging LinkedIn engagement")
        prompt_parts.append("- Suggest discussion prompts for LinkedIn comments")
    
    prompt_parts.extend([
        "\nSlide Structure:",
        "1. Title slide with compelling headline",
        "2. Problem/opportunity overview", 
        "3. Key insights or solution points",
        "4. Supporting data or examples",
        "5. Conclusion with call-to-action"
    ])
    
    return "\n".join(prompt_parts)

if __name__ == "__main__":
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8002"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"🚀 Starting LinkedIn PPT Generator Service on {host}:{port}")
    logger.info(f"🔧 Debug mode: {debug}")
    logger.info(f"🎯 Presenton URL: {os.getenv('PRESENTON_SERVICE_URL', 'http://presenton:8089')}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )