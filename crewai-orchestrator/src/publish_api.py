"""
Publish API endpoints for content generation and publication
"""

import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

from ai_writing_flow_client import AIWritingFlowClient
from linear_flow_engine import LinearFlowEngine
from agent_clients import CrewAIAgentClients

router = APIRouter()

# Initialize clients
ai_writing_flow = AIWritingFlowClient()
editorial_clients = CrewAIAgentClients(
    editorial_service_url=os.getenv("EDITORIAL_SERVICE_URL", "http://localhost:8040")
)
flow_engine = LinearFlowEngine(editorial_clients)


class PublishRequest(BaseModel):
    """Request model for content publication"""
    topic: Dict[str, Any] = Field(..., description="Topic information")
    platform: str = Field(default="general", description="Target platform")
    direct_content: bool = Field(default=True, description="If false, generate content via AI Writing Flow")
    content: Optional[str] = Field(default=None, description="Direct content if provided")


class PublishResponse(BaseModel):
    """Response model for publication request"""
    publication_id: str
    status: str
    content: str
    metadata: Dict[str, Any]
    ai_writing_flow_used: bool


@router.post("/publish", response_model=PublishResponse)
async def publish_content(request: PublishRequest):
    """
    Publish content with optional AI Writing Flow generation
    
    When direct_content=false, the content is generated via AI Writing Flow pipeline
    """
    try:
        import uuid
        publication_id = str(uuid.uuid4())
        
        if not request.direct_content:
            # Generate content via AI Writing Flow
            topic_title = request.topic.get("title", "Untitled")
            topic_description = request.topic.get("description", "")
            viral_score = request.topic.get("viral_score", 7.5)
            
            # Generate content
            ai_result = await ai_writing_flow.generate_content(
                topic_title=topic_title,
                topic_description=topic_description,
                platform=request.platform,
                viral_score=viral_score
            )
            
            content = ai_result.get("content", "")
            metadata = {
                "generated_by": "ai_writing_flow",
                "agents_used": ai_result.get("agents_used", []),
                "processing_time": ai_result.get("processing_time", 0),
                "topic": request.topic,
                "platform": request.platform
            }
            ai_flow_used = True
            
        else:
            # Use provided content directly
            if not request.content:
                raise HTTPException(
                    status_code=400, 
                    detail="Content is required when direct_content=true"
                )
            
            content = request.content
            
            # Optionally validate through editorial service
            validation_result = await flow_engine.validate(content, request.platform)
            
            metadata = {
                "generated_by": "direct",
                "validation_result": validation_result,
                "topic": request.topic,
                "platform": request.platform
            }
            ai_flow_used = False
        
        return PublishResponse(
            publication_id=publication_id,
            status="completed",
            content=content,
            metadata=metadata,
            ai_writing_flow_used=ai_flow_used
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/ai-writing-flow")
async def check_ai_writing_flow_health():
    """Check AI Writing Flow service health"""
    try:
        health_status = await ai_writing_flow.check_health()
        return {
            "status": health_status.value,
            "service": "ai-writing-flow",
            "url": ai_writing_flow.base_url
        }
    except Exception as e:
        return {
            "status": "error",
            "service": "ai-writing-flow",
            "error": str(e)
        }