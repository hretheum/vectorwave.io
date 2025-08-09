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

@router.post("/flows/execute")
async def execute_flow(req: FlowRequest) -> Dict[str, Any]:
    flow_id = await engine.execute_flow(req.content, req.platform)
    return {"flow_id": flow_id, "state": "running"}

@router.get("/flows/status/{flow_id}")
async def flow_status(flow_id: str) -> Optional[Dict[str, Any]]:
    return await engine.get_status(flow_id)

@router.get("/flows/active")
async def list_active():
    return await engine.list_active()
