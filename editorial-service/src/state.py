"""Application state dataclass for FastAPI service."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AppState:
    """Container for application wide state."""

    redis_client: Optional[Any] = None
    startup_time: Optional[float] = None
    health_checks: Dict[str, Any] = field(default_factory=dict)
    chromadb_client: Optional[Any] = None
    health_response_cache: Optional[Dict[str, Any]] = None
    health_cache_refresh_inflight: bool = False
    checkpoints: Dict[str, Any] = field(default_factory=dict)

