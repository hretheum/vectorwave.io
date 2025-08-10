from abc import ABC, abstractmethod
from typing import List, Dict


class TopicScraper(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def scrape_topics(self) -> List[Dict]:
        """Scrape topics from external source"""
        raise NotImplementedError

    @abstractmethod
    async def score_relevance(self, topic: Dict) -> float:
        """Score topic relevance (0-1)"""
        raise NotImplementedError
