"""
Data models for Gamma PPT Generator Service
Pydantic models for Gamma.app integration
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class PresentationTheme(str, Enum):
    """Available presentation themes"""
    MINIMAL = "minimal"
    BUSINESS = "business"
    CREATIVE = "creative"
    ACADEMIC = "academic"
    MODERN = "modern"
    ELEGANT = "elegant"


class OutputFormat(str, Enum):
    """Available output formats"""
    PDF = "pdf"
    PPTX = "pptx"


class GenerationStatus(str, Enum):
    """Generation status options"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Request Models
class TopicInfo(BaseModel):
    """Topic information for presentation generation"""
    title: str = Field(..., description="Presentation title")
    description: Optional[str] = Field(None, description="Topic description")
    keywords: Optional[List[str]] = Field(default=[], description="Related keywords")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    
    class Config:
        schema_extra = {
            "example": {
                "title": "AI Writing Flow Integration",
                "description": "Advanced multi-platform content generation system",
                "keywords": ["AI", "automation", "content"],
                "target_audience": "developers"
            }
        }


class GammaGenerationRequest(BaseModel):
    """Request for Gamma.app presentation generation"""
    topic: TopicInfo
    slides_count: Optional[int] = Field(default=8, ge=3, le=20, description="Number of slides")
    theme: Optional[PresentationTheme] = Field(default=PresentationTheme.BUSINESS, description="Presentation theme")
    language: Optional[str] = Field(default="en", description="Language code (e.g., 'en', 'pl')")
    output_formats: Optional[List[OutputFormat]] = Field(default=[OutputFormat.PDF], description="Output formats")
    custom_instructions: Optional[str] = Field(None, description="Custom generation instructions")
    
    class Config:
        schema_extra = {
            "example": {
                "topic": {
                    "title": "AI Writing Flow Integration",
                    "description": "Advanced multi-platform content generation system",
                    "keywords": ["AI", "automation", "content"],
                    "target_audience": "developers"
                },
                "slides_count": 8,
                "theme": "business",
                "language": "en",
                "output_formats": ["pdf", "pptx"]
            }
        }


# Response Models
class GammaGenerationResponse(BaseModel):
    """Response from Gamma.app presentation generation"""
    generation_id: str
    status: GenerationStatus
    gamma_presentation_id: Optional[str] = None
    preview_url: Optional[str] = None
    download_urls: Optional[Dict[str, str]] = None  # format -> url mapping
    slides_count: Optional[int] = None
    generation_time_ms: Optional[float] = None
    cost: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "generation_id": "gamma_a1b2c3d4e5f6",
                "status": "completed",
                "gamma_presentation_id": "gamma_pres_abc123",
                "preview_url": "https://gamma.app/docs/presentation_abc123",
                "download_urls": {
                    "pdf": "https://gamma.app/download/abc123.pdf",
                    "pptx": "https://gamma.app/download/abc123.pptx"
                },
                "slides_count": 8,
                "generation_time_ms": 15000.0,
                "cost": 0.25,
                "created_at": "2025-01-30T11:00:00Z"
            }
        }


# Health and Monitoring Models
class HealthResponse(BaseModel):
    """Service health check response"""
    status: str
    service: str
    version: str
    port: int
    timestamp: datetime
    uptime_seconds: float
    gamma_api_status: Optional[str] = None
    api_calls_remaining: Optional[int] = None
    monthly_usage: Optional[int] = None
    circuit_breaker_state: Optional[str] = None
    gamma_api_error: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "service": "gamma-ppt-generator",
                "version": "1.0.0",
                "port": 8003,
                "timestamp": "2025-01-30T11:00:00Z",
                "uptime_seconds": 3600.0,
                "gamma_api_status": "connected",
                "api_calls_remaining": 45,
                "monthly_usage": 5,
                "circuit_breaker_state": "CLOSED"
            }
        }


class GammaTestResponse(BaseModel):
    """Response for Gamma API connectivity test"""
    status: str
    connection_test: bool
    response_time_ms: float
    api_version: str
    monthly_limits: Dict[str, Any]
    error_message: Optional[str] = None
    tested_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "connection_test": True,
                "response_time_ms": 850.2,
                "api_version": "v1.0",
                "monthly_limits": {
                    "total": 50,
                    "used": 5,
                    "remaining": 45
                },
                "tested_at": "2025-01-30T11:00:00Z"
            }
        }


class ServiceStatus(BaseModel):
    """Service status information"""
    status: str
    remaining_calls: int
    monthly_usage: int
    rate_limit_reset: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "operational",
                "remaining_calls": 45,
                "monthly_usage": 5,
                "rate_limit_reset": "2025-02-01T00:00:00Z"
            }
        }


# Gamma API Client Models
class GammaAPIResponse(BaseModel):
    """Response from Gamma.app API"""
    success: bool
    presentation_id: Optional[str] = None
    preview_url: Optional[str] = None
    download_urls: Optional[Dict[str, str]] = None
    slides_count: Optional[int] = None
    processing_time_ms: Optional[float] = None
    cost: Optional[float] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class GammaConnectionTest(BaseModel):
    """Gamma API connection test result"""
    connected: bool
    response_time_ms: float
    api_version: str
    limits: Dict[str, Any]
    error: Optional[str] = None