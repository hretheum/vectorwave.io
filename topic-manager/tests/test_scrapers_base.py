import asyncio
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from scrapers.base_scraper import TopicScraper


class DummyScraper(TopicScraper):
    async def scrape_topics(self):
        return [{"title": "AI news", "url": "https://example.com"}]

    async def score_relevance(self, topic):
        return 0.7


def test_base_scraper_contract():
    s = DummyScraper("dummy")
    topics = asyncio.run(s.scrape_topics())
    assert isinstance(topics, list)
    assert 0.0 <= asyncio.run(s.score_relevance(topics[0])) <= 1.0
