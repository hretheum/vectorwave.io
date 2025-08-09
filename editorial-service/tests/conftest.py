import os
import sys
import inspect
import asyncio
from pathlib import Path
import pytest

# Note: do not declare pytest_plugins here to avoid deprecation warning

# Ensure /app and /app/src are available during pytest collection (docker image)
app_path = Path('/app')
src_path = app_path / 'src'
for p in (str(app_path), str(src_path)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Also support local runs
repo_root = Path(__file__).resolve().parents[1]
local_src = repo_root / 'src'
if local_src.exists():
    p = str(local_src)
    if p not in sys.path:
        sys.path.insert(0, p)


def pytest_collection_modifyitems(items):
    """Automatically mark async test functions to run with pytest-asyncio.

    This prevents 'async def functions are not natively supported' errors
    when tests forget to add @pytest.mark.asyncio and relies on
    asyncio_mode configured in pytest.ini.
    """
    for item in items:
        test_obj = getattr(item, "obj", None)
        if test_obj is None:
            continue
        func = test_obj
        # For class-based tests, item.obj is the function
        if inspect.iscoroutinefunction(func):
            item.add_marker(pytest.mark.asyncio)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session to avoid
    cross-loop issues with class-scoped async fixtures/clients."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
