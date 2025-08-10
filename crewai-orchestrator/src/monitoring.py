from __future__ import annotations
import time
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from agent_clients import CrewAIAgentClients, AgentHTTPClient


@dataclass
class AgentMetrics:
    calls_total: int = 0
    failures_total: int = 0
    last_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = float("inf")
    sum_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    breaker_state: str = "closed"
    last_error: Optional[str] = None
    updated_at: float = field(default_factory=lambda: time.time())

    def as_dict(self) -> Dict[str, Any]:
        avg = (self.sum_latency_ms / self.calls_total) if self.calls_total else 0.0
        return {
            "calls_total": self.calls_total,
            "failures_total": self.failures_total,
            "last_latency_ms": round(self.last_latency_ms, 2),
            "avg_latency_ms": round(avg, 2),
            "min_latency_ms": (None if self.min_latency_ms == float("inf") else round(self.min_latency_ms, 2)),
            "max_latency_ms": round(self.max_latency_ms, 2),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "breaker_state": self.breaker_state,
            "last_error": self.last_error,
            "updated_at": self.updated_at,
        }


class AgentPerformanceMonitor:
    def __init__(self, clients: CrewAIAgentClients) -> None:
        self.clients = clients
        # initialize lazily to avoid constructor order issues
        self.metrics: Dict[str, AgentMetrics] = {}
        self._latency_windows: Dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    def ensure_initialized(self) -> None:
        if not self.metrics:
            for name in self.clients.agents.keys():
                self.metrics[name] = AgentMetrics()
                self._latency_windows[name] = []

    async def record_call(self, agent_type: str, latency_ms: float, success: bool, error: Optional[str] = None) -> None:
        async with self._lock:
            self.ensure_initialized()
            m = self.metrics[agent_type]
            m.calls_total += 1
            if not success:
                m.failures_total += 1
                m.last_error = error
            m.last_latency_ms = latency_ms
            m.sum_latency_ms += latency_ms
            m.max_latency_ms = max(m.max_latency_ms, latency_ms)
            if latency_ms < m.min_latency_ms:
                m.min_latency_ms = latency_ms
            w = self._latency_windows[agent_type]
            w.append(latency_ms)
            if len(w) > 200:
                w.pop(0)
            # compute p95 on sliding window
            if w:
                sorted_w = sorted(w)
                idx = max(0, int(0.95 * (len(sorted_w) - 1)))
                m.p95_latency_ms = sorted_w[idx]
            # update breaker state snapshot
            m.breaker_state = self.clients.agents[agent_type].circuit_breaker.state.value
            m.updated_at = time.time()

    async def snapshot(self) -> Dict[str, Any]:
        async with self._lock:
            self.ensure_initialized()
            return {agent: m.as_dict() for agent, m in self.metrics.items()}
