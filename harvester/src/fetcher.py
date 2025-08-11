from typing import List, Dict, Optional, Tuple
import httpx
from datetime import datetime
from .models import RawTrendItem
from .config import settings
import asyncio
import xml.etree.ElementTree as ET


class HackerNewsFetcher:
    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    async def _get_json(self, client: httpx.AsyncClient, path: str) -> Optional[Dict]:
        delay = 0.5
        for attempt in range(3):
            try:
                r = await client.get(f"{self.BASE_URL}/{path}")
                r.raise_for_status()
                return r.json()
            except httpx.HTTPError:
                if attempt == 2:
                    raise
                await asyncio.sleep(delay)
                delay *= 2

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
                    delay = 0.5
                    for attempt in range(3):
                        try:
                            params = {
                                "search_query": query,
                                "sortBy": sort_by,
                                "sortOrder": "descending",
                                "max_results": max(1, limit),
                            }
                            r = await client.get(self.BASE_URL, params=params)
                            r.raise_for_status()
                            txt = r.text
                            if "<entry" in txt:
                                xml_text = txt
                                break
                            # No entries; try next variant
                            break
                        except httpx.HTTPError:
                            if attempt == 2:
                                break
                            await asyncio.sleep(delay)
                            delay *= 2
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
        self.devto = DevToFetcher()
        self.newsdata = NewsDataFetcher()
        self.producthunt = ProductHuntFetcher()

    async def run(self) -> Tuple[List[RawTrendItem], Dict[str, str]]:
        # Run all sources in parallel and merge results, collect errors per source
        tasks = [
            ("hacker-news", self.hn.fetch(limit=5)),
            ("arxiv", self.arxiv.fetch(limit=5)),
            ("dev-to", self.devto.fetch(limit=5)),
            ("newsdata-io", self.newsdata.fetch(limit=5)),
            ("product-hunt", self.producthunt.fetch(limit=5)),
        ]
        results = await asyncio.gather(*(t for _, t in tasks), return_exceptions=True)
        merged: List[RawTrendItem] = []
        errors: Dict[str, str] = {}
        for (name, _), res in zip(tasks, results):
            if isinstance(res, Exception):
                errors[name] = f"{type(res).__name__}: {res}"
                continue
            merged.extend(res)
        return merged, errors


class DevToFetcher:
    BASE_URL = "https://dev.to/api/articles"

    async def fetch(self, limit: int = 5) -> List[RawTrendItem]:
        """Fetch recent AI-related articles from Dev.to using API key if provided.

        Filters by tags commonly used for AI topics.
        """
        headers = {}
        if settings.DEV_TO_API_KEY:
            headers["api-key"] = settings.DEV_TO_API_KEY
        params_list = [
            {"tag": "ai", "top": 7},
            {"tag": "machinelearning", "top": 7},
            {"tag": "llm", "top": 7},
        ]

        articles: List[RawTrendItem] = []
        try:
            async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
                for params in params_list:
                    delay = 0.5
                    for attempt in range(3):
                        try:
                            r = await client.get(self.BASE_URL, params=params)
                            r.raise_for_status()
                            data = r.json()
                            break
                        except httpx.HTTPError:
                            if attempt == 2:
                                data = []
                                break
                            await asyncio.sleep(delay)
                            delay *= 2
                    for a in data:
                        title = a.get("title") or "(no title)"
                        url = a.get("url") or a.get("canonical_url")
                        author = (a.get("user") or {}).get("name")
                        published = a.get("published_at") or a.get("created_at")
                        published_dt = None
                        if published:
                            try:
                                published_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                            except Exception:
                                published_dt = None
                        tags = a.get("tags") or []
                        if isinstance(tags, str):
                            tags = [t.strip() for t in tags.split(",") if t.strip()]
                        summary = a.get("description") or a.get("excerpt")
                        articles.append(
                            RawTrendItem(
                                title=title,
                                summary=summary,
                                url=url,
                                source="dev-to",
                                keywords=tags or ["devto"],
                                author=author,
                                published_at=published_dt,
                            )
                        )
                        if len(articles) >= limit:
                            return articles[:limit]
            return articles[:limit]
        except httpx.HTTPError:
            return []


class NewsDataFetcher:
    BASE_URL = "https://newsdata.io/api/1/news"

    async def fetch(self, limit: int = 5) -> List[RawTrendItem]:
        """Fetch AI-related news from NewsData.io using API key from env.

        We query English language, AI keywords, and tech categories.
        """
        api_key = settings.NEWS_DATA_API_KEY
        if not api_key:
            return []
        # NewsData expects 'apikey' and supports 'q', 'language', 'category', 'page', 'size'
        params = {
            "apikey": api_key,
            "q": "(artificial intelligence) OR (machine learning) OR AI",
            "language": "en",
            "category": "technology,science",
            # NewsData uses 'page' cursor as token, not integer; omit for first page
            "size": max(1, min(limit, 50)),
        }
        data = {}
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                delay = 0.5
                for attempt in range(3):
                    try:
                        r = await client.get(self.BASE_URL, params=params)
                        r.raise_for_status()
                        data = r.json()
                        break
                    except httpx.HTTPError:
                        if attempt == 2:
                            return []
                        await asyncio.sleep(delay)
                        delay *= 2
        except httpx.HTTPError:
            return []

        results = (data or {}).get("results") or []
        items: List[RawTrendItem] = []
        for it in results:
            title = it.get("title") or "(no title)"
            summary = it.get("description") or it.get("content")
            url = it.get("link")
            author = it.get("creator")
            if isinstance(author, list):
                author = ", ".join([a for a in author if a]) or None
            pub = it.get("pubDate") or it.get("published_at")
            published_dt = None
            if pub:
                try:
                    published_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                except Exception:
                    published_dt = None
            keywords = []
            cats = it.get("category") or []
            if isinstance(cats, list):
                keywords.extend(cats)
            # tags/keywords field name varies; include if present
            tags = it.get("keywords") or it.get("tags")
            if isinstance(tags, list):
                keywords.extend(tags)
            items.append(
                RawTrendItem(
                    title=title,
                    summary=summary,
                    url=url,
                    source="newsdata-io",
                    keywords=keywords or ["newsdata"],
                    author=author,
                    published_at=published_dt,
                )
            )
            if len(items) >= limit:
                break
        return items


class ProductHuntFetcher:
    BASE_URL = "https://api.producthunt.com/v2/api/graphql"

    QUERY = """
    query TopPosts($first:Int!) {
      posts(first: $first, order: RANKING) {
        edges {
          node {
            name
            tagline
            url
            description
            createdAt
            votesCount
            reviewsCount
            slug
            topics(first: 5) { edges { node { name } } }
            user { name }
          }
        }
      }
    }
    """

    async def fetch(self, limit: int = 5) -> List[RawTrendItem]:
        token = settings.PRODUCT_HUNT_DEVELOPER_TOKEN
        if not token:
            return []
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {"query": self.QUERY, "variables": {"first": max(1, limit)}}
        data = {}
        try:
            async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
                delay = 0.5
                for attempt in range(3):
                    try:
                        r = await client.post(self.BASE_URL, json=payload)
                        r.raise_for_status()
                        data = r.json()
                        break
                    except httpx.HTTPError:
                        if attempt == 2:
                            return []
                        await asyncio.sleep(delay)
                        delay *= 2
        except httpx.HTTPError:
            return []

        posts = (((data or {}).get("data") or {}).get("posts") or {}).get("edges") or []
        items: List[RawTrendItem] = []
        for edge in posts:
            n = edge.get("node") or {}
            title = n.get("name") or "(no title)"
            summary = n.get("tagline") or n.get("description")
            url = n.get("url")
            author = (n.get("user") or {}).get("name")
            published_dt = None
            if n.get("createdAt"):
                try:
                    published_dt = datetime.fromisoformat(str(n["createdAt"]).replace("Z", "+00:00"))
                except Exception:
                    published_dt = None
            topics = []
            t = n.get("topics") or {}
            for e in (t.get("edges") or []):
                node = e.get("node") or {}
                name = node.get("name")
                if name:
                    topics.append(name)
            items.append(
                RawTrendItem(
                    title=title,
                    summary=summary,
                    url=url,
                    source="product-hunt",
                    keywords=topics or ["producthunt"],
                    author=author,
                    published_at=published_dt,
                )
            )
            if len(items) >= limit:
                break
        return items
