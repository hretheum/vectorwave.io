import os
import sys
import pytest

# Ensure local src on path for tests run from repo root
_here = os.path.dirname(__file__)
src = os.path.abspath(os.path.join(_here, "..", "src"))
if src not in sys.path:
    sys.path.insert(0, src)


def pytest_collection_modifyitems(config, items):
    """Skip heavy/performance and external-deps tests by default.

    These can be re-enabled via -m "heavy or perf or external" or by
    setting env ENABLE_FULL_SUITE=1.
    """
    full = os.getenv("ENABLE_FULL_SUITE") == "1"
    for item in list(items):
        markers = {m.name for m in item.iter_markers()}
        name = item.name.lower()
        path = str(item.fspath)
        if full:
            continue
        # Skip heavy/perf suites
        if any(k in name for k in ["heavy", "performance", "concurrent_flows"]) or \
           any(k in path for k in ["heavy_load", "concurrent_flows"]):
            item.add_marker(pytest.mark.skip(reason="heavy/perf test skipped by default"))
        # Skip tests needing crewai/aiohttp etc.
        if any(k in path for k in ["enhanced_knowledge_tools", "router_accuracy", "api_endpoints", "knowledge_adapter", "crewai"]):
            item.add_marker(pytest.mark.skip(reason="external deps skipped by default"))
