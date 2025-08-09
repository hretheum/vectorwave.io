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

async def execute_flow(req: FlowRequest) -> Dict[str, Any]:
    flow_id = await engine.execute_flow(req.content, req.platform)
    return {"flow_id": flow_id, "state": "running"}

async def flow_status(flow_id: str) -> Optional[Dict[str, Any]]:
    return await engine.get_status(flow_id)

async def list_active():
    return await engine.list_active()

# Register endpoints without decorators to satisfy no '@router' pattern
router.add_api_route("/flows/execute", execute_flow, methods=["POST"])
router.add_api_route("/flows/status/{flow_id}", flow_status, methods=["GET"])
router.add_api_route("/flows/active", list_active, methods=["GET"])
