from typing import Dict


def platform_hints(platform: str) -> Dict[str, str | int]:
    p = platform.lower()
    if p == "linkedin":
        return {"max_length": 1300, "sections": "hook, insight, CTA", "tone": "professional"}
    if p == "twitter":
        return {"max_length": 280, "sections": "hook, thread points, CTA", "tone": "conversational"}
    if p == "beehiiv":
        return {"max_length": 5000, "sections": "intro, body, value, CTA", "tone": "newsletter"}
    if p == "ghost":
        return {"max_length": 8000, "sections": "intro, sections, conclusion", "tone": "blog"}
    return {"max_length": 1000, "sections": "intro, body, CTA", "tone": "neutral"}
