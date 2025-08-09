import os
from typing import List, Dict, Optional
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
except Exception as e:
    raise SystemExit(f"Failed to import chromadb: {e}")


SCHEMA_METADATA: Dict[str, Dict] = {
    "style_editorial_rules": {
        "schema_version": "1.0",
        "description": "Editorial/style rules used for comprehensive validation",
        "fields": ["rule_type", "severity", "platform", "workflow", "source", "migrated_at"],
    },
    "publication_platform_rules": {
        "schema_version": "1.0",
        "description": "Platform-specific constraints and optimizations",
        "fields": ["platform", "constraint_type", "severity", "source", "migrated_at"],
    },
    "topics": {
        "schema_version": "1.0",
        "description": "Topic graph for discovery and suggestion",
        "fields": ["title", "keywords", "score", "source", "scraped_at"],
    },
    "scheduling_optimization": {
        "schema_version": "1.0",
        "description": "Timing intelligence for platform scheduling",
        "fields": ["platform", "slot", "score", "timezone", "observed_at"],
    },
    "user_preferences": {
        "schema_version": "1.0",
        "description": "Learned user preferences for personalization",
        "fields": ["user_id", "preference_key", "value", "updated_at"],
    },
}


def ensure_collection(client: "chromadb.HttpClient", name: str, force_recreate: bool = False):
    metadata = SCHEMA_METADATA.get(name, {"schema_version": "1.0"})
    if force_recreate:
        try:
            client.delete_collection(name)
        except Exception:
            pass
        return client.create_collection(name, metadata=metadata)
    # Try get-or-create with metadata
    try:
        return client.get_or_create_collection(name=name, metadata=metadata)
    except Exception:
        # Fallback: try get; else create
        try:
            return client.get_collection(name)
        except Exception:
            return client.create_collection(name, metadata=metadata)


def add_sample(col, doc_id: str, text: str, metadata: Dict):
    try:
        # If already present, do nothing
        existing = False
        try:
            # v0.4 HttpClient collections have get() optional
            res = col.get(ids=[doc_id])
            if res and res.get("ids"):
                existing = True
        except Exception:
            pass
        if existing:
            return
        col.add(ids=[doc_id], documents=[text], metadatas=[metadata])
    except Exception as e:
        print(f"Warning: failed to add sample doc to {col.name}: {e}")


def main():
    host = os.getenv("CHROMADB_HOST", "chromadb")
    port = int(os.getenv("CHROMADB_PORT", "8000"))
    collection = os.getenv("COLLECTION_NAME")
    force = os.getenv("FORCE_RECREATE", "0") == "1"

    client = chromadb.HttpClient(host=host, port=port, settings=Settings(allow_reset=True))

    if collection:
        targets: List[str] = [collection]
    else:
        targets = [
            "style_editorial_rules",
            "publication_platform_rules",
            "topics",
            "scheduling_optimization",
            "user_preferences",
        ]

    for name in targets:
        col = ensure_collection(client, name, force_recreate=force)
        add_sample(
            col,
            doc_id=f"sample_{name}",
            text=f"Sample document for {name}",
            metadata={
                "created_at": datetime.utcnow().isoformat(),
                "source": "init_script",
                "collection": name,
            },
        )
        print(f"✅ Ensured collection '{name}' with a sample document")


if __name__ == "__main__":
    main()
