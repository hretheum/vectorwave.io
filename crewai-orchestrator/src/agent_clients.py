import httpx
import time
from enum import Enum
from typing import Any, Dict


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
    def __init__(self, agent_type: str, editorial_service_url: str = "http://localhost:8040") -> None:
        self.agent_type = agent_type
        self.editorial_url = editorial_service_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
        self.circuit_breaker = CircuitBreaker()

    async def validate_content(self, content: str, platform: str, validation_mode: str = "comprehensive") -> Dict[str, Any]:
        payload = {
            "content": content,
            "platform": platform,
            "agent_type": self.agent_type,
            "validation_context": {
                "agent": self.agent_type,
                "timestamp": time.time(),
            },
        }

        async def _make_request():
            endpoint = f"{self.editorial_url}/validate/{validation_mode}"
            # Fallback to health if validate endpoint is not implemented
            try:
                resp = await self.client.post(endpoint, json=payload)
            except httpx.HTTPError:
                resp = await self.client.get(f"{self.editorial_url}/health")
            resp.raise_for_status()
            return resp.json()

        return await self.circuit_breaker.call(_make_request)


class CrewAIAgentClients:
    def __init__(self, editorial_service_url: str = "http://localhost:8040") -> None:
        self.agents: Dict[str, AgentHTTPClient] = {
            "research": AgentHTTPClient("research", editorial_service_url),
            "audience": AgentHTTPClient("audience", editorial_service_url),
            "writer": AgentHTTPClient("writer", editorial_service_url),
            "style": AgentHTTPClient("style", editorial_service_url),
            "quality": AgentHTTPClient("quality", editorial_service_url),
        }

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
