from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel
import sqlite3
import threading


class TopicModel(BaseModel):
    topic_id: str
    title: str
    description: str
    keywords: List[str]
    content_type: str


class TopicRepository:
    def create(self, topic: TopicModel) -> str: ...
    def get(self, topic_id: str) -> Optional[TopicModel]: ...
    def update(self, topic: TopicModel) -> bool: ...
    def delete(self, topic_id: str) -> bool: ...
    def list(self, limit: int = 100, offset: int = 0) -> List[TopicModel]: ...


class InMemoryTopicRepository(TopicRepository):
    def __init__(self) -> None:
        self._store: Dict[str, TopicModel] = {}

    def create(self, topic: TopicModel) -> str:
        self._store[topic.topic_id] = topic
        return topic.topic_id

    def get(self, topic_id: str) -> Optional[TopicModel]:
        return self._store.get(topic_id)

    def update(self, topic: TopicModel) -> bool:
        if topic.topic_id not in self._store:
            return False
        self._store[topic.topic_id] = topic
        return True

    def delete(self, topic_id: str) -> bool:
        return self._store.pop(topic_id, None) is not None

    def list(self, limit: int = 100, offset: int = 0) -> List[TopicModel]:
        vals = list(self._store.values())
        return vals[offset: offset + limit]


class SQLiteTopicRepository(TopicRepository):
    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS topics (
                topic_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                keywords TEXT NOT NULL,
                content_type TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def create(self, topic: TopicModel) -> str:
        with self._lock:
            self._conn.execute(
                "INSERT INTO topics(topic_id, title, description, keywords, content_type) VALUES (?, ?, ?, ?, ?)",
                (
                    topic.topic_id,
                    topic.title,
                    topic.description,
                    ",".join(topic.keywords),
                    topic.content_type,
                ),
            )
            self._conn.commit()
        return topic.topic_id

    def get(self, topic_id: str) -> Optional[TopicModel]:
        cur = self._conn.execute("SELECT topic_id, title, description, keywords, content_type FROM topics WHERE topic_id = ?", (topic_id,))
        row = cur.fetchone()
        if not row:
            return None
        return TopicModel(
            topic_id=row[0],
            title=row[1],
            description=row[2],
            keywords=[k for k in row[3].split(",") if k],
            content_type=row[4],
        )

    def update(self, topic: TopicModel) -> bool:
        with self._lock:
            cur = self._conn.execute(
                "UPDATE topics SET title=?, description=?, keywords=?, content_type=? WHERE topic_id=?",
                (
                    topic.title,
                    topic.description,
                    ",".join(topic.keywords),
                    topic.content_type,
                    topic.topic_id,
                ),
            )
            self._conn.commit()
            return cur.rowcount > 0

    def delete(self, topic_id: str) -> bool:
        with self._lock:
            cur = self._conn.execute("DELETE FROM topics WHERE topic_id=?", (topic_id,))
            self._conn.commit()
            return cur.rowcount > 0

    def list(self, limit: int = 100, offset: int = 0) -> List[TopicModel]:
        cur = self._conn.execute(
            "SELECT topic_id, title, description, keywords, content_type FROM topics ORDER BY topic_id LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = cur.fetchall()
        return [
            TopicModel(
                topic_id=r[0], title=r[1], description=r[2], keywords=[k for k in r[3].split(",") if k], content_type=r[4]
            )
            for r in rows
        ]
