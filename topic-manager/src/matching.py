from typing import Dict, List, Tuple
from functools import lru_cache


def suggest_platforms(topic: Dict) -> List[str]:
    """Suggest platforms for a topic based on simple heuristics.

    Deterministic given same input; used as a placeholder for Phase 2.
    """
    title = (topic.get("title") or "").strip().lower()
    keywords = tuple(sorted({str(k).strip().lower() for k in (topic.get("keywords") or [])}))
    return _suggest_platforms_cached((title, keywords))


@lru_cache(maxsize=2048)
def _suggest_platforms_cached(key: Tuple[str, Tuple[str, ...]]) -> List[str]:
    title, keywords = key
    joined = (title + " " + " ".join(keywords)).strip()

    platforms: List[str] = []

    if any(k in joined for k in ["enterprise", "b2b", "linkedin", "career"]):
        platforms.append("linkedin")
    if any(k in joined for k in ["ai", "ml", "dev", "opensource", "oss", "python", "js"]):
        platforms.append("twitter")
    if any(k in joined for k in ["newsletter", "longform", "case study", "deep dive"]):
        platforms.append("beehiiv")

    if not platforms:
        platforms = ["linkedin", "twitter"]

    weight = {"linkedin": 2, "twitter": 1, "beehiiv": 3}
    return sorted(set(platforms), key=lambda p: weight.get(p, 99))
