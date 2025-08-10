"""
Checkpoint-based validation workflow utilities for AI Writing Flow.

Provides a thin orchestration layer over Editorial Service selective validation
with three checkpoints: pre-writing, mid-writing, post-writing.
"""
from __future__ import annotations

from typing import Dict, Any, Optional, List
import asyncio

from .clients.editorial_client import EditorialServiceClient


class ValidationCheckpoints:
    """Run selective validation at predefined checkpoints.

    This utility does not persist state; it focuses on invoking Editorial Service
    with correct checkpoint literals and aggregating responses.
    """

    def __init__(self, client: Optional[EditorialServiceClient] = None, base_url: Optional[str] = None):
        self.client = client or EditorialServiceClient(base_url=base_url, timeout=30.0)

    async def validate_checkpoint(self, content: str, platform: str, checkpoint: str) -> Dict[str, Any]:
        """Validate content at a specific checkpoint.

        Args:
            content: Draft content string
            platform: Target platform literal (e.g., "linkedin")
            checkpoint: One of "pre-writing", "mid-writing", "post-writing"
        """
        if checkpoint not in ("pre-writing", "mid-writing", "post-writing"):
            raise ValueError(f"Unknown checkpoint: {checkpoint}")

        result = await self.client.validate_selective(
            content=content,
            platform=platform,
            checkpoint=checkpoint,
            context={"agent": "validation_checkpoints"},
        )
        # Normalize minimal shape we expect downstream
        return {
            "checkpoint": checkpoint,
            "rule_count": result.get("rule_count") or len(result.get("rules_applied", [])) or result.get("rules_applied", 0),
            "passed": result.get("passed", (len(result.get("violations", [])) == 0)),
            "raw": result,
        }

    async def validate_all(self, content: str, platform: str) -> List[Dict[str, Any]]:
        """Run all three checkpoints in sequence."""
        out: List[Dict[str, Any]] = []
        for cp in ("pre-writing", "mid-writing", "post-writing"):
            out.append(await self.validate_checkpoint(content, platform, cp))
        return out

    def validate_all_sync(self, content: str, platform: str) -> List[Dict[str, Any]]:
        """Synchronous wrapper for convenience in non-async contexts."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Fallback to threaded run if loop active
                return asyncio.run(self.validate_all(content, platform))
            return loop.run_until_complete(self.validate_all(content, platform))
        except RuntimeError:
            # No loop
            return asyncio.run(self.validate_all(content, platform))
