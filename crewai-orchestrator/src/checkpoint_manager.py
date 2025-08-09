from __future__ import annotations
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

from agent_clients import CrewAIAgentClients


class CheckpointType(str, Enum):
    PRE_WRITING = "pre_writing"
    MID_WRITING = "mid_writing"
    POST_WRITING = "post_writing"


class CheckpointStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_USER = "waiting_user"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CheckpointState:
    checkpoint_id: str
    checkpoint: CheckpointType
    content: str
    platform: str
    status: CheckpointStatus = CheckpointStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=lambda: time.time())
    updated_at: float = field(default_factory=lambda: time.time())
    error_message: Optional[str] = None
    user_notes: Optional[str] = None


class CheckpointManager:
    def __init__(self, clients: CrewAIAgentClients) -> None:
        self.clients = clients
        self.active: Dict[str, CheckpointState] = {}

    async def create(self, content: str, platform: str, checkpoint: str, user_notes: Optional[str] = None) -> str:
        ctype = self._parse_checkpoint(checkpoint)
        chk_id = f"chk_{uuid.uuid4().hex[:8]}"
        state = CheckpointState(
            checkpoint_id=chk_id,
            checkpoint=ctype,
            content=content,
            platform=platform,
            status=CheckpointStatus.RUNNING,
            user_notes=user_notes,
        )
        self.active[chk_id] = state

        async def _run():
            try:
                # Map checkpoint to a responsible agent for selective validation
                agent = self._agent_for_checkpoint(ctype)
                client = self.clients.get_agent(agent)
                # Run selective validation with implicit checkpoint mapping in client
                result = await client.validate_content(content, platform, validation_mode="selective")
                state.result = result
                state.status = CheckpointStatus.WAITING_USER
                state.updated_at = time.time()
            except Exception as e:
                state.status = CheckpointStatus.FAILED
                state.error_message = str(e)
                state.updated_at = time.time()

        asyncio.create_task(_run())
        return chk_id

    async def intervene(self, checkpoint_id: str, user_input: str, finalize: bool = False) -> Dict[str, Any]:
        state = self.active.get(checkpoint_id)
        if not state:
            return {"error": "not_found"}
        if state.status not in {CheckpointStatus.WAITING_USER, CheckpointStatus.RUNNING}:
            return {"error": f"cannot_intervene_in_status_{state.status}"}

        # Apply simple modification: append user note or replace content if directive provided
        if user_input:
            # If directive format is replace::<old>::<new>
            if user_input.startswith("replace::") and "::" in user_input[9:]:
                try:
                    _, old_text, new_text = user_input.split("::", 2)
                    if old_text and old_text in state.content:
                        state.content = state.content.replace(old_text, new_text)
                except ValueError:
                    # Fallback to append note
                    state.content = f"{state.content}\n\n[USER_NOTE]: {user_input}"
            else:
                state.content = f"{state.content}\n\n[USER_NOTE]: {user_input}"
            state.updated_at = time.time()

        if finalize:
            state.status = CheckpointStatus.COMPLETED
            state.updated_at = time.time()
            return {"status": state.status, "checkpoint_id": state.checkpoint_id}

        # Re-validate after intervention
        state.status = CheckpointStatus.RUNNING
        state.updated_at = time.time()

        async def _revalidate():
            try:
                agent = self._agent_for_checkpoint(state.checkpoint)
                client = self.clients.get_agent(agent)
                result = await client.validate_content(state.content, state.platform, validation_mode="selective")
                state.result = result
                state.status = CheckpointStatus.WAITING_USER
                state.updated_at = time.time()
            except Exception as e:
                state.status = CheckpointStatus.FAILED
                state.error_message = str(e)
                state.updated_at = time.time()

        asyncio.create_task(_revalidate())
        return {"status": "revalidating", "checkpoint_id": state.checkpoint_id}

    async def get_status(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        state = self.active.get(checkpoint_id)
        if not state:
            return None
        return {
            "checkpoint_id": state.checkpoint_id,
            "checkpoint": state.checkpoint.value,
            "status": state.status.value,
            "content_preview": state.content[:200],
            "result": state.result,
            "created_at": state.created_at,
            "updated_at": state.updated_at,
            "error_message": state.error_message,
        }

    async def list_active(self) -> Dict[str, Any]:
        return {
            cid: {
                "checkpoint": st.checkpoint.value,
                "status": st.status.value,
                "created_at": st.created_at,
            }
            for cid, st in self.active.items()
        }

    def _parse_checkpoint(self, checkpoint: str) -> CheckpointType:
        mapping = {
            "pre_writing": CheckpointType.PRE_WRITING,
            "mid_writing": CheckpointType.MID_WRITING,
            "post_writing": CheckpointType.POST_WRITING,
        }
        if checkpoint not in mapping:
            raise ValueError(f"Unknown checkpoint: {checkpoint}")
        return mapping[checkpoint]

    def _agent_for_checkpoint(self, ctype: CheckpointType) -> str:
        return {
            CheckpointType.PRE_WRITING: "audience",
            CheckpointType.MID_WRITING: "writer",
            CheckpointType.POST_WRITING: "quality",
        }[ctype]
