from fastapi import APIRouter
from .agent_clients import CrewAIAgentClients

router = APIRouter()
clients = CrewAIAgentClients()

@router.get("/circuit-breaker/status")
async def circuit_breaker_status():
    return clients.cb_status()
