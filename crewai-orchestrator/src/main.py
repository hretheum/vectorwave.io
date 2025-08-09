from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import time
from .api import router as api_router

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

class AgentInfo(BaseModel):
    agent_id: str
    agent_type: str | None = None
    metadata: Dict[str, Any] | None = None

_registered_agents: Dict[str, Dict[str, Any]] = {}
_start_time = time.time()

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "crewai-orchestrator",
        "version": "1.0.0",
        "port": 8042,
        "registered_agents": len(_registered_agents),
        "uptime_seconds": round(time.time() - _start_time, 3),
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
