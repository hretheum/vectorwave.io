#!/usr/bin/env python3
import argparse
import json
import os
from typing import Dict, List, Tuple

ALLOWED_RULE_TYPES = {"style", "structure", "quality", "editorial", "grammar", "tone", "engagement"}
ALLOWED_PLATFORMS = {"universal", "linkedin", "twitter", "substack", "beehiiv", "ghost", "youtube"}
ALLOWED_PRIORITIES = {"critical", "high", "medium", "low"}
ALLOWED_WORKFLOWS = {"comprehensive", "selective", "both"}
ALLOWED_ACTIONS = {"forbid", "require", "suggest", "optimize"}
ALLOWED_CHECKPOINTS = {None, "pre_writing", "mid_writing", "post_writing"}
REQUIRED_METADATA_FIELDS = [
    "rule_id", "rule_type", "platform", "workflow", "priority", "rule_action", "created_at", "source"
]


def load_rules(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_format(rules: List[Dict]) -> Tuple[int, List[str]]:
    errors: List[str] = []
    for idx, r in enumerate(rules):
        if "content" not in r or not isinstance(r["content"], str) or len(r["content"].strip()) < 5:
            errors.append(f"[{idx}] invalid content")
            continue
        md = r.get("metadata", {})
        for field in REQUIRED_METADATA_FIELDS:
            if field not in md:
                errors.append(f"[{idx}] missing metadata.{field}")
        if md.get("rule_type") not in ALLOWED_RULE_TYPES:
            errors.append(f"[{idx}] invalid rule_type: {md.get('rule_type')}")
        if md.get("platform") not in ALLOWED_PLATFORMS:
            errors.append(f"[{idx}] invalid platform: {md.get('platform')}")
        if md.get("workflow") not in ALLOWED_WORKFLOWS:
            errors.append(f"[{idx}] invalid workflow: {md.get('workflow')}")
        if md.get("priority") not in ALLOWED_PRIORITIES:
            errors.append(f"[{idx}] invalid priority: {md.get('priority')}")
        if md.get("rule_action") not in ALLOWED_ACTIONS:
            errors.append(f"[{idx}] invalid rule_action: {md.get('rule_action')}")
        if md.get("checkpoint") not in ALLOWED_CHECKPOINTS:
            errors.append(f"[{idx}] invalid checkpoint: {md.get('checkpoint')}")
    return (len(errors), errors)


def check_duplicates(rules: List[Dict]) -> Tuple[int, List[str]]:
    seen_content = {}
    dups = []
    for idx, r in enumerate(rules):
        key = r["content"].strip().lower()
        if key in seen_content:
            dups.append(f"duplicate content at {idx} and {seen_content[key]}")
        else:
            seen_content[key] = idx
    return (len(dups), dups)


def main():
    parser = argparse.ArgumentParser(description="Validate AI Writing Flow transformed rules JSON")
    parser.add_argument("--path", default=os.path.abspath(os.path.join(os.path.dirname(__file__), "output", "ai_writing_flow_chromadb_rules.json")))
    parser.add_argument("--check-format", action="store_true")
    parser.add_argument("--check-duplicates", action="store_true")
    args = parser.parse_args()

    rules = load_rules(args.path)

    result = {"path": args.path}

    if args.check_format:
        cnt, errors = validate_format(rules)
        result["validation_errors"] = cnt
        result["errors"] = errors[:50]
    if args.check_duplicates:
        cnt, dups = check_duplicates(rules)
        result["duplicate_count"] = cnt
        result["duplicates"] = dups[:50]

    print(json.dumps(result))


if __name__ == "__main__":
    main()
