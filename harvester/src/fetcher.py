from typing import List, Dict, Optional
import httpx
from datetime import datetime
from .models import RawTrendItem
import asyncio
import xml.etree.ElementTree as ET


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


class ArXivFetcher:
    BASE_URL = "https://export.arxiv.org/api/query"

    async def fetch(self, limit: int = 5) -> List[RawTrendItem]:
        """Fetch recent AI-related papers from ArXiv and normalize them.

        Uses Atom XML feed. Categories targeted: cs.AI, cs.LG, cs.CV.
        """
        params = {
            "search_query": "cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CV",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": max(1, limit),
        }
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                r = await client.get(self.BASE_URL, params=params)
                r.raise_for_status()
                xml_text = r.text
        except httpx.HTTPError:
            return []

        try:
            # Parse Atom feed
            root = ET.fromstring(xml_text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            items: List[RawTrendItem] = []
            for entry in root.findall("atom:entry", ns):
                title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip() or "(no title)"
                summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip() or None

                # Prefer alternate link, fallback to id
                link_url: Optional[str] = None
                for link in entry.findall("atom:link", ns):
                    rel = link.attrib.get("rel", "")
                    if rel in ("alternate", "") and link.attrib.get("href"):
                        link_url = link.attrib.get("href")
                        break
                if not link_url:
                    link_url = entry.findtext("atom:id", default=None, namespaces=ns)

                # Authors
                authors = [a.findtext("atom:name", default="", namespaces=ns) or "" for a in entry.findall("atom:author", ns)]
                author = ", ".join([a for a in authors if a]) or None

                # Published date
                published_raw = entry.findtext("atom:published", default=None, namespaces=ns)
                published_dt: Optional[datetime] = None
                if published_raw:
                    try:
                        published_dt = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
                    except Exception:
                        published_dt = None

                # Categories as keywords
                keywords: List[str] = []
                for cat in entry.findall("atom:category", ns):
                    term = cat.attrib.get("term")
                    if term:
                        keywords.append(term)

                items.append(
                    RawTrendItem(
                        title=title,
                        summary=summary,
                        url=link_url,
                        source="arxiv",
                        keywords=keywords or ["arxiv"],
                        author=author,
                        published_at=published_dt,
                    )
                )
            return items[: max(1, limit)]
        except Exception:
            # Parsing issues should not break the pipeline
            return []


class FetcherEngine:
    def __init__(self) -> None:
        self.hn = HackerNewsFetcher()
        self.arxiv = ArXivFetcher()

    async def run(self) -> List[RawTrendItem]:
        # Run all sources in parallel and merge results
        results = await asyncio.gather(
            self.hn.fetch(limit=5),
            self.arxiv.fetch(limit=5),
            return_exceptions=True,
        )
        merged: List[RawTrendItem] = []
        for res in results:
            if isinstance(res, Exception):
                continue
            merged.extend(res)
        return merged
