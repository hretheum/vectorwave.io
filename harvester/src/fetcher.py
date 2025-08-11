from typing import List, Dict


class HackerNewsFetcher:
    async def fetch(self, limit: int = 5) -> List[Dict]:
        # Phase 1 placeholder: return deterministic items
        return [
            {
                "title": f"HN Story #{i+1}",
                "summary": "Placeholder summary",
                "url": f"https://news.ycombinator.com/item?id={1000+i}",
                "source": "hacker-news",
                "keywords": ["ai", "hn"],
            }
            for i in range(limit)
        ]


class FetcherEngine:
    def __init__(self) -> None:
        self.hn = HackerNewsFetcher()

    async def run(self) -> List[Dict]:
        items = await self.hn.fetch(limit=5)
        return items
