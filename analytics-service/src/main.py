#!/usr/bin/env python3
"""
Analytics Service - Production Implementation
Multi-platform analytics with realistic API capabilities

Architecture: Clean Architecture + DDD
Port: 8081
Integration: ChromaDB + Circuit Breakers
"""

import os
import logging
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import uuid
import asyncio

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from pydantic import BaseModel

# Internal imports
from models import (
    PlatformConfig, ConfigurationResponse, ManualMetricsEntry, 
    ManualEntryResponse, AnalyticsInsights, HealthResponse,
    CSVImportRequest, CSVImportResponse, ExportResponse
)
from chromadb_manager import ChromaDBManager
from platform_collectors import PlatformCollectorManager
from analytics_engine import AnalyticsInsightsGenerator
from circuit_breaker import AnalyticsCircuitBreaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Initialize FastAPI app
app = FastAPI(
    title="Analytics Service",
    description="Production-ready multi-platform analytics for Vector Wave",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Platform Management", "description": "Platform configuration and setup"},
        {"name": "Data Collection", "description": "Manual entry and CSV import"},
        {"name": "Analytics", "description": "Insights generation and reporting"},
        {"name": "System", "description": "Health checks and monitoring"}
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
service_state = {
    "start_time": time.time(),
    "chromadb_manager": None,
    "collector_manager": None,
    "insights_generator": None,
    "circuit_breaker": None,
    "health_status": "starting"
}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user from JWT token (placeholder implementation)"""
    # TODO: Implement proper JWT validation
    return "user_dev"  # Development placeholder

@app.on_event("startup")
async def startup_event():
    """Initialize Analytics Service on startup"""
    logger.info("🚀 Starting Analytics Service...")
    
    try:
        # Initialize ChromaDB connection
        chromadb_url = os.getenv("CHROMADB_URL", "http://localhost:8000")
        service_state["chromadb_manager"] = ChromaDBManager(chromadb_url)
        await service_state["chromadb_manager"].initialize()
        
        # Initialize platform collectors
        service_state["collector_manager"] = PlatformCollectorManager(
            service_state["chromadb_manager"]
        )
        
        # Initialize analytics engine
        service_state["insights_generator"] = AnalyticsInsightsGenerator(
            service_state["chromadb_manager"]
        )
        
        # Initialize circuit breaker
        service_state["circuit_breaker"] = AnalyticsCircuitBreaker()
        
        service_state["health_status"] = "healthy"
        logger.info("✅ Analytics Service initialized successfully")
        logger.info("📊 Multi-platform analytics ready")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        service_state["health_status"] = "unhealthy"
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Analytics Service shutting down...")
    
    if service_state["chromadb_manager"]:
        await service_state["chromadb_manager"].close()

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with service information"""
    uptime = time.time() - service_state["start_time"]
    
    return {
        "service": "Analytics Service",
        "description": "Production-ready multi-platform analytics for Vector Wave",
        "version": "2.0.0",
        "status": service_state["health_status"],
        "port": 8081,
        "architecture": "Clean Architecture + DDD",
        "capabilities": {
            "platform_configuration": "Configure Ghost, Twitter, LinkedIn, Beehiiv data collection",
            "manual_data_entry": "LinkedIn metrics with quality scoring",
            "csv_import": "Beehiiv newsletter analytics processing",
            "insights_generation": "AI-powered cross-platform analytics",
            "data_export": "JSON, CSV, XLSX export formats"
        },
        "supported_platforms": {
            "ghost": {"method": "api", "status": "full_access"},
            "twitter": {"method": "proxy", "status": "typefully_integration"},
            "linkedin": {"method": "manual", "status": "no_api_available"},
            "beehiiv": {"method": "csv", "status": "export_only"}
        },
        "uptime_seconds": uptime,
        "chromadb_status": "connected" if service_state["chromadb_manager"] else "disconnected"
    }

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Comprehensive health check"""
    try:
        health_data = {
            "status": service_state["health_status"],
            "service": "analytics-service", 
            "version": "2.0.0",
            "port": 8081,
            "timestamp": datetime.now(),
            "uptime_seconds": time.time() - service_state["start_time"]
        }
        
        # Check ChromaDB connectivity
        if service_state["chromadb_manager"]:
            chromadb_health = await service_state["chromadb_manager"].health_check()
            health_data["chromadb_status"] = chromadb_health.status
            health_data["collections_available"] = chromadb_health.collections_count
        else:
            health_data["chromadb_status"] = "disconnected"
            health_data["collections_available"] = 0
        
        # Check circuit breaker states
        if service_state["circuit_breaker"]:
            health_data["circuit_breaker_state"] = service_state["circuit_breaker"].get_state()
        
        # Platform collectors status
        if service_state["collector_manager"]:
            health_data["platform_collectors"] = await service_state["collector_manager"].get_status()
        
        return HealthResponse(**health_data)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "health_check_failed",
                "message": "Service health check encountered an error",
                "details": str(e)
            }
        )

# Platform Configuration Endpoints
@app.post("/analytics/platforms/{platform}/configure", 
          response_model=ConfigurationResponse, 
          tags=["Platform Management"])
async def configure_platform_analytics(
    platform: str,
    config: PlatformConfig,
    current_user: str = Depends(get_current_user)
):
    """Configure platform-specific data collection"""
    
    logger.info(f"🔧 Configuring analytics for platform: {platform}")
    
    try:
        # Validate platform support
        supported_platforms = {
            "ghost": {
                "methods": ["api"],
                "metrics": ["views", "likes", "comments", "subscribers", "email_opens"],
                "limitations": []
            },
            "twitter": {
                "methods": ["proxy"],
                "metrics": ["views", "likes", "retweets", "replies", "bookmarks"],
                "limitations": ["Requires Typefully Pro subscription", "Limited to scheduled posts only"]
            },
            "linkedin": {
                "methods": ["manual"],
                "metrics": ["views", "reactions", "comments", "shares"],
                "limitations": ["No API access", "Manual data entry required", "Limited to public metrics"]
            },
            "beehiiv": {
                "methods": ["csv"],
                "metrics": ["subscribers", "opens", "clicks", "unsubscribes"],
                "limitations": ["CSV export only", "Weekly data updates maximum"]
            }
        }
        
        if platform not in supported_platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported platform: {platform}"
            )
        
        platform_capabilities = supported_platforms[platform]
        
        if config.collection_method not in platform_capabilities["methods"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Method '{config.collection_method}' not available for {platform}"
            )
        
        # Configure collector
        collector_result = await service_state["collector_manager"].configure_platform_collector(
            platform=platform,
            method=config.collection_method,
            config=config.dict(),
            user_id=current_user
        )
        
        # Determine next collection time
        next_collection = None
        if config.collection_frequency == "hourly":
            next_collection = datetime.now() + timedelta(hours=1)
        elif config.collection_frequency == "daily":
            next_collection = datetime.now() + timedelta(days=1)
        elif config.collection_frequency == "weekly":
            next_collection = datetime.now() + timedelta(weeks=1)
        
        response = ConfigurationResponse(
            platform=platform,
            status="configured",
            collection_method=config.collection_method,
            available_metrics=platform_capabilities["metrics"],
            limitations=platform_capabilities["limitations"],
            next_collection=next_collection
        )
        
        # Store configuration in ChromaDB
        await service_state["chromadb_manager"].store_platform_configuration(
            platform, config.dict(), response.dict(), current_user
        )
        
        logger.info(f"✅ Platform {platform} configured successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Platform configuration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "configuration_failed",
                "message": f"Platform analytics configuration failed for {platform}",
                "details": str(e)
            }
        )

# Manual Data Entry Endpoints  
@app.post("/analytics/data/manual-entry",
          response_model=ManualEntryResponse,
          tags=["Data Collection"])
async def submit_manual_metrics(
    entry: ManualMetricsEntry,
    current_user: str = Depends(get_current_user)
):
    """Submit manual metrics data for platforms like LinkedIn"""
    
    entry_id = f"manual_{uuid.uuid4().hex[:12]}"
    logger.info(f"📝 Processing manual entry: {entry_id} for {entry.platform}")
    
    try:
        # Process manual entry through collector manager
        processing_result = await service_state["collector_manager"].process_manual_entry(
            entry=entry,
            entry_id=entry_id,
            user_id=current_user
        )
        
        response = ManualEntryResponse(
            entry_id=entry_id,
            publication_id=entry.publication_id,
            platform=entry.platform,
            metrics_accepted=processing_result.accepted_metrics,
            data_quality_score=processing_result.quality_score,
            stored_at=datetime.now()
        )
        
        logger.info(f"✅ Manual entry {entry_id} processed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Manual entry processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "manual_entry_failed",
                "message": "Manual metrics submission failed",
                "entry_id": entry_id,
                "details": str(e)
            }
        )

# Analytics Insights Endpoints
@app.get("/analytics/insights/{user_id}",
         response_model=AnalyticsInsights,
         tags=["Analytics"])
async def get_analytics_insights(
    user_id: str,
    time_period: str = "30d",
    platforms: Optional[List[str]] = None,
    content_types: Optional[List[str]] = None,
    current_user: str = Depends(get_current_user)
):
    """Generate comprehensive analytics insights"""
    
    logger.info(f"🧠 Generating insights for user {user_id}, period: {time_period}")
    
    try:
        # Generate insights through analytics engine
        insights = await service_state["insights_generator"].generate_comprehensive_insights(
            user_id=user_id,
            time_period=time_period,
            platforms=platforms,
            content_types=content_types
        )
        
        logger.info(f"✅ Insights generated successfully for user {user_id}")
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics insights generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "insights_generation_failed", 
                "message": "Analytics insights generation failed",
                "user_id": user_id,
                "details": str(e)
            }
        )

if __name__ == "__main__":
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("SERVICE_PORT", "8081"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"🚀 Starting Analytics Service on {host}:{port}")
    logger.info(f"🔧 Debug mode: {debug}")
    logger.info("📊 Production multi-platform analytics ready")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )