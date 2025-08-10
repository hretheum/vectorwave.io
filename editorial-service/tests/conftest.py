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
# Ensure the repository root is on sys.path so that 'import src.*' works
root_str = str(repot_root) if 'repot_root' in globals() else str(repo_root)
if root_str not in sys.path:
    sys.path.insert(0, root_str)


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


def pytest_configure(config):
    # Register custom markers to silence warnings
    config.addinivalue_line("markers", "e2e: end-to-end tests")
    config.addinivalue_line("markers", "slow: slow tests")
    config.addinivalue_line("markers", "compatibility: compatibility tests")


def pytest_collection_modifyitems(config, items):
    """Skip docker-dependent integration by default unless explicitly enabled."""
    enable_full = os.getenv("ENABLE_FULL_SUITE") == "1"
    if enable_full:
        return
    for item in list(items):
        p = str(item.fspath)
        if any(s in p for s in ["integration/test_service_integration.py"]):
            item.add_marker(pytest.mark.skip(reason="docker-dependent test skipped by default"))


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session to avoid
    cross-loop issues with class-scoped async fixtures/clients."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
