# Enhanced CrewAI Agent Example

## Content Scout z Real-time Events

```python
# src/agents/agui_content_scout.py
from crewai import Agent
from src.agui.events import AGUIEvent, AGUIEventType
from src.agui.emitter import AGUIEventEmitter
from src.tools.web_scraping import WebScrapingTool
from src.tools.rss_feed import RSSFeedTool
from src.tools.social_media import SocialMediaTool
import asyncio
from datetime import datetime

class AGUIContentScout(Agent):
    def __init__(self, agui_emitter: AGUIEventEmitter):
        super().__init__(
            role='Content Scout with Real-time Updates',
            goal='Zbieranie tematów z live updates dla redaktorów',
            backstory='''Jesteś doświadczonym dziennikarzem śledczym z wieloletnim 
                         doświadczeniem w odkrywaniu ciekawych historii. Twoja specjalność
                         to real-time monitoring i błyskawiczne rozpoznawanie potencjału
                         viralowego nowych tematów.''',
            tools=[
                WebScrapingTool(),
                RSSFeedTool(),
                SocialMediaTool(),
            ],
            verbose=True
        )
        self.emitter = agui_emitter
        self.agent_id = "content_scout"
    
    async def discover_topics(self, sources_config: dict):
        """Odkrywanie tematów z real-time updates"""
        
        # Emit start event
        await self.emitter.emit(AGUIEvent(
            type=AGUIEventType.PROGRESS_UPDATE,
            data={
                "stage": "content_discovery_start",
                "message": "🔍 Rozpoczynam skanowanie źródeł...",
                "progress": 0,
                "total_sources": len(sources_config),
                "estimated_duration": "2-3 minuty"
            },
            agent_id=self.agent_id
        ))
```        
        topics_discovered = []
        sources = list(sources_config.keys())
        
        for i, source in enumerate(sources):
            # Emit progress update
            await self.emitter.emit(AGUIEvent(
                type=AGUIEventType.PROGRESS_UPDATE,
                data={
                    "stage": f"scanning_{source.lower().replace(' ', '_')}",
                    "message": f"📡 Skanowanie: {source}",
                    "progress": (i / len(sources)) * 100,
                    "current_source": source,
                    "sources_completed": i,
                    "sources_remaining": len(sources) - i
                },
                agent_id=self.agent_id
            ))
            
            try:
                # Actual topic discovery logic
                new_topics = await self._scan_source(source, sources_config[source])
                
                # Emit each discovered topic in real-time
                for topic in new_topics:
                    await self.emitter.emit(AGUIEvent(
                        type=AGUIEventType.TOPIC_DISCOVERED,
                        data={
                            "topic": {
                                "id": topic.id,
                                "title": topic.title,
                                "description": topic.description,
                                "source": source,
                                "url": topic.url,
                                "discovered_at": datetime.utcnow().isoformat(),
                                "initial_score": topic.initial_score,
                                "category": topic.category,
                                "keywords": topic.keywords,
                                "sentiment": topic.sentiment
                            },
                            "source_info": {
                                "name": source,
                                "reliability_score": sources_config[source].get("reliability", 0.8),
                                "update_frequency": sources_config[source].get("frequency", "hourly")
                            }
                        },
                        agent_id=self.agent_id
                    ))
                    
                    topics_discovered.append(topic)
```