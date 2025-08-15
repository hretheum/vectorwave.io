import httpx
import time
import os
from enum import Enum
from typing import Any, Dict, Optional


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.state = CircuitBreakerState.CLOSED

    def _should_attempt_reset(self) -> bool:
        return self.last_failure_time is None or (time.time() - self.last_failure_time) >= self.recovery_timeout

    async def call(self, func, *args, **kwargs):
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise RuntimeError("Circuit breaker OPEN - Editorial Service unavailable")
        try:
            result = await func(*args, **kwargs)
            self.failure_count = 0
            self.state = CircuitBreakerState.CLOSED
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
            raise e


class AgentHTTPClient:
    def __init__(self, agent_type: str, editorial_service_url: str = "http://localhost:8040", monitor=None) -> None:
        self.agent_type = agent_type
        self.editorial_url = editorial_service_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
        self.circuit_breaker = CircuitBreaker()
        self._supports_validation: Optional[bool] = None
        self._monitor = monitor

    async def validate_content(self, content: str, platform: str, validation_mode: str = "comprehensive") -> Dict[str, Any]:
        # Ensure Editorial Service exposes validation endpoints
        await self._ensure_validation_supported()

        # Build payload compatible with Editorial Service ValidationRequest
        payload = {
            "content": content,
            "mode": validation_mode,
        }
        if validation_mode == "selective":
            payload["checkpoint"] = self._checkpoint_for_agent()
        # Propagate platform context when provided (Editorial Service supports optional platform)
        if isinstance(platform, str) and platform.strip():
            payload["platform"] = platform.strip()

        async def _make_request():
            endpoint = f"{self.editorial_url}/validate/{validation_mode}"
            start = time.time()
            resp = await self.client.post(endpoint, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if self._monitor:
                await self._monitor.record_call(self.agent_type, (time.time() - start) * 1000, success=True)
            return data

        try:
            return await self.circuit_breaker.call(_make_request)
        except Exception as e:
            if self._monitor:
                await self._monitor.record_call(self.agent_type, 0.0, success=False, error=str(e))
            raise

    async def _ensure_validation_supported(self) -> None:
        if self._supports_validation is not None:
            if not self._supports_validation:
                raise RuntimeError("Editorial Service does not expose /validate endpoints")
            return
        try:
            r = await self.client.get(f"{self.editorial_url}/openapi.json")
            if r.status_code != 200:
                self._supports_validation = False
                raise RuntimeError("Editorial Service OpenAPI unavailable; cannot locate validation endpoints")
            spec = r.json()
            paths = spec.get("paths", {})
            self._supports_validation = "/validate/selective" in paths and "/validate/comprehensive" in paths
            if not self._supports_validation:
                raise RuntimeError("Editorial Service missing /validate endpoints (selective/comprehensive)")
        except Exception:
            self._supports_validation = False
            raise

    def _checkpoint_for_agent(self) -> str:
        mapping = {
            "research": "pre-writing",
            "audience": "pre-writing",
            "writer": "mid-writing",
            "style": "mid-writing",
            "quality": "post-writing",
        }
        return mapping.get(self.agent_type, "mid-writing")


class CrewAIAgentClients:
    def __init__(self, editorial_service_url: str = "http://localhost:8040") -> None:
        # Build agents first
        self.agents: Dict[str, AgentHTTPClient] = {
            "research": AgentHTTPClient("research", editorial_service_url, None),
            "audience": AgentHTTPClient("audience", editorial_service_url, None),
            "writer": AgentHTTPClient("writer", editorial_service_url, None),
            "style": AgentHTTPClient("style", editorial_service_url, None),
            "quality": AgentHTTPClient("quality", editorial_service_url, None),
        }
        # Then create monitor (needs agents list) and attach to each client
        from monitoring import AgentPerformanceMonitor  # type: ignore
        self.monitor = AgentPerformanceMonitor(self)
        for client in self.agents.values():
            client._monitor = self.monitor

    def get_agent(self, agent_type: str) -> AgentHTTPClient:
        if agent_type not in self.agents:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return self.agents[agent_type]

    def cb_status(self) -> Dict[str, Any]:
        status: Dict[str, Any] = {}
        for a_type, client in self.agents.items():
            status[a_type] = {
                "state": client.circuit_breaker.state.value,
                "failure_count": client.circuit_breaker.failure_count,
                "last_failure_time": client.circuit_breaker.last_failure_time,
            }
        return status

    async def perf_metrics(self) -> Dict[str, Any]:
        return await self.monitor.snapshot()
