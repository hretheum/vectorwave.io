from typing import List, Dict

class HackerNewsTopicScraperStub:
    async def scrape_topics(self) -> List[Dict]:
        return [
            {"title": "Hacker News: AI breakthrough", "description": "Top story about AI", "keywords": ["ai", "hn"], "content_type": "POST"},
            {"title": "Open-source tools gaining traction", "description": "OSS roundup", "keywords": ["oss"], "content_type": "ARTICLE"},
        ]

    async def score_relevance(self, topic: Dict) -> float:
        return 0.5
