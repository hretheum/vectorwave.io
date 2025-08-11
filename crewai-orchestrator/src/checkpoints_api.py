import os
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from agent_clients import CrewAIAgentClients
from checkpoint_manager import CheckpointManager

router = APIRouter()
clients = CrewAIAgentClients(editorial_service_url=os.getenv("EDITORIAL_SERVICE_URL", "http://localhost:8040"))
manager = CheckpointManager(clients)

class CreateCheckpointRequest(BaseModel):
    content: str
    platform: str
    checkpoint: str  # pre_writing | mid_writing | post_writing
    user_notes: Optional[str] = None

async def create_checkpoint(req: CreateCheckpointRequest) -> Dict[str, Any]:
    chk_id = await manager.create(req.content, req.platform, req.checkpoint, req.user_notes)
    return {"checkpoint_id": chk_id, "status": "running"}

async def get_checkpoint_status(checkpoint_id: str) -> Optional[Dict[str, Any]]:
    return await manager.get_status(checkpoint_id)

class InterveneRequest(BaseModel):
    user_input: str
    finalize: bool = False

async def intervene(checkpoint_id: str, req: InterveneRequest) -> Dict[str, Any]:
    return await manager.intervene(checkpoint_id, req.user_input, req.finalize)

async def list_checkpoints() -> Dict[str, Any]:
    return await manager.list_active()

async def get_checkpoint_history(checkpoint_id: str) -> List[Dict[str, Any]]:
    return await manager.get_history(checkpoint_id)

class StartSequenceRequest(BaseModel):
    content: str
    platform: str

async def start_sequence(req: StartSequenceRequest) -> Dict[str, Any]:
    fid = await manager.start_sequence(req.content, req.platform)
    return {"flow_id": fid, "status": "running"}

async def sequence_status(flow_id: str) -> Dict[str, Any]:
    return await manager.get_sequence_status(flow_id)

# Register endpoints
router.add_api_route("/checkpoints/create", create_checkpoint, methods=["POST"])
router.add_api_route("/checkpoints/status/{checkpoint_id}", get_checkpoint_status, methods=["GET"])
router.add_api_route("/checkpoints/{checkpoint_id}/intervene", intervene, methods=["POST"])
router.add_api_route("/checkpoints/active", list_checkpoints, methods=["GET"])
router.add_api_route("/checkpoints/history/{checkpoint_id}", get_checkpoint_history, methods=["GET"])
router.add_api_route("/checkpoints/sequence/start", start_sequence, methods=["POST"])
router.add_api_route("/checkpoints/sequence/status/{flow_id}", sequence_status, methods=["GET"])
