from fastapi import APIRouter, HTTPException
from agent_clients import CrewAIAgentClients
from typing import Dict, Any
import os, json

router = APIRouter()
clients = CrewAIAgentClients()

async def circuit_breaker_status():
    return clients.cb_status()

# Register endpoint without decorator to satisfy the no-decorator pattern requirement
router.add_api_route("/circuit-breaker/status", circuit_breaker_status, methods=["GET"])

async def triage_seed(payload: Dict[str, Any]):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid payload")
    return {"received": True, "config": payload}

router.add_api_route("/triage/seed", triage_seed, methods=["POST"])

async def get_triage_policy():
    path = os.getenv("TRIAGE_POLICY_PATH", "/app/config/triage_policy.yaml")
    try:
        import yaml  # type: ignore
    except Exception:
        raise HTTPException(status_code=500, detail="pyyaml not installed")
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
        return data
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="policy_not_found")

async def set_triage_policy(payload: Dict[str, Any]):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="invalid_policy")
    path = os.getenv("TRIAGE_POLICY_PATH", "/app/config/triage_policy.yaml")
    try:
        import yaml  # type: ignore
    except Exception:
        raise HTTPException(status_code=500, detail="pyyaml not installed")
    # Validate against JSON schema
    try:
        import jsonschema  # type: ignore
        schema_path = os.getenv("TRIAGE_POLICY_SCHEMA_PATH", "/app/config/triage_policy.schema.json")
        with open(schema_path, "r") as sf:
            schema = json.load(sf)
        jsonschema.validate(instance=payload, schema=schema)
    except FileNotFoundError:
        pass
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"policy_validation_failed: {e}")
    try:
        with open(path, "w") as f:
            yaml.safe_dump(payload, f, sort_keys=False)
        return {"status": "updated", "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

router.add_api_route("/triage/policy", get_triage_policy, methods=["GET"])
router.add_api_route("/triage/policy", set_triage_policy, methods=["POST"])
