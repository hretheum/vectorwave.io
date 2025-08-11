from typing import List, Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime


class RawTrendItem(BaseModel):
    title: str
    summary: Optional[str] = None
    url: Optional[HttpUrl] = None
    source: str
    keywords: List[str] = []
    author: Optional[str] = None
    published_at: Optional[datetime] = None
