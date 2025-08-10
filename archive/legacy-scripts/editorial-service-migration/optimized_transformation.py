#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures as futures
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Reuse constants
ALLOWED_RULE_TYPES = {"style", "structure", "quality", "editorial", "grammar", "tone", "engagement"}
ALLOWED_PLATFORMS = {"universal", "linkedin", "twitter", "substack", "beehiiv", "ghost", "youtube"}
ALLOWED_PRIORITIES = {"critical", "high", "medium", "low"}
ALLOWED_ACTIONS = {"forbid", "require", "suggest", "optimize"}


def _hash_id(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _score_quality(text: str) -> float:
    score = 0.6
    n = len(text)
    if 40 <= n <= 200:
        score += 0.2
    if any(w in text.lower() for w in ("must", "never", "require", "limit", "max")):
        score += 0.15
    return max(0.0, min(1.0, round(score, 2)))


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _build_aiwf_doc(hit: Dict[str, Any], fpath: str, value: Optional[str]) -> Optional[Dict[str, Any]]:
    category = (hit.get("category_guess") or hit.get("type") or "directive_line").lower()
    base_snippet = hit.get("snippet", "")

    # content selection fast path
    if category == "forbidden" and value:
        content = f"Avoid using the phrase: '{value}'"
        rule_type = "style"
        rule_action = "forbid"
        priority = "high"
    elif category == "required" and value:
        content = f"Ensure to include required element: '{value}'"
        rule_type = "editorial"
        rule_action = "require"
        priority = "high"
    elif category == "pattern" and value:
        content = f"Follow the style pattern: '{value}' where applicable"
        rule_type = "style"
        rule_action = "optimize"
        priority = "medium"
    else:
        content = base_snippet.strip()
        if len(content) < 5:
            return None
        rule_type = "style"
        rule_action = "suggest"
        priority = (hit.get("priority_guess") or "low").lower()
        if priority not in ALLOWED_PRIORITIES:
            priority = "low"

    rid = f"aiwf_{category}_{_hash_id(content)}"
    metadata: Dict[str, Any] = {
        "rule_id": rid,
        "rule_type": rule_type,
        "platform": "universal",
        "platform_specific": False,
        "workflow": "both",
        "priority": priority,
        "checkpoint": None,
        "rule_action": rule_action,
        "confidence_threshold": 0.7 if priority in {"critical", "high"} else 0.6,
        "auto_fix": rule_action in {"suggest", "optimize"},
        "applies_to": ["thought_leadership", "industry_update", "tutorial"],
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "source": "ai_writing_flow_migration",
        "migrated_from": fpath,
        "version": 1,
        "usage_count": 0,
        "success_rate": 0.0,
        "related_rules": [],
        "conflicts_with": [],
        "supersedes": [],
        "quality_score": _score_quality(content),
        "discovery": {
            "type": hit.get("type"),
            "start_line": hit.get("start_line"),
            "end_line": hit.get("end_line"),
        },
    }
    return {"content": content, "metadata": metadata}


def transform_aiwf_catalog_fast(catalog: Dict[str, Any], workers: int = 4) -> List[Dict[str, Any]]:
    files = catalog.get("files", [])

    tasks: List[Tuple[Dict[str, Any], str, Optional[str]]] = []
    for f in files:
        fpath = f.get("file")
        for h in f.get("hits", []):
            values = (h.get("values_preview") or [])
            if values:
                for v in values:
                    tasks.append((h, fpath, v))
            else:
                tasks.append((h, fpath, None))

    results: List[Optional[Dict[str, Any]]] = []
    with futures.ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = [ex.submit(_build_aiwf_doc, h, fpath, v) for (h, fpath, v) in tasks]
        for fut in futures.as_completed(futs):
            results.append(fut.result())

    # de-duplicate by content
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for r in results:
        if not r:
            continue
        key = r["content"].strip().lower()
        if len(key) < 12 or key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    deduped.sort(key=lambda d: d["metadata"]["rule_id"])
    return deduped


def _build_platform_doc(hit: Dict[str, Any], fpath: str) -> Optional[Dict[str, Any]]:
    platform = (hit.get("platform") or "universal").lower()
    if platform not in ALLOWED_PLATFORMS:
        platform = "universal"
    values = hit.get("values", {}) if isinstance(hit.get("values"), dict) else {}
    nums = values.get("numbers", [])
    strings = values.get("strings", [])
    t = hit.get("type")

    if t in ("max_length", "character_limit"):
        limit = nums[0] if nums else None
        content = (
            f"{platform.title()} content must not exceed {limit} characters"
            if limit else f"{platform.title()} content must respect the platform character limit"
        )
        rule_type = "structure"; rule_action = "require"; priority = "critical"
    elif t == "hashtag_rules":
        cnt = nums[0] if nums else None
        content = (
            f"Use no more than {cnt} hashtags on {platform.title()}"
            if cnt else f"Use platform-appropriate number of hashtags on {platform.title()}"
        )
        rule_type = "engagement"; rule_action = "optimize"; priority = "medium"
    elif t == "forbidden_phrases":
        phrase = strings[0] if strings else None
        content = (
            f"Avoid using the phrase: '{phrase}' on {platform.title()}"
            if phrase else f"Avoid platform-forbidden phrases on {platform.title()}"
        )
        rule_type = "style"; rule_action = "forbid"; priority = "high"
    elif t == "required_elements":
        elem = strings[0] if strings else None
        content = (
            f"Ensure to include required element on {platform.title()}: '{elem}'"
            if elem else f"Ensure platform-required elements are included on {platform.title()}"
        )
        rule_type = "editorial"; rule_action = "require"; priority = "high"
    elif t == "regex_pattern":
        pat = strings[0] if strings else None
        content = (
            f"Follow platform style pattern on {platform.title()}: '{pat}'"
            if pat else f"Follow platform style patterns on {platform.title()}"
        )
        rule_type = "style"; rule_action = "optimize"; priority = "medium"
    else:
        content = f"Ensure content follows {platform.title()} platform-specific rules"
        rule_type = "editorial"; rule_action = "suggest"; priority = "low"

    rid = f"pub_{platform}_{t}_{_hash_id(content)}"
    metadata: Dict[str, Any] = {
        "rule_id": rid,
        "rule_type": rule_type,
        "platform": platform,
        "platform_specific": platform != "universal",
        "workflow": "both",
        "priority": priority,
        "checkpoint": None,
        "rule_action": rule_action,
        "confidence_threshold": 0.7 if priority in {"critical", "high"} else 0.6,
        "auto_fix": rule_action in {"suggest", "optimize"},
        "applies_to": ["thought_leadership", "industry_update", "tutorial"],
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "source": "publisher_migration",
        "migrated_from": fpath,
        "version": 1,
        "usage_count": 0,
        "success_rate": 0.0,
        "related_rules": [],
        "conflicts_with": [],
        "supersedes": [],
        "quality_score": _score_quality(content),
        "platform_constraints": values,
        "discovery": {"type": t, "line": hit.get("line")},
    }
    return {"content": content, "metadata": metadata}


def transform_platform_catalog_fast(catalog: Dict[str, Any], workers: int = 4) -> List[Dict[str, Any]]:
    files = catalog.get("files", [])
    hits: List[Tuple[Dict[str, Any], str]] = []
    for f in files:
        fpath = f.get("file")
        for h in f.get("hits", []):
            hits.append((h, fpath))

    results: List[Optional[Dict[str, Any]]] = []
    with futures.ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = [ex.submit(_build_platform_doc, h, fpath) for (h, fpath) in hits]
        for fut in futures.as_completed(futs):
            results.append(fut.result())

    # de-duplicate by (platform, content)
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for r in results:
        if not r:
            continue
        key = (r["metadata"].get("platform", "universal"), r["content"].strip().lower())
        if len(key[1]) < 12 or key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    deduped.sort(key=lambda d: (d["metadata"]["platform"], d["metadata"]["rule_id"]))
    return deduped
