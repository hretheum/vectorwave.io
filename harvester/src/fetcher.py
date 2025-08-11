from typing import List, Dict, Optional
import httpx
from datetime import datetime
from .models import RawTrendItem


class HackerNewsFetcher:
    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    async def _get_json(self, client: httpx.AsyncClient, path: str) -> Optional[Dict]:
        r = await client.get(f"{self.BASE_URL}/{path}")
        r.raise_for_status()
        return r.json()

    async def fetch(self, limit: int = 5) -> List[RawTrendItem]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            ids = await self._get_json(client, "topstories.json") or []
            items: List[RawTrendItem] = []
            for sid in ids[: max(1, limit)]:
                data = await self._get_json(client, f"item/{sid}.json") or {}
                title = data.get("title") or "(no title)"
                url = data.get("url")
                author = data.get("by")
                time_ts = data.get("time")
                published_at = None
                if isinstance(time_ts, (int, float)):
                    published_at = datetime.utcfromtimestamp(time_ts)
                items.append(
                    RawTrendItem(
                        title=title,
                        summary=None,
                        url=url,
                        source="hacker-news",
                        keywords=["hn"],
                        author=author,
                        published_at=published_at,
                    )
                )
            return items


class FetcherEngine:
    def __init__(self) -> None:
        self.hn = HackerNewsFetcher()

    async def run(self) -> List[RawTrendItem]:
        return await self.hn.fetch(limit=5)
