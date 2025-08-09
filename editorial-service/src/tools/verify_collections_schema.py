import os
from typing import Dict, List

import chromadb
from chromadb.config import Settings

TARGETS = [
    "style_editorial_rules",
    "publication_platform_rules",
    "topics",
    "scheduling_optimization",
    "user_preferences",
]

REQUIRED_META_KEYS = ["schema_version", "description", "hints"]

# Recommended hints to guide operational indexing/queries (documentation-level)
RECOMMENDED_HINTS: Dict[str, List[str]] = {
    "style_editorial_rules": ["rule_type", "severity", "platform", "workflow"],
    "publication_platform_rules": ["platform", "constraint_type", "severity"],
    "topics": ["title", "keywords", "score"],
    "scheduling_optimization": ["platform", "slot", "timezone"],
    "user_preferences": ["user_id", "preference_key"],
}


def main() -> int:
    host = os.getenv("CHROMADB_HOST", "chromadb")
    port = int(os.getenv("CHROMADB_PORT", "8000"))

    client = chromadb.HttpClient(host=host, port=port, settings=Settings(allow_reset=True))
    ok = True

    for name in TARGETS:
        col = client.get_or_create_collection(name)
        meta = col.metadata or {}
        # auto-fill missing suggested keys for dev convenience
        changed = False
        if "schema_version" not in meta:
            meta["schema_version"] = "1.0"
            changed = True
        if "description" not in meta:
            meta["description"] = f"Collection {name}"
            changed = True
        if "hints" not in meta:
            # Chroma v0.4.x expects simple types in metadata; store as comma-separated string
            meta["hints"] = ",".join(RECOMMENDED_HINTS.get(name, []))
            changed = True
        # store back if changed
        if changed:
            try:
                client.delete_collection(name)
            except Exception:
                pass
            col = client.create_collection(name, metadata=meta)
        # Verification output
        missing = [k for k in REQUIRED_META_KEYS if k not in col.metadata]
        print(f"{name}: metadata={col.metadata}")
        if missing:
            ok = False
            print(f"MISSING: {missing}")
    if not ok:
        print("FAIL: Some collections missing required metadata keys")
        return 1
    print("OK: All collections carry recommended metadata skeleton")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
