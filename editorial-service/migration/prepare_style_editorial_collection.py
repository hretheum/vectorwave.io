#!/usr/bin/env python3
import os
import sys
import json
import time
from typing import Dict, Any

import chromadb
from chromadb.config import Settings

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "style_editorial_rules")
CHROMA_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMADB_PORT", "8000"))

SCHEMA_METADATA = {
    "schema_version": 1,
    "description": "Content style and editorial validation rules",
    "hints": [
        "metadata.rule_id unique",
        "filterable: platform, rule_type, workflow, priority, checkpoint",
        "embedding: all-MiniLM-L6-v2"
    ],
}


def ensure_collection(client) -> Dict[str, Any]:
    try:
        col = client.get_collection(COLLECTION_NAME)
        # Optional: reset to empty for fresh import
        try:
            col.delete(where={})
        except Exception:
            pass
    except Exception:
        col = client.create_collection(COLLECTION_NAME, metadata=SCHEMA_METADATA)
    # Ensure metadata present
    try:
        col.modify(metadata=SCHEMA_METADATA)
    except Exception:
        pass
    return {"name": COLLECTION_NAME, "metadata": SCHEMA_METADATA}


def main():
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT, settings=Settings(allow_reset=True))
    info = ensure_collection(client)

    # Simple health check: list collections
    cols = [c.name for c in client.list_collections()]

    print(json.dumps({
        "status": "ok",
        "prepared_collection": info["name"],
        "metadata": info["metadata"],
        "collections": cols
    }))


if __name__ == "__main__":
    main()
