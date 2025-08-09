import os
from typing import List, Dict
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
except Exception as e:
    raise SystemExit(f"Failed to import chromadb: {e}")


def ensure_collection(client: "chromadb.HttpClient", name: str):
    try:
        col = client.get_collection(name)
    except Exception:
        col = client.create_collection(name)
    return col


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
        col = ensure_collection(client, name)
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
