#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

CATALOG_PATH_DEFAULT = os.path.abspath(os.path.join(os.path.dirname(__file__), "output", "ai_writing_flow_rules_catalog.json"))
OUTPUT_DEFAULT = os.path.abspath(os.path.join(os.path.dirname(__file__), "output", "ai_writing_flow_chromadb_rules.json"))

ALLOWED_RULE_TYPES = {"style", "structure", "quality", "editorial", "grammar", "tone", "engagement"}
ALLOWED_PLATFORMS = {"universal", "linkedin", "twitter", "substack", "beehiiv", "ghost", "youtube"}
ALLOWED_PRIORITIES = {"critical", "high", "medium", "low"}
ALLOWED_WORKFLOWS = {"comprehensive", "selective", "both"}
ALLOWED_ACTIONS = {"forbid", "require", "suggest", "optimize"}

# Heuristics
def hash_id(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def clean_text(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^#\s*", "", t)  # strip python comments
    t = re.sub(r'^"{3}|"{3}$|^\'{3}|\'{3}$', "", t)  # strip triple quotes markers if captured
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def score_quality(text: str) -> float:
    score = 0.5
    n = len(text)
    if 40 <= n <= 240:
        score += 0.2
    if re.search(r"\b(must|never|forbid|require)\b", text, re.IGNORECASE):
        score += 0.2
    if re.search(r"\b(examples?|e\.g\.|i\.e\.)\b", text, re.IGNORECASE):
        score += 0.05
    return max(0.0, min(1.0, round(score, 2)))


CATEGORY_TO_ACTION = {
    "forbidden": "forbid",
    "required": "require",
    "pattern": "optimize",
    "directive_line": "suggest",
}

CATEGORY_TO_RULETYPE = {
    "forbidden": "style",
    "required": "editorial",
    "pattern": "style",
    "directive_line": "style",
}

PRIORITY_NORMALIZE = {"high", "medium", "low", "critical"}


def build_rule_content(category: str, base_text: str, value: Optional[str]) -> str:
    if category == "forbidden" and value:
        return f"Avoid using the phrase: '{value}'"
    if category == "required" and value:
        return f"Ensure to include required element: '{value}'"
    if category == "pattern" and value:
        return f"Follow the style pattern: '{value}' where applicable"
    # directive or fallback
    cleaned = clean_text(base_text)
    return cleaned


def transform_catalog(catalog: Dict[str, Any]) -> List[Dict[str, Any]]:
    documents: List[Dict[str, Any]] = []
    seen_contents = set()

    files = catalog.get("files", [])
    for f in files:
        fpath = f.get("file")
        hits = f.get("hits", [])
        for h in hits:
            category_guess = h.get("category_guess") or h.get("type") or "directive_line"
            category = category_guess
            base_snippet = h.get("snippet", "")
            values = h.get("values_preview", []) or [None]

            for v in values:
                content = build_rule_content(category, base_snippet, v)
                content_norm = content.lower().strip()
                if len(content_norm) < 12:
                    continue
                if content_norm in seen_contents:
                    continue
                seen_contents.add(content_norm)

                rule_type = CATEGORY_TO_RULETYPE.get(category, "style")
                rule_action = CATEGORY_TO_ACTION.get(category, "suggest")
                priority_guess = (h.get("priority_guess") or "low").lower()
                priority = priority_guess if priority_guess in PRIORITY_NORMALIZE else "low"

                rid = f"aiwf_{category}_{hash_id(content)}"

                metadata: Dict[str, Any] = {
                    "rule_id": rid,
                    "rule_type": rule_type if rule_type in ALLOWED_RULE_TYPES else "style",
                    "platform": "universal",
                    "platform_specific": False,
                    "workflow": "both",
                    "priority": priority,
                    "checkpoint": None,
                    "rule_action": rule_action,
                    "confidence_threshold": 0.7 if priority in {"critical", "high"} else 0.6,
                    "auto_fix": rule_action in {"suggest", "optimize"},
                    "applies_to": ["thought_leadership", "industry_update", "tutorial"],
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "updated_at": datetime.utcnow().isoformat() + "Z",
                    "source": "ai_writing_flow_migration",
                    "migrated_from": fpath,
                    "version": 1,
                    "usage_count": 0,
                    "success_rate": 0.0,
                    "related_rules": [],
                    "conflicts_with": [],
                    "supersedes": [],
                    "quality_score": score_quality(content),
                    "discovery": {
                        "type": h.get("type"),
                        "start_line": h.get("start_line"),
                        "end_line": h.get("end_line"),
                    },
                }

                documents.append({
                    "content": content,
                    "metadata": metadata,
                })

    # sort deterministic
    documents.sort(key=lambda d: d["metadata"]["rule_id"])
    return documents


def main():
    parser = argparse.ArgumentParser(description="Transform AI Writing Flow discovered rules to ChromaDB format")
    parser.add_argument("--catalog", default=CATALOG_PATH_DEFAULT)
    parser.add_argument("--output", default=OUTPUT_DEFAULT)
    args = parser.parse_args()

    with open(args.catalog, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    docs = transform_catalog(catalog)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

    print(json.dumps({"status": "ok", "output": args.output, "count": len(docs)}))


if __name__ == "__main__":
    main()
