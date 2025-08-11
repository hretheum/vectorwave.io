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
        headers = {
            "User-Agent": "vector-wave-harvester/1.0 (+https://vector-wave.local; contact: dev@vector-wave.local)",
            "Accept": "application/atom+xml, application/xml;q=0.9, */*;q=0.8",
        }
        search_variants = [
            ("cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CV", "submittedDate"),
            ("cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CV", "lastUpdatedDate"),
            ("cat:cs.AI", "submittedDate"),
            ("cat:cs.LG", "submittedDate"),
            ("cat:cs.CV", "submittedDate"),
            ("all:ai", "submittedDate"),
            ("ti:ai", "submittedDate"),
        ]

        xml_text: Optional[str] = None
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
                for query, sort_by in search_variants:
                    params = {
                        "search_query": query,
                        "sortBy": sort_by,
                        "sortOrder": "descending",
                        "max_results": max(1, limit),
                    }
                    r = await client.get(self.BASE_URL, params=params)
                    r.raise_for_status()
                    txt = r.text
                    # Fast check: look for any <entry>
                    if "<entry" in txt:
                        xml_text = txt
                        break
                    # Otherwise, try the next variant
        except httpx.HTTPError:
            return []
        if not xml_text:
            return []

        try:
            # Parse Atom feed robustly (with and without explicit namespace prefixes)
            atom_ns = "http://www.w3.org/2005/Atom"
            root = ET.fromstring(xml_text)

            def findall_e(parent: ET.Element, local: str) -> List[ET.Element]:
                nodes = parent.findall(f"{{{atom_ns}}}{local}")
                if not nodes:
                    nodes = parent.findall(local)
                return nodes

            def findtext_e(parent: ET.Element, local: str) -> Optional[str]:
                node = parent.find(f"{{{atom_ns}}}{local}")
                if node is not None and node.text is not None:
                    return node.text
                node = parent.find(local)
                return node.text if node is not None else None

            items: List[RawTrendItem] = []
            entries = findall_e(root, "entry")
            for entry in entries:
                title = (findtext_e(entry, "title") or "").strip() or "(no title)"
                summary = (findtext_e(entry, "summary") or "").strip() or None

                # Prefer alternate link, fallback to id
                link_url: Optional[str] = None
                for link in findall_e(entry, "link"):
                    rel = link.attrib.get("rel", "")
                    href = link.attrib.get("href")
                    if href and rel in ("alternate", ""):
                        link_url = href
                        break
                if not link_url:
                    link_url = findtext_e(entry, "id")

                # Authors
                authors: List[str] = []
                for a in findall_e(entry, "author"):
                    name = findtext_e(a, "name") or ""
                    if name:
                        authors.append(name)
                author = ", ".join(authors) or None

                # Published date
                published_raw = findtext_e(entry, "published")
                published_dt: Optional[datetime] = None
                if published_raw:
                    try:
                        published_dt = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
                    except Exception:
                        published_dt = None

                # Categories as keywords
                keywords: List[str] = []
                for cat in findall_e(entry, "category"):
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
