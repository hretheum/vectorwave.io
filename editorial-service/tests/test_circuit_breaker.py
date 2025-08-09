import asyncio
import time
import pytest

from src.utils.circuit_breaker import CircuitBreaker, CircuitBreakerState


@pytest.mark.asyncio
async def test_circuit_breaker_transitions():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.2)

    calls = {"count": 0}

    async def fail_once():
        calls["count"] += 1
        raise RuntimeError("fail")

    # two failures -> OPEN
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cb.call(fail_once)
    assert cb.state == CircuitBreakerState.OPEN

    # while OPEN and not yet timed out
    with pytest.raises(RuntimeError):
        await cb.call(fail_once)

    # wait to allow HALF_OPEN
    await asyncio.sleep(0.25)
    assert cb._should_attempt_reset() is True

    # half-open trial fails -> back to OPEN
    with pytest.raises(RuntimeError):
        await cb.call(fail_once)
    assert cb.state == CircuitBreakerState.OPEN

    # wait and then succeed
    await asyncio.sleep(0.25)

    async def succeed():
        calls["count"] += 1
        return "ok"

    res = await cb.call(succeed)
    assert res == "ok"
    assert cb.state == CircuitBreakerState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_success_path():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)

    async def work(x):
        return x * 2

    assert await cb.call(work, 5) == 10
    assert cb.state == CircuitBreakerState.CLOSED


def test_circuit_breaker_sync():
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

    def fail():
        raise ValueError("bad")

    with pytest.raises(ValueError):
        cb.call_sync(fail)
    assert cb.state == CircuitBreakerState.OPEN

    time.sleep(0.12)

    def ok():
        return 42

    assert cb.call_sync(ok) == 42
    assert cb.state == CircuitBreakerState.CLOSED
