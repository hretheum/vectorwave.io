import os
import httpx
import asyncio
from typing import Any, Dict


class AIWritingFlowClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("AI_WRITING_FLOW_URL", "http://localhost:8044")).rstrip("/")
        connect = float(os.getenv("AIWF_CONNECT_TIMEOUT", "5.0"))
        read = float(os.getenv("AIWF_READ_TIMEOUT", "10.0"))
        write = float(os.getenv("AIWF_WRITE_TIMEOUT", "5.0"))
        pool = float(os.getenv("AIWF_POOL_TIMEOUT", "5.0"))
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(connect=connect, read=read, write=write, pool=pool))
        self.retry_max = int(os.getenv("AIWF_RETRY_MAX_ATTEMPTS", "3"))
        self.retry_initial = float(os.getenv("AIWF_RETRY_INITIAL_DELAY", "0.2"))
        self.retry_backoff = float(os.getenv("AIWF_RETRY_BACKOFF", "2.0"))
        self.retry_max_delay = float(os.getenv("AIWF_RETRY_MAX_DELAY", "2.0"))

    async def health(self) -> Dict[str, Any]:
        return await self._with_retries(lambda: self.client.get(f"{self.base_url}/health"))

    async def generate_multi_platform(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Health gate: ensure upstream is healthy before posting
        try:
            health = await self.health()
            if not isinstance(health, dict) or health.get("status") != "healthy":
                raise httpx.HTTPStatusError("AI Writing Flow unhealthy", request=None, response=None)  # type: ignore[arg-type]
        except Exception as e:
            raise e
        return await self._with_retries(lambda: self.client.post(f"{self.base_url}/v2/generate/multi-platform", json=payload))

    async def _with_retries(self, call):
        delay = self.retry_initial
        attempt = 1
        last_exc = None
        while attempt <= self.retry_max:
            try:
                resp = await call()
                resp.raise_for_status()
                return resp.json()
            except Exception as e:  # noqa: BLE001
                last_exc = e
                retryable = isinstance(e, (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError))
                if not retryable or attempt == self.retry_max:
                    break
                await asyncio.sleep(delay)
                delay = min(self.retry_max_delay, delay * self.retry_backoff)
                attempt += 1
        assert last_exc is not None
        raise last_exc


