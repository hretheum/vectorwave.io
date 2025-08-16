import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

from agent_clients import CrewAIAgentClients
from linear_flow_engine import LinearFlowEngine
from ai_writing_flow_client import AIWritingFlowClient

router = APIRouter()
clients = CrewAIAgentClients(editorial_service_url=os.getenv("EDITORIAL_SERVICE_URL", "http://localhost:8040"))
engine = LinearFlowEngine(clients)
ai_writing_flow = AIWritingFlowClient()


class FlowRequest(BaseModel):
    content: str
    platform: str = "general"
    direct_content: bool = Field(default=True, description="If false, generate content via AI Writing Flow")
    topic: Optional[Dict[str, Any]] = Field(default=None, description="Topic metadata for content generation")


class FlowResponse(BaseModel):
    status: str
    content: str
    metadata: Dict[str, Any]
    agents_used: list = []
    source: str = "direct"  # "direct" or "ai_writing_flow"


async def execute_flow_handler(request: FlowRequest):
    """Execute the content flow with optional AI Writing Flow generation"""
    try:
        # Check if we should use AI Writing Flow for content generation
        if not request.direct_content:
            # Extract topic information
            topic_title = request.topic.get("title", "Untitled") if request.topic else "Untitled"
            topic_description = request.topic.get("description", request.content) if request.topic else request.content
            viral_score = request.topic.get("viral_score", 7.5) if request.topic else 7.5
            
            # Generate content via AI Writing Flow
            ai_result = await ai_writing_flow.generate_content(
                topic_title=topic_title,
                topic_description=topic_description,
                platform=request.platform,
                viral_score=viral_score
            )
            
            # Use generated content for further processing
            content = ai_result.get("content", request.content)
            agents_used = ai_result.get("agents_used", [])
            source = "ai_writing_flow"
        else:
            # Use provided content directly
            content = request.content
            agents_used = []
            source = "direct"
        
        # Execute linear flow engine for validation/enhancement
        result = await engine.execute(content, request.platform)
        
        # Combine agents used
        if result.get("steps"):
            for step in result["steps"]:
                agent = step.get("agent")
                if agent and agent not in agents_used:
                    agents_used.append(agent)
        
        return FlowResponse(
            status="completed",
            content=result.get("final_content", content),
            metadata={
                "platform": request.platform,
                "direct_content": request.direct_content,
                "flow_results": result,
                "topic": request.topic
            },
            agents_used=agents_used,
            source=source
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def validate_flow_handler(request: FlowRequest):
    """Validate content through the flow"""
    try:
        # If not direct content, process through AI Writing Flow first
        if not request.direct_content:
            topic_title = request.topic.get("title", "Untitled") if request.topic else "Untitled"
            topic_description = request.topic.get("description", request.content) if request.topic else request.content
            
            # Process through AI Writing Flow
            ai_result = await ai_writing_flow.process_content(
                content=request.content,
                platform=request.platform,
                topic=request.topic,
                validation_mode="selective"
            )
            content = ai_result.get("content", request.content)
        else:
            content = request.content
        
        # Validate through linear flow
        result = await engine.validate(content, request.platform)
        
        return {
            "status": "validated",
            "results": result,
            "content": content,
            "direct_content": request.direct_content
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Register endpoints
router.add_api_route("/flows/execute", execute_flow_handler, methods=["POST"], response_model=FlowResponse)
router.add_api_route("/flows/validate", validate_flow_handler, methods=["POST"])
