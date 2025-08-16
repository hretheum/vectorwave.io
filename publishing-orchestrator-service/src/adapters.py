from typing import Dict, Any


def linkedin_adapter(content: str, topic: Dict[str, Any]) -> Dict[str, Any]:
    # Simple formatting for LinkedIn
    return {
        "content": content.strip(),
        "hashtags": ["#VectorWave", "#AI", "#LinkedIn"],
        "meta": {"platform": "linkedin", "title": topic.get("title", "")},
    }


def twitter_adapter(content: str, topic: Dict[str, Any]) -> Dict[str, Any]:
    # Trim to 280 chars and add a CTA
    trimmed = (content[:270] + "…") if len(content) > 280 else content
    return {
        "content": trimmed,
        "cta": "Retweet if useful",
        "meta": {"platform": "twitter", "title": topic.get("title", "")},
    }


def beehiiv_adapter(content: str, topic: Dict[str, Any]) -> Dict[str, Any]:
    # Newsletter wrapper
    return {
        "subject": topic.get("title", "Newsletter"),
        "body": content,
        "meta": {"platform": "beehiiv"},
    }


def ghost_adapter(content: str, topic: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": topic.get("title", "Post"),
        "html": f"<p>{content}</p>",
        "tags": ["VectorWave", "AI"],
        "meta": {"platform": "ghost"},
    }


PLATFORM_ADAPTERS = {
    "linkedin": linkedin_adapter,
    "twitter": twitter_adapter,
    "beehiiv": beehiiv_adapter,
    "ghost": ghost_adapter,
}
