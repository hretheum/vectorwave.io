from fastapi import APIRouter
from typing import Dict, Any

from agent_clients import CrewAIAgentClients

router = APIRouter()
_clients: CrewAIAgentClients | None = None

def _get_clients() -> CrewAIAgentClients:
    global _clients
    if _clients is None:
        _clients = CrewAIAgentClients()
    return _clients

async def metrics() -> Dict[str, Any]:
    clients = _get_clients()
    return await clients.perf_metrics()

# Expose metrics under /monitoring/agents/performance
router.add_api_route("/monitoring/agents/performance", metrics, methods=["GET"])

async def circuit_breaker_status() -> Dict[str, Any]:
    clients = _get_clients()
    return clients.cb_status()

# Expose circuit breaker snapshot
router.add_api_route("/monitoring/agents/circuit-breaker", circuit_breaker_status, methods=["GET"])
