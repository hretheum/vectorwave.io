from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
import asyncio
import time
import uuid
from dataclasses import dataclass, field

from agent_clients import CrewAIAgentClients


class LinearFlowEngine:
    """Deterministic multi-agent flow research→audience→writer→style→quality.

    Each step may return suggestions; we apply a simple mutation strategy to
    feed improved content to the next step.
    """

    ORDER: Tuple[str, ...] = (
        "research",
        "audience",
        "writer",
        "style",
        "quality",
    )

    def __init__(self, clients: CrewAIAgentClients) -> None:
        self.clients = clients
        self.active: Dict[str, "FlowState"] = {}

    async def run(
        self,
        content: str,
        platform: str,
        content_type: str = "article",
        prefer_comprehensive: Optional[Dict[str, bool]] = None,
        direct_content: bool = True,
    ) -> Dict[str, Any]:
        # If direct_content=false, use AI Writing Flow instead of traditional agents
        if not direct_content:
            # Generate topic data from content
            topic_data = {
                "title": content.split('\n')[0] if '\n' in content else content[:50],
                "description": content,
                "content_type": content_type.upper(),
                "content_ownership": "ORIGINAL",
            }
            
            # Call AI Writing Flow
            aiwf_result = await self.clients.ai_writing_flow.generate(
                topic_data=topic_data,
                platform=platform,
                mode="selective"
            )
            
            if aiwf_result:
                return {
                    "steps": [{
                        "agent": "ai_writing_flow",
                        "mode": "selective",
                        "result": aiwf_result
                    }],
                    "final_content": aiwf_result.get("content", content),
                    "ai_writing_flow_used": True,
                    "validation_results": aiwf_result.get("validation_results", {}),
                    "checkpoints_passed": aiwf_result.get("checkpoints_passed", {})
                }
        
        # Traditional flow with direct_content=true
        prefer = prefer_comprehensive or {}
        current_content = content
        results: Dict[str, Any] = {"steps": [], "ai_writing_flow_used": False}

        for agent in self.ORDER:
            mode = "comprehensive" if prefer.get(agent, agent in ("research", "audience", "style", "quality")) else "selective"
            client = self.clients.get_agent(agent)
            validation = await client.validate_content(current_content, platform, validation_mode=mode)
            results["steps"].append({"agent": agent, "mode": mode, "result": validation})
            # Mutate content with suggestions if present
            suggestions: List[str] = validation.get("suggestions", []) if isinstance(validation, dict) else []
            if suggestions:
                current_content = self._apply_suggestions(current_content, suggestions)
        results["final_content"] = current_content
        return results

    # --- Stateful execution API ---
    async def execute_flow(self, content: str, platform: str, content_type: str = "article", 
                          direct_content: bool = True) -> str:
        flow_id = f"flow_{uuid.uuid4().hex[:8]}"
        self.active[flow_id] = FlowState(
            flow_id=flow_id,
            status="running",
            current_agent=None,
            progress=0.0,
            chromadb_sourced=True,
            created_at=time.time(),
            updated_at=time.time(),
            result=None,
            ai_writing_flow_used=not direct_content,
        )

        async def _runner():
            state = self.active[flow_id]
            try:
                # Use AI Writing Flow if direct_content=false
                if not direct_content:
                    state.current_agent = "ai_writing_flow"
                    state.progress = 10.0
                    state.updated_at = time.time()
                    
                    topic_data = {
                        "title": content.split('\n')[0] if '\n' in content else content[:50],
                        "description": content,
                        "content_type": content_type.upper(),
                        "content_ownership": "ORIGINAL",
                    }
                    
                    aiwf_result = await self.clients.ai_writing_flow.generate(
                        topic_data=topic_data,
                        platform=platform,
                        mode="selective"
                    )
                    
                    state.progress = 100.0
                    state.status = "completed"
                    state.result = {
                        "steps": [{"agent": "ai_writing_flow", "mode": "selective", "result": aiwf_result}],
                        "final_content": aiwf_result.get("content", content) if aiwf_result else content,
                        "ai_writing_flow_used": True,
                        "validation_results": aiwf_result.get("validation_results", {}) if aiwf_result else {},
                        "checkpoints_passed": aiwf_result.get("checkpoints_passed", {}) if aiwf_result else {}
                    }
                    state.updated_at = time.time()
                    return
                
                # Traditional flow with direct_content=true
                steps_total = len(self.ORDER)
                current_content = content
                results: List[Dict[str, Any]] = []
                for idx, agent in enumerate(self.ORDER, start=1):
                    state.current_agent = agent
                    state.progress = round(((idx - 1) / steps_total) * 100.0, 2)
                    state.updated_at = time.time()
                    client = self.clients.get_agent(agent)
                    # Prefer comprehensive by default for non-writer
                    mode = "comprehensive" if agent != "writer" else "selective"
                    validation = await client.validate_content(current_content, platform, validation_mode=mode)
                    # Heuristic chromadb sourced: rules_applied present and not empty
                    try:
                        if not (isinstance(validation, dict) and validation.get("rules_applied")):
                            state.chromadb_sourced = False
                    except Exception:
                        state.chromadb_sourced = False
                    results.append({"agent": agent, "mode": mode, "result": validation})
                    suggestions: List[str] = validation.get("suggestions", []) if isinstance(validation, dict) else []
                    if suggestions:
                        current_content = self._apply_suggestions(current_content, suggestions)
                state.progress = 100.0
                state.status = "completed"
                state.result = {"steps": results, "final_content": current_content, "ai_writing_flow_used": False}
                state.updated_at = time.time()
            except Exception as e:
                state.status = "failed"
                state.error_message = str(e)
                state.updated_at = time.time()

        asyncio.create_task(_runner())
        return flow_id

    async def get_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        state = self.active.get(flow_id)
        if not state:
            return None
        return state.to_dict()

    async def list_active(self) -> Dict[str, Any]:
        return {fid: st.to_compact() for fid, st in self.active.items() if st.status in ("running", "waiting_user")}

    def _apply_suggestions(self, content: str, suggestions: List[str]) -> str:
        # Simple strategy: append top-3 suggestions as actionable bullets at end
        top = suggestions[:3]
        if not top:
            return content
        lines = [content.strip(), "", "Improvements applied:"] + [f"- {s}" for s in top]
        return "\n".join(lines)


@dataclass
class FlowState:
    flow_id: str
    status: str  # running | completed | failed | waiting_user
    current_agent: Optional[str]
    progress: float
    chromadb_sourced: bool
    created_at: float
    updated_at: float
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    ai_writing_flow_used: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "status": self.status,
            "current_agent": self.current_agent,
            "progress": self.progress,
            "chromadb_sourced": self.chromadb_sourced,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result": self.result,
            "error_message": self.error_message,
            "ai_writing_flow_used": self.ai_writing_flow_used,
        }

    def to_compact(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "current_agent": self.current_agent,
            "progress": self.progress,
        }
