from __future__ import annotations

from typing import Dict, List, Optional, Tuple
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
    def list(self, limit: int = 100, offset: int = 0, q: Optional[str] = None, content_type: Optional[str] = None) -> List[TopicModel]: ...


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

    def list(self, limit: int = 100, offset: int = 0, q: Optional[str] = None, content_type: Optional[str] = None) -> List[TopicModel]:
        vals = list(self._store.values())
        if q:
            ql = q.lower()
            vals = [t for t in vals if ql in t.title.lower() or ql in t.description.lower() or any(ql in k.lower() for k in t.keywords)]
        if content_type:
            vals = [t for t in vals if t.content_type.lower() == content_type.lower()]
        return vals[offset: offset + limit]


class SQLiteTopicRepository(TopicRepository):
    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER NOT NULL
                )
                """
            )
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
        # initialize schema version to 1 if empty
        cur = self._conn.execute("SELECT COUNT(1) FROM schema_version")
        if cur.fetchone()[0] == 0:
            self._conn.execute("INSERT INTO schema_version(version) VALUES(1)")
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

    def list(self, limit: int = 100, offset: int = 0, q: Optional[str] = None, content_type: Optional[str] = None) -> List[TopicModel]:
        sql = "SELECT topic_id, title, description, keywords, content_type FROM topics"
        args: Tuple = tuple()
        clauses = []
        if q:
            clauses.append("(LOWER(title) LIKE ? OR LOWER(description) LIKE ? OR LOWER(keywords) LIKE ?)")
            ql = f"%{q.lower()}%"
            args += (ql, ql, ql)
        if content_type:
            clauses.append("LOWER(content_type) = ?")
            args += (content_type.lower(),)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY topic_id LIMIT ? OFFSET ?"
        args += (limit, offset)
        cur = self._conn.execute(sql, args)
        rows = cur.fetchall()
        return [
            TopicModel(
                topic_id=r[0], title=r[1], description=r[2], keywords=[k for k in r[3].split(",") if k], content_type=r[4]
            )
            for r in rows
        ]
