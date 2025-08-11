from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx


class EmbeddingProvider:
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:  # pragma: no cover - interface
        raise NotImplementedError


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        # Allow Azure/OpenAI-compatible endpoints
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY missing")
        if not texts:
            return []
        payload: Dict[str, Any] = {"input": texts, "model": self.model}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        url = f"{self.base_url}/embeddings"
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            # data["data"] is a list with objects containing "embedding"
            return [item["embedding"] for item in (data.get("data") or [])]


def resolve_provider() -> Optional[EmbeddingProvider]:
    provider = (os.getenv("EMBEDDINGS_PROVIDER") or "").lower().strip()
    if provider in ("openai", ""):
        # Default to OpenAI when key is present, otherwise None
        if os.getenv("OPENAI_API_KEY"):
            return OpenAIEmbeddingProvider()
        return None
    # Extendable: voyage, cohere, etc.
    return None
