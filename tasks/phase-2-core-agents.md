# PHASE 2: Core Agent Implementation

## 📋 Bloki Zadań Atomowych

### Blok 5: Content Discovery Domain
**Czas**: 4h | **Agent**: project-coder | **Dependencies**: Phase 1 complete

**Task 2.0**: Content Scout domain implementation

#### Execution Steps:
1. **Enhanced Topic entity with business logic**
   ```python
   # src/domains/content/domain/entities/topic.py
   from dataclasses import dataclass, field
   from datetime import datetime
   from typing import List, Optional, Dict
   from uuid import UUID, uuid4
   from enum import Enum
   
   class TopicStatus(Enum):
       DISCOVERED = "discovered"
       ANALYZING = "analyzing"
       PENDING_REVIEW = "pending_review"
       APPROVED = "approved"
       REJECTED = "rejected"
   
   class TopicCategory(Enum):
       TECH = "technology"
       BUSINESS = "business"
       POLITICS = "politics"
       ENTERTAINMENT = "entertainment"
       SCIENCE = "science"
       HEALTH = "health"
   
   @dataclass
   class Topic:
       id: UUID = field(default_factory=uuid4)
       title: str = ""
       description: str = ""
       url: str = ""
       source: str = ""
       discovered_at: datetime = field(default_factory=datetime.utcnow)
       keywords: List[str] = field(default_factory=list)
       initial_score: float = 0.0
       category: TopicCategory = TopicCategory.TECH
       status: TopicStatus = TopicStatus.DISCOVERED
       sentiment: Optional[float] = None
       metadata: Dict[str, any] = field(default_factory=dict)
       
       def calculate_relevance_score(self, target_keywords: List[str]) -> float:
           """Calculate relevance based on keyword overlap"""
           if not self.keywords or not target_keywords:
               return 0.0
               
           overlap = set(self.keywords) & set(target_keywords)
           return len(overlap) / len(set(self.keywords) | set(target_keywords))
       
       def is_fresh(self, hours: int = 24) -> bool:
           """Check if topic is fresh (within X hours)"""
           delta = datetime.utcnow() - self.discovered_at
           return delta.total_seconds() < (hours * 3600)
       
       def mark_as_analyzing(self) -> None:
           """Transition to analyzing state"""
           if self.status == TopicStatus.DISCOVERED:
               self.status = TopicStatus.ANALYZING
           else:
               raise ValueError(f"Cannot transition from {self.status} to analyzing")
       
       def approve(self) -> None:
           """Approve topic for publication"""
           if self.status == TopicStatus.PENDING_REVIEW:
               self.status = TopicStatus.APPROVED
           else:
               raise ValueError(f"Cannot approve topic in {self.status} state")
   ```

2. **Source entity for RSS/API management**
   ```python
   # src/domains/content/domain/entities/source.py
   from dataclasses import dataclass, field
   from datetime import datetime
   from typing import Dict, List, Optional
   from uuid import UUID, uuid4
   from enum import Enum
   
   class SourceType(Enum):
       RSS = "rss"
       API = "api"
       SOCIAL = "social"
       SCRAPING = "scraping"
   
   class SourceStatus(Enum):
       ACTIVE = "active"
       INACTIVE = "inactive"
       ERROR = "error"
       RATE_LIMITED = "rate_limited"
   
   @dataclass
   class Source:
       id: UUID = field(default_factory=uuid4)
       name: str = ""
       url: str = ""
       source_type: SourceType = SourceType.RSS
       status: SourceStatus = SourceStatus.ACTIVE
       reliability_score: float = 0.8
       last_checked: Optional[datetime] = None
       check_interval_minutes: int = 60
       rate_limit_per_hour: Optional[int] = None
       metadata: Dict[str, any] = field(default_factory=dict)
       error_count: int = 0
       success_count: int = 0
       
       def calculate_success_rate(self) -> float:
           """Calculate success rate percentage"""
           total = self.success_count + self.error_count
           if total == 0:
               return 0.0
           return self.success_count / total
       
       def should_check_now(self) -> bool:
           """Check if source should be checked now"""
           if self.status != SourceStatus.ACTIVE:
               return False
               
           if not self.last_checked:
               return True
               
           minutes_since_check = (datetime.utcnow() - self.last_checked).total_seconds() / 60
           return minutes_since_check >= self.check_interval_minutes
       
       def record_success(self) -> None:
           """Record successful check"""
           self.success_count += 1
           self.last_checked = datetime.utcnow()
           if self.status == SourceStatus.ERROR:
               self.status = SourceStatus.ACTIVE
               self.error_count = 0
       
       def record_error(self) -> None:
           """Record failed check"""
           self.error_count += 1
           self.last_checked = datetime.utcnow()
           
           if self.error_count >= 5:
               self.status = SourceStatus.ERROR
   ```

3. **Content Discovery Service z business logic**
   ```python
   # src/domains/content/domain/services/content_discovery_service.py
   from typing import List, Dict, Optional
   from datetime import datetime, timedelta
   import asyncio
   from uuid import UUID
   
   from ..entities.topic import Topic, TopicCategory, TopicStatus
   from ..entities.source import Source, SourceStatus
   from ..repositories.topic_repository import ITopicRepository
   from ..repositories.source_repository import ISourceRepository
   
   class ContentDiscoveryService:
       def __init__(
           self, 
           topic_repo: ITopicRepository,
           source_repo: ISourceRepository
       ):
           self.topic_repo = topic_repo
           self.source_repo = source_repo
           
       async def discover_from_all_sources(self) -> List[Topic]:
           """Discover topics from all active sources"""
           sources = await self.source_repo.find_active_sources()
           discovered_topics = []
           
           for source in sources:
               if source.should_check_now():
                   try:
                       topics = await self._discover_from_source(source)
                       discovered_topics.extend(topics)
                       source.record_success()
                   except Exception as e:
                       source.record_error()
                       print(f"Error discovering from {source.name}: {e}")
                   
                   await self.source_repo.save(source)
           
           return discovered_topics
       
       async def _discover_from_source(self, source: Source) -> List[Topic]:
           """Discover topics from a specific source"""
           # This will be implemented by infrastructure services
           # For now, return empty list
           return []
       
       async def deduplicate_topics(self, topics: List[Topic]) -> List[Topic]:
           """Remove duplicate topics based on URL and title similarity"""
           unique_topics = []
           seen_urls = set()
           
           for topic in topics:
               if topic.url not in seen_urls:
                   # Check for existing similar topics
                   similar = await self._find_similar_topic(topic)
                   if not similar:
                       unique_topics.append(topic)
                       seen_urls.add(topic.url)
           
           return unique_topics
       
       async def _find_similar_topic(self, topic: Topic) -> Optional[Topic]:
           """Find similar topic by URL or title"""
           # Check by exact URL first
           existing = await self.topic_repo.find_by_url(topic.url)
           if existing:
               return existing
           
           # Check by title similarity (basic implementation)
           recent_topics = await self.topic_repo.find_recent(limit=100)
           for existing_topic in recent_topics:
               if self._calculate_title_similarity(topic.title, existing_topic.title) > 0.8:
                   return existing_topic
           
           return None
       
       def _calculate_title_similarity(self, title1: str, title2: str) -> float:
           """Calculate title similarity using simple word overlap"""
           words1 = set(title1.lower().split())
           words2 = set(title2.lower().split())
           
           if not words1 or not words2:
               return 0.0
               
           intersection = words1 & words2
           union = words1 | words2
           
           return len(intersection) / len(union)
   ```

4. **Repository interfaces z enhanced methods**
   ```python
   # src/domains/content/domain/repositories/source_repository.py
   from abc import ABC, abstractmethod
   from typing import List, Optional
   from uuid import UUID
   
   from ..entities.source import Source, SourceStatus, SourceType
   
   class ISourceRepository(ABC):
       @abstractmethod
       async def save(self, source: Source) -> None:
           pass
           
       @abstractmethod
       async def find_by_id(self, source_id: UUID) -> Optional[Source]:
           pass
           
       @abstractmethod
       async def find_active_sources(self) -> List[Source]:
           pass
           
       @abstractmethod
       async def find_by_type(self, source_type: SourceType) -> List[Source]:
           pass
           
       @abstractmethod
       async def find_sources_to_check(self) -> List[Source]:
           pass
   ```

**Success Criteria**:
- [ ] Topic entity z business logic methods
- [ ] Source entity z rate limiting logic
- [ ] ContentDiscoveryService z deduplication
- [ ] Repository interfaces defined
- [ ] Unit tests dla domain logic >85% coverage

---

### Blok 6: RSS Infrastructure
**Czas**: 3h | **Agent**: project-coder | **Dependencies**: Blok 5

**Task 2.1**: RSS Feed scraping service

#### Execution Steps:
1. **RSS Scraping Service implementation**
   ```python
   # src/domains/content/infrastructure/services/rss_service.py
   import asyncio
   import aiohttp
   import feedparser
   from typing import List, Optional, Dict
   from datetime import datetime
   from urllib.parse import urljoin, urlparse
   
   from ...domain.entities.topic import Topic, TopicCategory
   from ...domain.entities.source import Source
   
   class RSSService:
       def __init__(self, session: aiohttp.ClientSession):
           self.session = session
           self.user_agent = "AI Kolegium Redakcyjne Bot 1.0"
           
       async def fetch_topics_from_rss(self, source: Source) -> List[Topic]:
           """Fetch topics from RSS feed"""
           try:
               headers = {"User-Agent": self.user_agent}
               timeout = aiohttp.ClientTimeout(total=30)
               
               async with self.session.get(source.url, headers=headers, timeout=timeout) as response:
                   if response.status != 200:
                       raise Exception(f"HTTP {response.status}: {await response.text()}")
                   
                   content = await response.text()
                   return self._parse_rss_content(content, source)
                   
           except asyncio.TimeoutError:
               raise Exception("RSS feed request timed out")
           except Exception as e:
               raise Exception(f"Failed to fetch RSS feed: {str(e)}")
       
       def _parse_rss_content(self, content: str, source: Source) -> List[Topic]:
           """Parse RSS content into Topic entities"""
           feed = feedparser.parse(content)
           topics = []
           
           if feed.bozo and feed.bozo_exception:
               print(f"Warning: RSS feed has issues: {feed.bozo_exception}")
           
           for entry in feed.entries[:50]:  # Limit to 50 most recent
               topic = self._create_topic_from_entry(entry, source)
               if topic:
                   topics.append(topic)
           
           return topics
       
       def _create_topic_from_entry(self, entry, source: Source) -> Optional[Topic]:
           """Create Topic from RSS entry"""
           try:
               title = getattr(entry, 'title', '').strip()
               description = self._extract_description(entry)
               url = getattr(entry, 'link', '').strip()
               
               if not title or not url:
                   return None
               
               # Extract keywords from title and description
               keywords = self._extract_keywords(title, description)
               
               # Determine category based on source metadata or keywords
               category = self._determine_category(keywords, source)
               
               # Parse published date
               published_at = self._parse_published_date(entry)
               
               topic = Topic(
                   title=title,
                   description=description,
                   url=url,
                   source=source.name,
                   keywords=keywords,
                   category=category,
                   discovered_at=published_at or datetime.utcnow(),
                   metadata={
                       'rss_entry_id': getattr(entry, 'id', ''),
                       'author': getattr(entry, 'author', ''),
                       'tags': [tag.term for tag in getattr(entry, 'tags', [])],
                       'source_url': source.url
                   }
               )
               
               return topic
               
           except Exception as e:
               print(f"Error creating topic from RSS entry: {e}")
               return None
       
       def _extract_description(self, entry) -> str:
           """Extract description from RSS entry"""
           # Try multiple description fields
           for field in ['summary', 'description', 'content']:
               content = getattr(entry, field, '')
               if content:
                   if isinstance(content, list) and content:
                       content = content[0]
                   if hasattr(content, 'value'):
                       content = content.value
                   
                   # Strip HTML tags (basic)
                   import re
                   content = re.sub('<[^<]+?>', '', str(content))
                   return content.strip()[:500]  # Limit length
           
           return ""
       
       def _extract_keywords(self, title: str, description: str) -> List[str]:
           """Extract keywords from title and description"""
           import re
           
           text = f"{title} {description}".lower()
           
           # Remove common stop words
           stop_words = {
               'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
               'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
               'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
               'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did'
           }
           
           # Extract words (alphanumeric, 3+ chars)
           words = re.findall(r'\b[a-zA-Z0-9]{3,}\b', text)
           keywords = [word for word in words if word not in stop_words]
           
           # Return top 10 most frequent unique keywords
           from collections import Counter
           word_counts = Counter(keywords)
           return [word for word, count in word_counts.most_common(10)]
       
       def _determine_category(self, keywords: List[str], source: Source) -> TopicCategory:
           """Determine topic category based on keywords and source"""
           # Check source metadata first
           default_category = source.metadata.get('default_category')
           if default_category:
               try:
                   return TopicCategory(default_category)
               except ValueError:
                   pass
           
           # Keyword-based classification
           tech_keywords = {'ai', 'artificial', 'intelligence', 'machine', 'learning', 
                           'python', 'javascript', 'programming', 'software', 'tech', 
                           'algorithm', 'data', 'cloud', 'api', 'framework'}
           
           business_keywords = {'business', 'startup', 'market', 'economy', 'finance',
                               'investment', 'revenue', 'profit', 'company', 'corporate'}
           
           keyword_set = set(keywords)
           
           if keyword_set & tech_keywords:
               return TopicCategory.TECH
           elif keyword_set & business_keywords:
               return TopicCategory.BUSINESS
           
           return TopicCategory.TECH  # Default fallback
       
       def _parse_published_date(self, entry) -> Optional[datetime]:
           """Parse published date from RSS entry"""
           for field in ['published_parsed', 'updated_parsed']:
               time_struct = getattr(entry, field, None)
               if time_struct:
                   try:
                       import time
                       return datetime.fromtimestamp(time.mktime(time_struct))
                   except:
                       pass
           
           return None
   ```

2. **RSS Repository Implementation**
   ```python
   # src/domains/content/infrastructure/repositories/postgresql_topic_repository.py
   import asyncpg
   from typing import List, Optional
   from uuid import UUID
   from datetime import datetime
   
   from ...domain.entities.topic import Topic, TopicStatus, TopicCategory
   from ...domain.repositories.topic_repository import ITopicRepository
   
   class PostgreSQLTopicRepository(ITopicRepository):
       def __init__(self, connection_pool: asyncpg.Pool):
           self.pool = connection_pool
           
       async def save(self, topic: Topic) -> None:
           """Save topic to database"""
           async with self.pool.acquire() as conn:
               await conn.execute("""
                   INSERT INTO topics (
                       id, title, description, url, source, discovered_at,
                       keywords, initial_score, category, status, sentiment, metadata
                   ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                   ON CONFLICT (id) DO UPDATE SET
                       title = EXCLUDED.title,
                       description = EXCLUDED.description,
                       keywords = EXCLUDED.keywords,
                       initial_score = EXCLUDED.initial_score,
                       status = EXCLUDED.status,
                       sentiment = EXCLUDED.sentiment,
                       metadata = EXCLUDED.metadata
               """,
               topic.id, topic.title, topic.description, topic.url,
               topic.source, topic.discovered_at, topic.keywords,
               topic.initial_score, topic.category.value, topic.status.value,
               topic.sentiment, topic.metadata
               )
       
       async def find_by_id(self, topic_id: UUID) -> Optional[Topic]:
           """Find topic by ID"""
           async with self.pool.acquire() as conn:
               row = await conn.fetchrow(
                   "SELECT * FROM topics WHERE id = $1", topic_id
               )
               return self._row_to_topic(row) if row else None
       
       async def find_by_url(self, url: str) -> Optional[Topic]:
           """Find topic by URL"""
           async with self.pool.acquire() as conn:
               row = await conn.fetchrow(
                   "SELECT * FROM topics WHERE url = $1", url
               )
               return self._row_to_topic(row) if row else None
       
       async def find_recent(self, limit: int = 50) -> List[Topic]:
           """Find recent topics"""
           async with self.pool.acquire() as conn:
               rows = await conn.fetch("""
                   SELECT * FROM topics 
                   ORDER BY discovered_at DESC 
                   LIMIT $1
               """, limit)
               return [self._row_to_topic(row) for row in rows]
               
       def _row_to_topic(self, row) -> Topic:
           """Convert database row to Topic entity"""
           return Topic(
               id=row['id'],
               title=row['title'],
               description=row['description'],
               url=row['url'],
               source=row['source'],
               discovered_at=row['discovered_at'],
               keywords=row['keywords'],
               initial_score=row['initial_score'],
               category=TopicCategory(row['category']),
               status=TopicStatus(row['status']),
               sentiment=row['sentiment'],
               metadata=row['metadata']
           )
   ```

3. **Database migration script**
   ```sql
   -- database/migrations/001_create_topics_table.sql
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   
   CREATE TABLE IF NOT EXISTS topics (
       id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
       title VARCHAR(500) NOT NULL,
       description TEXT,
       url VARCHAR(2000) UNIQUE NOT NULL,
       source VARCHAR(200) NOT NULL,
       discovered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
       keywords TEXT[] DEFAULT '{}',
       initial_score DECIMAL(5,4) DEFAULT 0.0,
       category VARCHAR(50) NOT NULL DEFAULT 'technology',
       status VARCHAR(50) NOT NULL DEFAULT 'discovered',
       sentiment DECIMAL(3,2),
       metadata JSONB DEFAULT '{}',
       created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
       updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   
   CREATE INDEX idx_topics_discovered_at ON topics(discovered_at DESC);
   CREATE INDEX idx_topics_source ON topics(source);
   CREATE INDEX idx_topics_status ON topics(status);
   CREATE INDEX idx_topics_category ON topics(category);
   CREATE INDEX idx_topics_url_hash ON topics USING hash(url);
   
   -- Trigger for updated_at
   CREATE OR REPLACE FUNCTION update_updated_at_column()
   RETURNS TRIGGER AS $$
   BEGIN
       NEW.updated_at = NOW();
       RETURN NEW;
   END;
   $$ language 'plpgsql';
   
   CREATE TRIGGER update_topics_updated_at 
       BEFORE UPDATE ON topics 
       FOR EACH ROW 
       EXECUTE FUNCTION update_updated_at_column();
   ```

**Success Criteria**:
- [ ] RSS feeds parsowane correctly
- [ ] Keywords extraction działa
- [ ] Category classification basic
- [ ] Database persistence working
- [ ] Duplicate detection by URL
- [ ] Integration tests passing

---

### Blok 7: Content Scout Agent
**Czas**: 4h | **Agent**: project-coder | **Dependencies**: Blok 6

**Task 2.2**: Content Scout agent z AG-UI events

#### Execution Steps:
1. **CrewAI Content Scout Agent**
   ```python
   # src/domains/content/infrastructure/agents/content_scout_agent.py
   import asyncio
   from typing import List, Dict, Any
   from datetime import datetime
   from crewai import Agent, Task, Crew
   
   from src.shared.domain.events.agui_events import AGUIEvent, AGUIEventType
   from src.shared.infrastructure.agui.event_emitter import AGUIEventEmitter
   from ...domain.entities.topic import Topic
   from ...domain.entities.source import Source
   from ...domain.services.content_discovery_service import ContentDiscoveryService
   from ..services.rss_service import RSSService
   
   class ContentScoutAgent:
       def __init__(
           self, 
           discovery_service: ContentDiscoveryService,
           rss_service: RSSService,
           agui_emitter: AGUIEventEmitter
       ):
           self.discovery_service = discovery_service
           self.rss_service = rss_service
           self.emitter = agui_emitter
           self.agent_id = "content_scout"
           
           # CrewAI Agent definition
           self.agent = Agent(
               role='Content Discovery Specialist',
               goal='Discover and categorize trending topics from multiple sources in real-time',
               backstory="""You are an experienced digital content scout with a keen eye for 
                          emerging trends. You monitor RSS feeds, news sources, and social 
                          platforms to identify topics with viral potential. Your expertise 
                          lies in quickly categorizing content and assessing its relevance 
                          for publication.""",
               verbose=True,
               allow_delegation=False
           )
       
       async def start_discovery_cycle(self, sources_config: Dict[str, Any]) -> List[Topic]:
           """Main discovery cycle with real-time AG-UI events"""
           
           # Emit start event
           await self.emitter.emit(AGUIEvent(
               type=AGUIEventType.PROGRESS_UPDATE,
               data={
                   "stage": "discovery_start",
                   "message": "🔍 Starting content discovery cycle...",
                   "progress": 0,
                   "total_sources": len(sources_config.get('sources', [])),
                   "estimated_duration": "2-3 minutes",
                   "agent_status": "active"
               },
               agent_id=self.agent_id
           ))
           
           try:
               # Discover from all sources
               all_topics = await self.discovery_service.discover_from_all_sources()
               
               # Progress update
               await self.emitter.emit(AGUIEvent(
                   type=AGUIEventType.PROGRESS_UPDATE,
                   data={
                       "stage": "processing_topics",
                       "message": f"📊 Processing {len(all_topics)} discovered topics...",
                       "progress": 50,
                       "topics_found": len(all_topics),
                   },
                   agent_id=self.agent_id
               ))
               
               # Deduplicate topics
               unique_topics = await self.discovery_service.deduplicate_topics(all_topics)
               
               # Emit each unique topic as discovered
               for i, topic in enumerate(unique_topics):
                   await self._emit_topic_discovered(topic, i + 1, len(unique_topics))
                   
                   # Small delay to prevent overwhelming frontend
                   await asyncio.sleep(0.1)
               
               # Final completion event
               await self.emitter.emit(AGUIEvent(
                   type=AGUIEventType.TASK_COMPLETE,
                   data={
                       "stage": "discovery_complete",
                       "message": f"✅ Discovery complete: {len(unique_topics)} unique topics found",
                       "total_topics": len(unique_topics),
                       "duplicates_removed": len(all_topics) - len(unique_topics),
                       "success": True,
                       "duration_seconds": self._calculate_duration()
                   },
                   agent_id=self.agent_id
               ))
               
               return unique_topics
               
           except Exception as e:
               await self._emit_error(str(e))
               raise
       
       async def _emit_topic_discovered(self, topic: Topic, current: int, total: int):
           """Emit topic discovered event with full context"""
           await self.emitter.emit(AGUIEvent(
               type=AGUIEventType.TOPIC_DISCOVERED,
               data={
                   "topic": {
                       "id": str(topic.id),
                       "title": topic.title,
                       "description": topic.description[:200] + "..." if len(topic.description) > 200 else topic.description,
                       "url": topic.url,
                       "source": topic.source,
                       "category": topic.category.value,
                       "keywords": topic.keywords[:5],  # Limit to top 5
                       "discovered_at": topic.discovered_at.isoformat(),
                       "initial_score": topic.initial_score,
                       "status": topic.status.value
                   },
                   "discovery_context": {
                       "current_index": current,
                       "total_topics": total,
                       "progress_percentage": (current / total) * 100,
                       "agent_id": self.agent_id,
                       "discovery_batch_id": str(datetime.utcnow().timestamp())
                   },
                   "analysis_preview": {
                       "category_confidence": 0.85,  # Will be enhanced later
                       "relevance_score": topic.initial_score,
                       "freshness_hours": self._calculate_freshness_hours(topic),
                       "keyword_density": len(topic.keywords)
                   }
               },
               agent_id=self.agent_id
           ))
       
       async def _emit_error(self, error_message: str):
           """Emit error event"""
           await self.emitter.emit(AGUIEvent(
               type=AGUIEventType.MESSAGE,
               data={
                   "level": "error",
                   "message": f"❌ Content discovery error: {error_message}",
                   "timestamp": datetime.utcnow().isoformat(),
                   "agent_id": self.agent_id,
                   "requires_attention": True
               },
               agent_id=self.agent_id
           ))
       
       def _calculate_freshness_hours(self, topic: Topic) -> float:
           """Calculate hours since topic was published"""
           delta = datetime.utcnow() - topic.discovered_at
           return delta.total_seconds() / 3600
       
       def _calculate_duration(self) -> float:
           """Calculate task duration - placeholder"""
           return 120.0  # Will implement proper timing
   
       # CrewAI Task definitions
       def create_discovery_task(self) -> Task:
           """Create CrewAI task for content discovery"""
           return Task(
               description="""
                   Scan configured RSS feeds and news sources to discover new content topics.
                   Focus on technology, business, and science topics with viral potential.
                   Extract key information including title, description, URL, keywords, and category.
                   Ensure discovered topics are fresh (within 24 hours) and relevant.
               """,
               agent=self.agent,
               expected_output="List of discovered topics with metadata and categorization"
           )
   ```

2. **Agent Orchestration Service**
   ```python
   # src/domains/content/application/services/agent_orchestration_service.py
   import asyncio
   from typing import List, Dict, Any
   from datetime import datetime
   
   from ...infrastructure.agents.content_scout_agent import ContentScoutAgent
   from ...domain.entities.topic import Topic
   from src.shared.infrastructure.agui.event_emitter import AGUIEventEmitter
   from src.shared.domain.events.agui_events import AGUIEvent, AGUIEventType
   
   class AgentOrchestrationService:
       def __init__(self, agui_emitter: AGUIEventEmitter):
           self.emitter = agui_emitter
           self.agents = {}
           self.running_tasks = {}
       
       def register_agent(self, agent_id: str, agent: Any) -> None:
           """Register an agent for orchestration"""
           self.agents[agent_id] = agent
       
       async def start_content_discovery(self, config: Dict[str, Any]) -> List[Topic]:
           """Start content discovery orchestration"""
           
           # Emit orchestration start
           await self.emitter.emit(AGUIEvent(
               type=AGUIEventType.STATE_SYNC,
               data={
                   "orchestration_id": str(datetime.utcnow().timestamp()),
                   "stage": "agents_starting",
                   "active_agents": ["content_scout"],
                   "config": config,
                   "message": "🚀 Starting agent orchestration..."
               },
               agent_id="orchestrator"
           ))
           
           # Get Content Scout agent
           content_scout = self.agents.get("content_scout")
           if not content_scout:
               raise ValueError("Content Scout agent not registered")
           
           # Start discovery
           try:
               topics = await content_scout.start_discovery_cycle(config)
               
               # Emit orchestration complete
               await self.emitter.emit(AGUIEvent(
                   type=AGUIEventType.STATE_SYNC,
                   data={
                       "stage": "orchestration_complete",
                       "topics_discovered": len(topics),
                       "success": True,
                       "message": f"✅ Orchestration complete: {len(topics)} topics ready for analysis"
                   },
                   agent_id="orchestrator"
               ))
               
               return topics
               
           except Exception as e:
               await self.emitter.emit(AGUIEvent(
                   type=AGUIEventType.MESSAGE,
                   data={
                       "level": "error",
                       "message": f"❌ Orchestration failed: {str(e)}",
                       "requires_attention": True
                   },
                   agent_id="orchestrator"
               ))
               raise
   ```

3. **API Endpoint dla Content Discovery**
   ```python
   # src/interfaces/api/controllers/content_controller.py
   from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
   from typing import List, Dict, Any
   from dependency_injector.wiring import inject, Provide
   
   from src.domains.content.application.services.agent_orchestration_service import AgentOrchestrationService
   from src.shared.infrastructure.container import Container
   
   router = APIRouter(prefix="/api/content", tags=["content"])
   
   @router.post("/discover")
   @inject
   async def start_discovery(
       background_tasks: BackgroundTasks,
       config: Dict[str, Any] = None,
       orchestration_service: AgentOrchestrationService = Provide[Container.orchestration_service]
   ):
       """Start content discovery process"""
       
       default_config = {
           "sources": [
               {
                   "name": "TechCrunch",
                   "url": "https://techcrunch.com/feed/",
                   "type": "rss",
                   "category": "technology"
               },
               {
                   "name": "Hacker News",
                   "url": "https://hnrss.org/frontpage",
                   "type": "rss", 
                   "category": "technology"
               }
           ],
           "max_topics_per_source": 20,
           "freshness_hours": 24
       }
       
       discovery_config = config or default_config
       
       try:
           # Start discovery in background
           background_tasks.add_task(
               orchestration_service.start_content_discovery,
               discovery_config
           )
           
           return {
               "status": "started",
               "message": "Content discovery started in background",
               "config": discovery_config
           }
           
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))
   
   @router.get("/topics/recent")
   @inject
   async def get_recent_topics(
       limit: int = 50,
       topic_repo = Provide[Container.topic_repository]
   ):
       """Get recently discovered topics"""
       try:
           topics = await topic_repo.find_recent(limit=limit)
           return {
               "topics": [
                   {
                       "id": str(topic.id),
                       "title": topic.title,
                       "description": topic.description[:200],
                       "url": topic.url,
                       "source": topic.source,
                       "category": topic.category.value,
                       "status": topic.status.value,
                       "discovered_at": topic.discovered_at.isoformat(),
                       "keywords": topic.keywords[:5]
                   }
                   for topic in topics
               ],
               "total": len(topics)
           }
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))
   ```

**Success Criteria**:
- [ ] Content Scout agent emituje real-time events
- [ ] TOPIC_DISCOVERED events zawierają pełny context
- [ ] Agent orchestration service działa
- [ ] API endpoints dla discovery dostępne
- [ ] WebSocket events docierają do frontend
- [ ] Error handling i recovery mechanisms

**Deploy Test**: Po ukończeniu, uruchom `/api/content/discover` i sprawdź czy events docierają przez WebSocket