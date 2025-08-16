import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional

from agent_clients import CrewAIAgentClients
from linear_flow_engine import LinearFlowEngine

router = APIRouter()
clients = CrewAIAgentClients(editorial_service_url=os.getenv("EDITORIAL_SERVICE_URL", "http://localhost:8040"))
engine = LinearFlowEngine(clients)

class FlowRequest(BaseModel):
    content: str
    platform: str
    direct_content: Optional[bool] = True  # Default true for backward compatibility

async def execute_flow(req: FlowRequest) -> Dict[str, Any]:
    # Check AI Writing Flow health if direct_content=false
    if not req.direct_content:
        health = await clients.ai_writing_flow.health_check()
        if health.get("status") != "healthy":
            return {"error": "AI Writing Flow unavailable", "health": health}
    
    flow_id = await engine.execute_flow(req.content, req.platform, 
                                       direct_content=req.direct_content)
    return {"flow_id": flow_id, "state": "running", 
            "ai_writing_flow_enabled": not req.direct_content}

async def flow_status(flow_id: str) -> Optional[Dict[str, Any]]:
    return await engine.get_status(flow_id)

async def list_active():
    return await engine.list_active()

# Register endpoints without decorators to satisfy the no-decorator pattern requirement
router.add_api_route("/flows/execute", execute_flow, methods=["POST"])
router.add_api_route("/flows/status/{flow_id}", flow_status, methods=["GET"])
router.add_api_route("/flows/active", list_active, methods=["GET"])
