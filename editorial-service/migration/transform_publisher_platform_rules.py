#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

CATALOG_PATH_DEFAULT = os.path.abspath(os.path.join(os.path.dirname(__file__), "output", "publisher_platform_rules_catalog.json"))
OUTPUT_DEFAULT = os.path.abspath(os.path.join(os.path.dirname(__file__), "output", "publisher_platform_chromadb_rules.json"))

ALLOWED_RULE_TYPES = {"style", "structure", "quality", "editorial", "grammar", "tone", "engagement"}
ALLOWED_PLATFORMS = {"universal", "linkedin", "twitter", "substack", "beehiiv", "ghost", "youtube"}
ALLOWED_PRIORITIES = {"critical", "high", "medium", "low"}
ALLOWED_WORKFLOWS = {"comprehensive", "selective", "both"}
ALLOWED_ACTIONS = {"forbid", "require", "suggest", "optimize"}

CATEGORY_TO_ACTION = {
    "forbidden_phrases": "forbid",
    "required_elements": "require",
    "regex_pattern": "optimize",
    "max_length": "require",
    "character_limit": "require",
    "hashtag_rules": "optimize",
    "platform_specific": "suggest",
}

CATEGORY_TO_RULETYPE = {
    "forbidden_phrases": "style",
    "required_elements": "editorial",
    "regex_pattern": "style",
    "max_length": "structure",
    "character_limit": "structure",
    "hashtag_rules": "engagement",
    "platform_specific": "editorial",
}

PRIORITY_BY_CATEGORY = {
    "max_length": "critical",
    "character_limit": "critical",
    "forbidden_phrases": "high",
    "required_elements": "high",
    "regex_pattern": "medium",
    "hashtag_rules": "medium",
    "platform_specific": "low",
}


def hash_id(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def clean_text(text: str) -> str:
    t = text.strip()
    t = re.sub(r"\s+", " ", t)
    return t


def score_quality(text: str) -> float:
    score = 0.6
    n = len(text)
    if 40 <= n <= 200:
        score += 0.2
    if re.search(r"\b(must|never|require|limit|max)\b", text, re.IGNORECASE):
        score += 0.15
    return max(0.0, min(1.0, round(score, 2)))


def build_content(hit: Dict[str, Any]) -> str:
    cat = hit.get("type")
    platform = hit.get("platform", "universal")
    values = hit.get("values", {})
    nums = values.get("numbers", []) if isinstance(values, dict) else []
    strings = values.get("strings", []) if isinstance(values, dict) else []

    if cat in ("max_length", "character_limit"):
        limit = nums[0] if nums else None
        if limit:
            return f"{platform.title()} content must not exceed {limit} characters"
        return f"{platform.title()} content must respect the platform character limit"
    if cat == "hashtag_rules":
        count = nums[0] if nums else None
        if count:
            return f"Use no more than {count} hashtags on {platform.title()}"
        return f"Use platform-appropriate number of hashtags on {platform.title()}"
    if cat == "forbidden_phrases":
        phrase = strings[0] if strings else None
        if phrase:
            return f"Avoid using the phrase: '{phrase}' on {platform.title()}"
        return f"Avoid platform-forbidden phrases on {platform.title()}"
    if cat == "required_elements":
        elem = strings[0] if strings else None
        if elem:
            return f"Ensure to include required element on {platform.title()}: '{elem}'"
        return f"Ensure platform-required elements are included on {platform.title()}"
    if cat == "regex_pattern":
        pat = strings[0] if strings else None
        if pat:
            return f"Follow platform style pattern on {platform.title()}: '{pat}'"
        return f"Follow platform style patterns on {platform.title()}"
    # platform_specific fallback
    return f"Ensure content follows {platform.title()} platform-specific rules"


def transform_catalog(catalog: Dict[str, Any]) -> List[Dict[str, Any]]:
    documents: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str]] = set()  # (platform, content_norm)

    for f in catalog.get("files", []):
        fpath = f.get("file")
        for h in f.get("hits", []):
            platform = h.get("platform", "universal").lower()
            if platform not in ALLOWED_PLATFORMS:
                platform = "universal"
            content = build_content(h)
            content_norm = clean_text(content).lower()
            key = (platform, content_norm)
            if len(content_norm) < 12 or key in seen:
                continue
            seen.add(key)

            cat = h.get("type")
            rule_type = CATEGORY_TO_RULETYPE.get(cat, "editorial")
            rule_action = CATEGORY_TO_ACTION.get(cat, "suggest")
            priority = PRIORITY_BY_CATEGORY.get(cat, "low")

            rid = f"pub_{platform}_{cat}_{hash_id(content)}"
            metadata: Dict[str, Any] = {
                "rule_id": rid,
                "rule_type": rule_type if rule_type in ALLOWED_RULE_TYPES else "editorial",
                "platform": platform,
                "platform_specific": platform != "universal",
                "workflow": "both",
                "priority": priority if priority in ALLOWED_PRIORITIES else "low",
                "checkpoint": None,
                "rule_action": rule_action,
                "confidence_threshold": 0.7 if priority in {"critical", "high"} else 0.6,
                "auto_fix": rule_action in {"suggest", "optimize"},
                "applies_to": ["thought_leadership", "industry_update", "tutorial"],
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "source": "publisher_migration",
                "migrated_from": fpath,
                "version": 1,
                "usage_count": 0,
                "success_rate": 0.0,
                "related_rules": [],
                "conflicts_with": [],
                "supersedes": [],
                "quality_score": score_quality(content),
                "platform_constraints": h.get("values", {}),
                "discovery": {
                    "type": h.get("type"),
                    "line": h.get("line"),
                },
            }

            documents.append({
                "content": content,
                "metadata": metadata,
            })

    documents.sort(key=lambda d: (d["metadata"]["platform"], d["metadata"]["rule_id"]))
    return documents


def main():
    parser = argparse.ArgumentParser(description="Transform Publisher Platform discovered rules to ChromaDB format")
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
