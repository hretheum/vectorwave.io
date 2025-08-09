#!/usr/bin/env python3
"""
Analytics Blackbox Service - Data Models
Task 3.3.1: Analytics API Placeholders
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PublicationMetrics(BaseModel):
    """Publication performance metrics"""
    publication_id: str = Field(..., description="Unique publication identifier")
    platform: str = Field(..., description="Publishing platform (linkedin, twitter, etc.)")
    metrics: Dict[str, Any] = Field(..., description="Platform-specific metrics")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Metric collection timestamp")
    user_id: Optional[str] = Field(None, description="User identifier")
    content_type: Optional[str] = Field(None, description="Content type (article, post, presentation)")


class TrackingResponse(BaseModel):
    """Response for publication tracking"""
    status: str = Field(..., description="Tracking status")
    publication_id: str = Field(..., description="Publication identifier")
    platform: str = Field(..., description="Platform name")
    note: str = Field(..., description="Status note")
    tracked_metrics: List[str] = Field(..., description="List of tracked metric types")
    future_features: List[str] = Field(..., description="Future analytics capabilities")


class UserInsights(BaseModel):
    """User analytics insights response"""
    user_id: str = Field(..., description="User identifier")
    insights: Dict[str, Any] = Field(..., description="Analytics insights data")
    placeholder_recommendations: List[str] = Field(..., description="Placeholder recommendations")
    future_features: List[str] = Field(..., description="Future insights capabilities")


class PlatformAnalytics(BaseModel):
    """Platform-specific analytics response"""
    platform: str = Field(..., description="Platform name")
    total_publications: int = Field(default=0, description="Total publications tracked")
    performance_summary: Dict[str, Any] = Field(..., description="Performance summary")
    placeholder_note: str = Field(..., description="Placeholder status note")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    placeholder_mode: bool = Field(default=True, description="Whether service is in placeholder mode")
    future_capabilities: List[str] = Field(..., description="Future analytics capabilities")
    error: Optional[str] = Field(None, description="Error message if unhealthy")