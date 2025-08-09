from __future__ import annotations
import asyncio
import time
from enum import Enum
from typing import Any, Awaitable, Callable, Optional, Type


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """
    Async circuit breaker utility.

    - CLOSED: calls pass through
    - OPEN: calls short-circuit until timeout elapses
    - HALF_OPEN: allow a single trial; if success -> CLOSED, if failure -> OPEN
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[BaseException] = Exception,
    ) -> None:
        if failure_threshold <= 0:
            raise ValueError("failure_threshold must be > 0")
        if recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be > 0")

        self.failure_threshold: int = failure_threshold
        self.recovery_timeout: float = recovery_timeout
        self.expected_exception: Type[BaseException] = expected_exception

        self.failure_count: int = 0
        self.last_failure_time: Optional[float] = None
        self.state: CircuitBreakerState = CircuitBreakerState.CLOSED
        self._half_open_lock = asyncio.Lock()

    async def call(self, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any) -> Any:
        """Execute an awaitable under circuit breaker protection."""
        if self.state == CircuitBreakerState.OPEN:
            # Check if we should transition to HALF_OPEN
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise RuntimeError("Circuit breaker is OPEN")

        if self.state == CircuitBreakerState.HALF_OPEN:
            # Ensure only one trial call proceeds at a time
            async with self._half_open_lock:
                if self.state != CircuitBreakerState.HALF_OPEN:
                    # state changed while waiting
                    return await self.call(func, *args, **kwargs)
                try:
                    result = await func(*args, **kwargs)
                    self._on_success()
                    return result
                except self.expected_exception as e:
                    self._on_failure()
                    raise e

        # CLOSED
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.recovery_timeout

    def _on_success(self) -> None:
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def _on_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN

    # Synchronous helper for sync callables
    def call_sync(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise RuntimeError("Circuit breaker is OPEN")
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
