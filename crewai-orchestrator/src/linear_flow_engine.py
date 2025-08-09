from __future__ import annotations
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from agent_clients import CrewAIAgentClients


class FlowState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FlowExecution:
    flow_id: str
    content: str
    platform: str
    state: FlowState = FlowState.PENDING
    current_agent: Optional[str] = None
    agent_results: Dict[str, Any] = field(default_factory=dict)
    failed_agents: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: time.time())
    updated_at: float = field(default_factory=lambda: time.time())
    error_message: Optional[str] = None


class LinearFlowEngine:
    def __init__(self, clients: CrewAIAgentClients, fail_fast: bool = False) -> None:
        self.clients = clients
        self.active: Dict[str, FlowExecution] = {}
        self.sequence: List[str] = ["research", "audience", "writer", "style", "quality"]
        self.fail_fast = fail_fast

    async def execute_flow(self, content: str, platform: str) -> str:
        flow_id = f"flow_{uuid.uuid4().hex[:8]}"
        fx = FlowExecution(flow_id=flow_id, content=content, platform=platform, state=FlowState.RUNNING)
        self.active[flow_id] = fx

        async def _run():
            try:
                current_content = content
                any_success = False
                for agent in self.sequence:
                    fx.current_agent = agent
                    fx.updated_at = time.time()
                    client = self.clients.get_agent(agent)
                    try:
                        # Call Editorial Service; may fallback to health if validate endpoint missing
                        result = await client.validate_content(
                            current_content, platform, validation_mode=self._mode_for(agent)
                        )
                        fx.agent_results[agent] = result
                        any_success = True
                        # Simple suggestion application if present
                        suggestions = result.get("suggestions") if isinstance(result, dict) else None
                        if isinstance(suggestions, list):
                            for s in suggestions:
                                if s.get("type") == "replacement" and s.get("apply_automatically"):
                                    old_text = s.get("old_text", "")
                                    new_text = s.get("new_text", "")
                                    if old_text and old_text in current_content:
                                        current_content = current_content.replace(old_text, new_text)
                    except Exception as step_error:
                        fx.agent_results[agent] = {"error": str(step_error)}
                        fx.failed_agents.append(agent)
                        if self.fail_fast:
                            raise
                        # continue to next agent
                        continue
                fx.state = FlowState.COMPLETED if any_success else FlowState.FAILED
                fx.current_agent = None
                fx.updated_at = time.time()
            except Exception as e:
                fx.state = FlowState.FAILED
                fx.error_message = str(e)
                fx.updated_at = time.time()

        asyncio.create_task(_run())
        return flow_id

    async def get_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        fx = self.active.get(flow_id)
        if not fx:
            return None
        progress = len(fx.agent_results) / len(self.sequence) * 100.0
        return {
            "flow_id": fx.flow_id,
            "state": fx.state.value,
            "current_agent": fx.current_agent,
            "progress": round(progress, 1),
            "agent_results": fx.agent_results,
            "failed_agents": fx.failed_agents,
            "created_at": fx.created_at,
            "updated_at": fx.updated_at,
            "error_message": fx.error_message,
            "sequential_execution": True,
        }

    async def list_active(self) -> List[Dict[str, Any]]:
        return [
            {"flow_id": fx.flow_id, "state": fx.state.value, "current_agent": fx.current_agent, "created_at": fx.created_at}
            for fx in self.active.values()
        ]

    def _mode_for(self, agent: str) -> str:
        return {
            "research": "selective",
            "audience": "selective",
            "writer": "selective",
            "style": "comprehensive",
            "quality": "comprehensive",
        }.get(agent, "selective")
