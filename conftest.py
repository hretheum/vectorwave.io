import os
import pytest

# Global skip logic controlled via environment variables
_ENABLE_FULL = os.getenv("ENABLE_FULL_SUITE") == "1"

# Markers we want to skip by default in Phase 2 core profile
_DEFAULT_SKIP_MARKERS = [
    "integration",
    "slow",
    "performance",
    "network",
    "external",
]


def pytest_collection_modifyitems(config, items):
    if _ENABLE_FULL:
        return

    skip_marker = pytest.mark.skip(reason="Skipped by default Phase 2 core profile. Set ENABLE_FULL_SUITE=1 to enable.")
    for item in items:
        for mark in _DEFAULT_SKIP_MARKERS:
            if mark in item.keywords:
                item.add_marker(skip_marker)
                break


def pytest_ignore_collect(path, config):
    """Prevent importing heavy tests in default profile to avoid ImportErrors.

    This runs before test modules are imported, so it avoids dependency errors
    from optional/heavy modules.
    """
    if _ENABLE_FULL:
        return False

    p = str(path)
    # Skip entire heavy test suites by default
    heavy_dirs = [
        os.path.sep + "editorial-service" + os.path.sep + "tests",
        os.path.sep + "topic-manager" + os.path.sep + "tests",
    ]
    for d in heavy_dirs:
        if d in p:
            return True

    # Skip known heavy/require-external tests in ai_writing_flow
    aiwf_tests_root = os.path.sep + "kolegium" + os.path.sep + "ai_writing_flow" + os.path.sep + "tests" + os.path.sep
    if aiwf_tests_root in p:
        # Allowlist minimal core tests only; skip everything else
        allowlist = {
            os.path.join("kolegium", "ai_writing_flow", "tests", "test_writing_crew_integration.py"),
        }
        # Normalize path for comparison
        rel = p[p.find("kolegium"):] if "kolegium" in p else p
        return rel not in allowlist

    # default: don't ignore
    return False
