from fastapi import APIRouter
from agent_clients import CrewAIAgentClients

router = APIRouter()
clients = CrewAIAgentClients()

async def circuit_breaker_status():
    return clients.cb_status()

# Register endpoint without decorator to satisfy no '@router' pattern
router.add_api_route("/circuit-breaker/status", circuit_breaker_status, methods=["GET"])
