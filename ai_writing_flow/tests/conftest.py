import os
import pytest

# Phase 2 core profile: skip heavy AIWF tests unless explicitly enabled
_ENABLE_FULL = os.getenv("ENABLE_FULL_SUITE") == "1"

_SKIP_BY_DEFAULT = [
    "integration",
    "slow",
    "performance",
    "network",
    "external",
]

def pytest_collection_modifyitems(config, items):
    if _ENABLE_FULL:
        return
    skip_marker = pytest.mark.skip(reason="Phase 2 core profile: ENABLE_FULL_SUITE=1 to run heavy tests")
    for item in items:
        for k in _SKIP_BY_DEFAULT:
            if k in item.keywords:
                item.add_marker(skip_marker)
                break
