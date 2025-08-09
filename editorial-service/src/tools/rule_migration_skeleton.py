import os
from typing import List, Dict
from datetime import datetime

import chromadb
from chromadb.config import Settings

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "style_editorial_rules")


def to_rule_doc(rule_text: str, metadata: Dict) -> Dict:
    # Normalize rule metadata before insertion
    base = {
        "rule_id": metadata.get("rule_id", f"auto_{hash(rule_text) & 0xFFFFFFFF:08x}"),
        "rule_type": metadata.get("rule_type", "style"),
        "severity": metadata.get("severity", "medium"),
        "platform": metadata.get("platform", "universal"),
        "workflow": metadata.get("workflow", "comprehensive"),
        "source": metadata.get("source", "migration"),
        "migrated_at": datetime.utcnow().isoformat(),
    }
    base.update(metadata)
    return base


def migrate_rules(rules: List[Dict]):
    host = os.getenv("CHROMADB_HOST", "chromadb")
    port = int(os.getenv("CHROMADB_PORT", "8000"))

    client = chromadb.HttpClient(host=host, port=port, settings=Settings(allow_reset=True))
    col = client.get_or_create_collection(COLLECTION_NAME)

    docs, metas, ids = [], [], []
    for r in rules:
        text = r["text"]
        md = to_rule_doc(text, r.get("metadata", {}))
        docs.append(text)
        metas.append(md)
        ids.append(md["rule_id"])

    # Batch add in small chunks if needed
    CHUNK = int(os.getenv("BATCH_SIZE", "128"))
    for i in range(0, len(docs), CHUNK):
        sl = slice(i, i + CHUNK)
        col.add(ids=ids[sl], documents=docs[sl], metadatas=metas[sl])
    print(f"Migrated {len(docs)} rules into {COLLECTION_NAME}")


if __name__ == "__main__":
    # Example skeleton input
    sample_rules = [
        {"text": "Use concrete numbers instead of vague terms", "metadata": {"rule_type": "content", "severity": "high"}},
        {"text": "Avoid buzzwords like 'revolutionary'", "metadata": {"rule_type": "style", "severity": "medium"}},
    ]
    migrate_rules(sample_rules)
