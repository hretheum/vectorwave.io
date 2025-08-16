"""
Deprecated module: styleguide_loader

This module previously contained hardcoded styleguide rules. The system has
migrated to a ChromaDB-centric Editorial Service. All style validation now
goes through HTTP endpoints exposed by Editorial Service. This file is kept
as a thin shim to avoid import errors; its functions are no-ops or minimal
defaults and will be removed in a future release.
"""

from typing import Dict, Any


def load_styleguide_context() -> Dict[str, Any]:
    """Return minimal context. Do not use hardcoded rules."""
    return {"source": "deprecated", "note": "Use Editorial Service instead"}


def get_platform_constraints(platform: str) -> Dict[str, Any]:
    """Return empty constraints; callers should not rely on this anymore."""
    return {}


def validate_against_styleguide(content: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Return a neutral validation result; real validation is externalized."""
    return {"valid": True, "issues": [], "score": 100}