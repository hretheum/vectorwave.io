from fastapi import FastAPI
import os
import asyncio
from checkpoint_manager import CheckpointManager
from agent_clients import CrewAIAgentClients
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import time
from api import router as api_router
from flows_api import router as flows_router
from checkpoints_api import router as checkpoints_router
from monitoring_api import router as monitoring_router
from aiwf_client import AIWritingFlowClient

app = FastAPI(
    title="CrewAI Orchestrator Service",
    version="1.0.0",
    description="Orchestrates CrewAI agents with ChromaDB validation"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(flows_router)
app.include_router(checkpoints_router)
app.include_router(monitoring_router)

# Minimal proxy to AI Writing Flow for smoke/E2E
_aiwf_client = AIWritingFlowClient(os.getenv("AI_WRITING_FLOW_URL", "http://ai-writing-flow-service:8044"))

@app.get("/aiwf/health")
async def aiwf_health_proxy():
    return await _aiwf_client.health()

class AgentInfo(BaseModel):
    agent_id: str
    agent_type: str | None = None
    metadata: Dict[str, Any] | None = None

_registered_agents: Dict[str, Dict[str, Any]] = {}
_start_time = time.time()
_sequence_ready = False

async def _init_sequence_readiness() -> None:
    global _sequence_ready
    try:
        clients = CrewAIAgentClients()
        cm = CheckpointManager(clients)
        r = await cm._get_redis()
        _sequence_ready = bool(r)
    except Exception:
        _sequence_ready = False

# Kick off readiness check on startup
asyncio.get_event_loop().create_task(_init_sequence_readiness())

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "crewai-orchestrator",
        "version": "1.0.0",
        "port": 8042,
        "registered_agents": len(_registered_agents),
        "uptime_seconds": round(time.time() - _start_time, 3),
        "sequence_ready": _sequence_ready,
    }

@app.get("/agents/registered")
async def get_registered():
    return list(_registered_agents.keys())

@app.post("/agents/register")
async def register(agent: AgentInfo):
    _registered_agents[agent.agent_id] = agent.model_dump()
    return {"status": "registered", "agent_id": agent.agent_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8042)
