from typing import List, Dict, Any


class RawTrendItem(dict):
    """Lightweight alias for normalized trend items (placeholder for Pydantic model)."""


class StorageService:
    def __init__(self, host: str, port: int, collection: str) -> None:
        self._host = host
        self._port = port
        self._collection = collection

    async def save_items(self, items: List[RawTrendItem]) -> int:
        """Placeholder: in Phase 1 just count items; Phase 2 will call ChromaDB."""
        # Later: call Chroma REST to upsert documents with metadata
        return len(items)
