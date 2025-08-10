from typing import Dict, List


def suggest_platforms(topic: Dict) -> List[str]:
    """Suggest platforms for a topic based on simple heuristics.

    Deterministic given same input; used as a placeholder for Phase 2.
    """
    title = (topic.get("title") or "").lower()
    keywords = [str(k).lower() for k in topic.get("keywords") or []]

    platforms: List[str] = []

    if any(k in (title + " "+" ".join(keywords)) for k in ["enterprise", "b2b", "linkedin", "career"]):
        platforms.append("linkedin")
    if any(k in (title + " "+" ".join(keywords)) for k in ["ai", "ml", "dev", "opensource", "oss", "python", "js"]):
        platforms.append("twitter")
    if any(k in (title + " "+" ".join(keywords)) for k in ["newsletter", "longform", "case study", "deep dive"]):
        platforms.append("beehiiv")

    if not platforms:
        platforms = ["linkedin", "twitter"]

    # Make deterministic: sort by fixed weight
    weight = {"linkedin": 2, "twitter": 1, "beehiiv": 3}
    platforms = sorted(set(platforms), key=lambda p: weight.get(p, 99))
    return platforms
