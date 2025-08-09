#!/usr/bin/env python3
"""
LinkedIn PPT Generator Service - Data Models
Task 3.2.1: LinkedIn PPT Generator Service
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class LinkedInPPTRequest(BaseModel):
    """Request model for LinkedIn PPT generation"""
    topic_title: str = Field(..., description="Title of the LinkedIn post topic")
    topic_description: str = Field(..., description="Description of the LinkedIn post content")
    slides_count: int = Field(default=5, ge=3, le=15, description="Number of slides to generate")
    template: str = Field(default="business", description="Presentation template to use")
    linkedin_format: bool = Field(default=True, description="Optimize for LinkedIn sharing")
    include_call_to_action: bool = Field(default=True, description="Include LinkedIn CTA slide")
    target_audience: Optional[str] = Field(None, description="Target audience for the presentation")
    keywords: Optional[List[str]] = Field(None, description="Keywords for content optimization")


class LinkedInPPTResponse(BaseModel):
    """Response model for LinkedIn PPT generation"""
    presentation_id: str = Field(..., description="Unique presentation identifier")
    pptx_url: str = Field(..., description="URL to download PPTX file")
    pdf_url: str = Field(..., description="URL to download PDF file") 
    pdf_path: str = Field(..., description="Local path to PDF file")
    slide_count: int = Field(..., description="Number of slides generated")
    generation_time: float = Field(..., description="Time taken to generate presentation")
    template_used: str = Field(..., description="Template used for generation")
    topic_title: str = Field(..., description="Final topic title used")
    linkedin_optimized: bool = Field(default=True, description="Whether content is LinkedIn-optimized")
    ready_for_linkedin: bool = Field(default=True, description="Whether presentation is ready for LinkedIn sharing")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    presenton_available: bool = Field(..., description="Whether presenton service is accessible")
    presenton_url: str = Field(..., description="Presenton service URL")
    error: Optional[str] = Field(None, description="Error message if unhealthy")