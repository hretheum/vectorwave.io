from __future__ import annotations
import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, List, Tuple
import os
import json
import redis.asyncio as aioredis

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
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis | None:
        if self.redis is not None:
            return self.redis
        try:
            self.redis = aioredis.from_url(self.redis_url)
            # sanity ping
            await self.redis.ping()
            return self.redis
        except Exception:
            self.redis = None
            return None

    def _rk_state(self, checkpoint_id: str) -> str:
        return f"vw:orch:chk:{checkpoint_id}:state"

    def _rk_events(self, checkpoint_id: str) -> str:
        return f"vw:orch:chk:{checkpoint_id}:events"

    def _rk_flow(self, flow_id: str) -> str:
        return f"vw:orch:flow:{flow_id}:checkpoints"

    def _rk_flow_meta(self, flow_id: str) -> str:
        return f"vw:orch:flow:{flow_id}:meta"

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

        # Best-effort persist to Redis and add event
        await self._persist_state(state)
        await self._append_event(chk_id, "created", {"checkpoint": ctype.value, "platform": platform})

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
                await self._persist_state(state)
                await self._append_event(chk_id, "validated", {"rule_count": result.get("rule_count")})
            except Exception as e:
                state.status = CheckpointStatus.FAILED
                state.error_message = str(e)
                state.updated_at = time.time()
                await self._persist_state(state)
                await self._append_event(chk_id, "failed", {"error": str(e)})

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
            await self._persist_state(state)
            await self._append_event(checkpoint_id, "intervene", {"user_input": user_input})

        if finalize:
            state.status = CheckpointStatus.COMPLETED
            state.updated_at = time.time()
            await self._persist_state(state)
            await self._append_event(checkpoint_id, "finalized", {})
            return {"status": state.status, "checkpoint_id": state.checkpoint_id}

        # Re-validate after intervention
        state.status = CheckpointStatus.RUNNING
        state.updated_at = time.time()
        await self._persist_state(state)
        await self._append_event(checkpoint_id, "revalidating", {})

        async def _revalidate():
            try:
                agent = self._agent_for_checkpoint(state.checkpoint)
                client = self.clients.get_agent(agent)
                result = await client.validate_content(state.content, state.platform, validation_mode="selective")
                state.result = result
                state.status = CheckpointStatus.WAITING_USER
                state.updated_at = time.time()
                await self._persist_state(state)
                await self._append_event(checkpoint_id, "revalidated", {"rule_count": result.get("rule_count")})
            except Exception as e:
                state.status = CheckpointStatus.FAILED
                state.error_message = str(e)
                state.updated_at = time.time()
                await self._persist_state(state)
                await self._append_event(checkpoint_id, "failed", {"error": str(e)})

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

    async def get_history(self, checkpoint_id: str) -> List[Dict[str, Any]]:
        r = await self._get_redis()
        if not r:
            return []
        key = self._rk_events(checkpoint_id)
        items = await r.lrange(key, 0, -1)
        out: List[Dict[str, Any]] = []
        for raw in items:
            try:
                out.append(json.loads(raw))
            except Exception:
                continue
        return out

    async def _persist_state(self, state: CheckpointState) -> None:
        r = await self._get_redis()
        if not r:
            return
        await r.hset(
            self._rk_state(state.checkpoint_id),
            mapping={
                "checkpoint": state.checkpoint.value,
                "platform": state.platform,
                "status": state.status.value,
                "content": state.content,
                "result": json.dumps(state.result) if state.result is not None else "null",
                "created_at": str(state.created_at),
                "updated_at": str(state.updated_at),
                "error_message": state.error_message or "",
            },
        )
        # 24h TTL
        await r.expire(self._rk_state(state.checkpoint_id), 60 * 60 * 24)

    async def _append_event(self, checkpoint_id: str, event_type: str, data: Dict[str, Any]) -> None:
        r = await self._get_redis()
        if not r:
            return
        evt = {
            "ts": time.time(),
            "type": event_type,
            "data": data,
        }
        await r.rpush(self._rk_events(checkpoint_id), json.dumps(evt))
        await r.expire(self._rk_events(checkpoint_id), 60 * 60 * 24)

    # --- Sequence (pre -> mid -> post) ---
    async def start_sequence(self, content: str, platform: str) -> str:
        flow_id = f"cflow_{uuid.uuid4().hex[:8]}"
        r = await self._get_redis()
        if r:
            await r.delete(self._rk_flow(flow_id))
            await r.hset(
                self._rk_flow_meta(flow_id),
                mapping={
                    "status": "running",
                    "current_step": "pre_writing",
                    "created_at": str(time.time()),
                    "updated_at": str(time.time()),
                },
            )

        async def _runner():
            order = [
                CheckpointType.PRE_WRITING.value,
                CheckpointType.MID_WRITING.value,
                CheckpointType.POST_WRITING.value,
            ]
            current_content = content
            try:
                for idx, cp in enumerate(order):
                    chk_id = await self.create(current_content, platform, cp)
                    if r:
                        await r.rpush(self._rk_flow(flow_id), chk_id)
                        await r.hset(self._rk_flow_meta(flow_id), mapping={
                            "current_step": cp,
                            "updated_at": str(time.time()),
                        })
                    # Best-effort wait a short time for validation to complete
                    for _ in range(40):  # up to ~10s
                        st = self.active.get(chk_id)
                        if st and st.result is not None and st.status in {CheckpointStatus.WAITING_USER, CheckpointStatus.COMPLETED}:
                            # Optionally, mutate content with suggestions if available
                            try:
                                suggestions = st.result.get("suggestions", []) if isinstance(st.result, dict) else []
                                if suggestions:
                                    current_content = self._apply_suggestions(current_content, suggestions)
                            except Exception:
                                pass
                            break
                        await asyncio.sleep(0.25)
                if r:
                    await r.hset(self._rk_flow_meta(flow_id), mapping={
                        "status": "completed",
                        "updated_at": str(time.time()),
                    })
            except Exception as e:
                if r:
                    await r.hset(self._rk_flow_meta(flow_id), mapping={
                        "status": f"failed:{str(e)}",
                        "updated_at": str(time.time()),
                    })

        asyncio.create_task(_runner())
        return flow_id

    async def get_sequence_status(self, flow_id: str) -> Dict[str, Any]:
        r = await self._get_redis()
        checkpoints: List[str] = []
        meta: Dict[str, Any] = {"status": "unknown", "current_step": None}
        if r:
            checkpoints = [c.decode("utf-8") if isinstance(c, (bytes, bytearray)) else c for c in await r.lrange(self._rk_flow(flow_id), 0, -1)]
            raw_meta = await r.hgetall(self._rk_flow_meta(flow_id))
            meta = { (k.decode("utf-8") if isinstance(k, (bytes, bytearray)) else k): (v.decode("utf-8") if isinstance(v, (bytes, bytearray)) else v) for k, v in raw_meta.items() }
        return {
            "flow_id": flow_id,
            "status": meta.get("status", "unknown"),
            "current_step": meta.get("current_step"),
            "checkpoints": checkpoints,
        }

    def _apply_suggestions(self, content: str, suggestions: List[str]) -> str:
        top = suggestions[:3]
        if not top:
            return content
        lines = [content.strip(), "", "Improvements applied:"] + [f"- {s}" for s in top]
        return "\n".join(lines)

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
