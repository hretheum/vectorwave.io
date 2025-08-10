#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Set, Tuple

STYLEGUIDES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "styleguides"))
OUTPUT_DEFAULT = os.path.abspath(os.path.join(os.path.dirname(__file__), "output", "chromadb_rules.json"))

# Enumerations aligned with target-version/CHROMADB_SCHEMA_SPECIFICATION.md
ALLOWED_RULE_TYPES = {"style", "structure", "quality", "editorial", "grammar", "tone", "engagement"}
ALLOWED_PLATFORMS = {"universal", "linkedin", "twitter", "substack", "beehiiv", "ghost", "youtube"}
ALLOWED_PRIORITIES = {"critical", "high", "medium", "low"}
ALLOWED_WORKFLOWS = {"comprehensive", "selective", "both"}
ALLOWED_CHECKPOINTS = {"pre_writing", "mid_writing", "post_writing"}

KEYWORD_PRIORITY_MAP: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b(must|never|forbid|prohibit|required)\b", re.IGNORECASE), "high"),
    (re.compile(r"\b(should|avoid|no\s+more\s+than|limit)\b", re.IGNORECASE), "medium"),
]

KEYWORD_ACTION_MAP: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b(avoid|never|do\s+not|forbid|prohibit)\b", re.IGNORECASE), "forbid"),
    (re.compile(r"\b(must|require|include|ensure)\b", re.IGNORECASE), "require"),
    (re.compile(r"\b(should|suggest|consider|recommend)\b", re.IGNORECASE), "suggest"),
]

PLATFORM_HINTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"linkedin", re.IGNORECASE), "linkedin"),
    (re.compile(r"twitter|x\.com", re.IGNORECASE), "twitter"),
    (re.compile(r"substack", re.IGNORECASE), "substack"),
    (re.compile(r"beehiiv", re.IGNORECASE), "beehiiv"),
    (re.compile(r"ghost", re.IGNORECASE), "ghost"),
    (re.compile(r"youtube", re.IGNORECASE), "youtube"),
]

RULE_TYPE_HINTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"buzzword|jargon|clarity|concise|style|tone|voice", re.IGNORECASE), "style"),
    (re.compile(r"grammar|typo|punctuation", re.IGNORECASE), "grammar"),
    (re.compile(r"hook|engagement|cta|call\s*to\s*action", re.IGNORECASE), "engagement"),
    (re.compile(r"structure|outline|format|sections", re.IGNORECASE), "structure"),
    (re.compile(r"quality|consistency|review", re.IGNORECASE), "quality"),
    (re.compile(r"editorial|guideline|policy", re.IGNORECASE), "editorial"),
    (re.compile(r"tone|voice", re.IGNORECASE), "tone"),
]

CHECKPOINT_HINTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"pre[-_\s]?writing|before\s+writing|planning", re.IGNORECASE), "pre_writing"),
    (re.compile(r"mid[-_\s]?writing|during\s+writing|draft", re.IGNORECASE), "mid_writing"),
    (re.compile(r"post[-_\s]?writing|after\s+writing|final|publish", re.IGNORECASE), "post_writing"),
]

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def hash_id(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def normalize_rule_text(text: str) -> str:
    # strip bullets, markdown, extra spaces
    t = re.sub(r"^\s*[-*+]\s+", "", text.strip())
    t = re.sub(r"^\s*\d+[\).]\s+", "", t)
    t = re.sub(r"\s+", " ", t)
    return t


def extract_candidate_lines(md_content: str) -> List[str]:
    lines = []
    for raw in md_content.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("- ", "* ")):
            lines.append(line)
        elif re.match(r"^\d+[\).]\s+", line):
            lines.append(line)
        else:
            # capture directive-like sentences
            if re.search(r"\b(must|should|avoid|never|require|prohibit|forbid|do\s+not)\b", line, re.IGNORECASE):
                lines.append(line)
    # also split long lines into sentences
    sentences: List[str] = []
    for l in lines:
        parts = SENTENCE_SPLIT.split(l)
        sentences.extend(p for p in parts if p and len(p.split()) >= 3)
    return [normalize_rule_text(s) for s in sentences]


def infer_platform(text: str, file_name: str) -> str:
    for pattern, platform in PLATFORM_HINTS:
        if pattern.search(text) or pattern.search(file_name):
            return platform
    return "universal"


def infer_rule_type(text: str) -> str:
    for pattern, rtype in RULE_TYPE_HINTS:
        if pattern.search(text):
            return rtype
    return "style"


def infer_priority(text: str) -> str:
    for pattern, priority in KEYWORD_PRIORITY_MAP:
        if pattern.search(text):
            return priority
    return "low"


def infer_action(text: str) -> str:
    for pattern, action in KEYWORD_ACTION_MAP:
        if pattern.search(text):
            return action
    return "optimize"


def infer_checkpoint(text: str) -> str:
    for pattern, cp in CHECKPOINT_HINTS:
        if pattern.search(text):
            return cp
    return ""


def score_quality(text: str) -> float:
    score = 0.5
    length = len(text)
    if 50 <= length <= 240:
        score += 0.2
    if re.search(r"\b(must|never|forbid|require)\b", text, re.IGNORECASE):
        score += 0.2
    if re.search(r"\b(examples?|e\.g\.|i\.e\.)\b", text, re.IGNORECASE):
        score += 0.05
    return max(0.0, min(1.0, round(score, 2)))


def transform_styleguides(input_dir: str) -> List[Dict]:
    documents: List[Dict] = []
    seen_texts: Set[str] = set()

    for fname in sorted(os.listdir(input_dir)):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(input_dir, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        candidates = extract_candidate_lines(content)
        for raw_text in candidates:
            text = normalize_rule_text(raw_text)
            norm_key = text.lower()
            if len(text) < 12 or norm_key in seen_texts:
                continue

            seen_texts.add(norm_key)
            platform = infer_platform(text, fname)
            rule_type = infer_rule_type(text)
            priority = infer_priority(text)
            rule_action = infer_action(text)
            checkpoint = infer_checkpoint(text)

            rid = f"sg_{rule_type}_{hash_id(text)}"
            metadata: Dict = {
                "rule_id": rid,
                "rule_type": rule_type if rule_type in ALLOWED_RULE_TYPES else "style",
                "platform": platform if platform in ALLOWED_PLATFORMS else "universal",
                "platform_specific": platform != "universal",
                "workflow": "both",
                "priority": priority if priority in ALLOWED_PRIORITIES else "low",
                "checkpoint": checkpoint if checkpoint in ALLOWED_CHECKPOINTS else None,
                "rule_action": rule_action,
                "confidence_threshold": 0.75 if priority in {"critical", "high"} else 0.6,
                "auto_fix": rule_action in {"suggest", "optimize"},
                "applies_to": ["thought_leadership", "industry_update", "tutorial"],
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "source": "styleguides",
                "migrated_from": path,
                "version": 1,
                "usage_count": 0,
                "success_rate": 0.0,
                "related_rules": [],
                "conflicts_with": [],
                "supersedes": [],
                "quality_score": score_quality(text),
            }

            documents.append({
                "content": text,
                "metadata": metadata,
            })

    return documents


def main():
    parser = argparse.ArgumentParser(description="Transform styleguides to ChromaDB-ready rules JSON")
    parser.add_argument("--input-dir", default=STYLEGUIDES_DIR)
    parser.add_argument("--output", default=OUTPUT_DEFAULT)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    docs = transform_styleguides(args.input_dir)

    # Sort deterministically by rule_id
    docs.sort(key=lambda d: d["metadata"]["rule_id"])

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "status": "ok",
        "output": args.output,
        "count": len(docs)
    }))


if __name__ == "__main__":
    main()
