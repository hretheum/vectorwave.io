# Kompletna Analiza CrewAI dla Vector Wave - AI Kolegium Redakcyjne

## 🎯 Executive Summary

Na podstawie dogłębnej analizy całej dokumentacji CrewAI (https://docs.crewai.com), przedstawiam kompletne rekomendacje implementacji dla projektu Vector Wave - AI Kolegium Redakcyjne. CrewAI to framework do orkiestracji wieloagentowych systemów AI, który idealnie pasuje do naszych potrzeb redakcyjnych.

## 📚 1. Installation & Setup

### 1.1 Project Scaffolding

**Rekomendacja**: Użyj CrewAI CLI do inicjalizacji projektu struktury:

```bash
# Instalacja CrewAI CLI
pip install crewai

# Scaffolding nowego projektu
crewai create kolegium-redakcyjne
cd kolegium-redakcyjne

# Struktura wygenerowana automatycznie:
kolegium-redakcyjne/
├── src/
│   ├── kolegium_redakcyjne/
│   │   ├── __init__.py
│   │   ├── main.py              # Entry point
│   │   ├── crew.py              # Główna definicja crew
│   │   ├── agents.py            # Definicje agentów
│   │   ├── tasks.py             # Definicje zadań
│   │   └── tools/               # Custom tools
│   │       ├── __init__.py
│   │       └── custom_tool.py
├── tests/
├── pyproject.toml
├── README.md
└── .env.example
```

### 1.2 CLI Commands

```bash
# Uruchomienie crew
crewai run

# Trenowanie crew na danych
crewai train

# Replay konkretnej sesji
crewai replay <task_id>

# Testowanie crew
crewai test

# Reset pamięci agentów
crewai reset-memories
```

### 1.3 Environment Setup dla Vector Wave

```bash
# requirements.txt
crewai==0.30.11
crewai-tools==0.4.26
langchain-openai==0.1.7
langchain-anthropic==0.1.15
pydantic==2.6.4
fastapi==0.110.0
uvicorn==0.29.0
redis==5.0.3
postgresql-client==2.5.1
```

```env
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=claude-...
POSTGRES_URL=postgresql://...
REDIS_URL=redis://...
SERPER_API_KEY=...  # Google Search
BROWSERLESS_API_KEY=...  # Web scraping
```

## 📊 2. Core Concepts - Szczegółowa Analiza

### 2.1 Agents - Definicja Agentów Redakcyjnych

**Kluczowe atrybuty agenta**:

```python
from crewai import Agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

class EditorialAgent:
    def __init__(self):
        self.agent = Agent(
            role="Content Scout",                    # Rola w zespole
            goal="Discover trending topics",        # Główny cel
            backstory="""You are an expert content scout with 10 years 
                        of experience in digital media...""",  # Historia/kontekst
            verbose=True,                           # Debugowanie
            allow_delegation=False,                 # Może delegować zadania
            max_iter=5,                            # Max iteracji na zadanie
            max_execution_time=300,                # Timeout w sekundach
            system_template=custom_template,        # Custom prompt template
            llm=ChatOpenAI(model="gpt-4-turbo"),   # Model LLM
            tools=[rss_tool, trend_tool],          # Dostępne narzędzia
            step_callback=self.on_step,            # Callback po każdym kroku
            callbacks=[opentelemetry_callback],    # Lista callbacks
            memory=True,                           # Włącz pamięć agenta
            max_rpm=10,                           # Rate limiting
        )
```

**5 Agentów dla Vector Wave**:

1. **Content Scout** - Discovery agent
2. **Trend Analyst** - Analytics agent  
3. **Editorial Strategist** - Decision agent
4. **Quality Assessor** - QA agent
5. **Decision Coordinator** - Orchestration agent

### 2.2 Tasks - Zadania Atomowe

```python
from crewai import Task

# Zadanie z kontekstem od innych zadań
editorial_task = Task(
    description="""Analyze discovered topics for editorial potential.
                  Consider viral potential, controversy level, and brand fit.""",
    expected_output="""JSON with:
                      - topic_id
                      - editorial_score (0-1)
                      - controversy_level (0-1) 
                      - recommended_action (approve/reject/review)
                      - reasoning""",
    agent=editorial_strategist,
    context=[discovery_task, analysis_task],    # Input z innych zadań
    async_execution=True,                       # Asynchroniczne wykonanie
    output_json=EditorialDecision,              # Pydantic model dla output
    output_pydantic=EditorialDecision,          # Walidacja output
    output_file="editorial_decisions.json",     # Zapis do pliku
    callback=on_editorial_complete,             # Callback po ukończeniu
    human_input=True,                          # Wymaga ludzkiej interwencji
    human_input_prompt="Review controversial content"
)
```

### 2.3 Crews vs Flows - KLUCZOWA DECYZJA

**Rekomendacja**: Użyj **CrewAI Flows** zamiast podstawowych Crews dla systemu decyzyjnego.

| Aspekt | Crews | Flows | Rekomendacja |
|--------|-------|--------|-------------|
| **Kontrola** | Autonomiczne agenty | Deterministyczna | ✅ Flows |
| **Decision Trees** | Brak | Conditional routing | ✅ Flows |
| **Stan** | Ograniczony | Pełne zarządzanie | ✅ Flows |
| **Human-in-Loop** | Podstawowe | Natywne wsparcie | ✅ Flows |
| **Audytowalność** | Podstawowa | Pełna ścieżka | ✅ Flows |

### 2.4 Tools - Narzędzia Agentów

**Built-in Tools CrewAI**:

```python
from crewai_tools import (
    SerperDevTool,      # Google Search
    ScrapeWebsiteTool,  # Web scraping
    FileReadTool,       # File operations
    CodeDocsSearchTool, # Code search
    CSVSearchTool,      # CSV analysis
    DirectoryReadTool,  # Directory browsing
    TXTSearchTool,      # Text search
    JSONSearchTool,     # JSON search
    MDXSearchTool,      # MDX search
    PDFSearchTool,      # PDF search
    PGSearchTool,       # PostgreSQL search
    RagTool,           # RAG search
    ScrapeElementFromWebsiteTool,  # Specific element scraping
    SeleniumScrapingTool,          # Dynamic scraping
    WebsiteSearchTool,             # Website search
    XMLSearchTool,                 # XML search
    YoutubeChannelSearchTool,      # YouTube search
    YoutubeVideoSearchTool         # YouTube video search
)
```

**Custom Tools dla Vector Wave**:

```python
from crewai.tools import tool
from typing import List, Dict, Any

@tool("RSS Feed Monitor")
def rss_feed_monitor(categories: List[str]) -> List[Dict[str, Any]]:
    """Monitor RSS feeds for trending topics"""
    # Implementation with AG-UI events
    discovered_topics = []
    for category in categories:
        topics = fetch_rss_topics(category)
        for topic in topics:
            # Emit AG-UI event
            emit_agui_event("TOPIC_DISCOVERED", {
                "topic_id": topic["id"],
                "title": topic["title"],
                "category": category,
                "source": topic["source"]
            })
            discovered_topics.append(topic)
    return discovered_topics

@tool("Viral Potential Analyzer")
def viral_potential_analyzer(content: str) -> Dict[str, float]:
    """Analyze viral potential using multiple signals"""
    signals = {
        "google_trends": analyze_google_trends(content),
        "social_mentions": count_social_mentions(content),
        "sentiment_score": analyze_sentiment(content),
        "engagement_prediction": predict_engagement(content)
    }
    
    viral_score = calculate_viral_score(signals)
    
    emit_agui_event("VIRAL_ANALYSIS_COMPLETE", {
        "content_hash": hash(content),
        "viral_score": viral_score,
        "signals": signals
    })
    
    return {"viral_score": viral_score, "signals": signals}

@tool("Controversy Detector")
def controversy_detector(content: str) -> Dict[str, Any]:
    """Detect potentially controversial content"""
    controversy_signals = {
        "political_keywords": detect_political_content(content),
        "sensitive_topics": detect_sensitive_topics(content),
        "fact_check_needed": requires_fact_checking(content),
        "bias_score": analyze_bias(content)
    }
    
    controversy_level = calculate_controversy_level(controversy_signals)
    
    if controversy_level > 0.7:
        emit_agui_event("HUMAN_INPUT_REQUEST", {
            "content_hash": hash(content),
            "controversy_level": controversy_level,
            "reason": "High controversy detected",
            "signals": controversy_signals
        })
    
    return {
        "controversy_level": controversy_level,
        "signals": controversy_signals,
        "human_review_required": controversy_level > 0.7
    }
```

### 2.5 Processes - Typy Wykonania

```python
from crewai import Crew

# Sequential - zadania po kolei
crew = Crew(
    agents=[scout, analyst, editor],
    tasks=[discover, analyze, decide],
    process="sequential"
)

# Hierarchical - manager deleguje zadania
crew = Crew(
    agents=[manager, scout, analyst, editor],
    tasks=[coordinate, discover, analyze, decide],
    process="hierarchical",
    manager_llm=ChatOpenAI(model="gpt-4")
)

# Consensual - agenty głosują nad decyzjami
crew = Crew(
    agents=[editor1, editor2, editor3],
    tasks=[review_task],
    process="consensual",
    consensus_threshold=0.7  # 70% zgoda potrzebna
)
```

### 2.6 Memory - System Pamięci

**4 typy pamięci w CrewAI**:

```python
from crewai import Crew

crew = Crew(
    agents=[...],
    tasks=[...],
    # Short-term memory - sesja
    memory=True,
    
    # Long-term memory - persystentna
    memory_type="long_term",
    memory_storage_path="./crew_memory",
    
    # Entity memory - pamięć o encjach
    entity_memory=True,
    
    # Contextual memory - kontekst rozmów
    contextual_memory=True,
    
    # Embedding model dla similarity search
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-3-large"}
    }
)
```

**Konfiguracja dla Vector Wave**:

```python
# Memory storage w PostgreSQL
crew = Crew(
    memory=True,
    memory_type="long_term", 
    memory_config={
        "provider": "postgresql",
        "connection_string": "postgresql://user:pass@localhost/memory_db",
        "table_name": "crew_memory"
    }
)
```

### 2.7 Planning - Planowanie Zadań

```python
from crewai import Crew

# Włącz planning dla złożonych zadań
crew = Crew(
    agents=[...],
    tasks=[...],
    planning=True,
    planning_llm=ChatOpenAI(model="gpt-4")  # Mocniejszy model do planowania
)

# Custom planning strategy
crew = Crew(
    planning=True,
    planning_strategy="step_by_step",  # lub "goal_oriented"
    max_planning_iterations=3
)
```

### 2.8 Knowledge Sources - Baza Wiedzy

```python
from crewai import Crew, LLM
from crewai.knowledge.source import TextFileKnowledgeSource

# Wczytanie bazy wiedzy Vector Wave
knowledge_sources = [
    TextFileKnowledgeSource(
        file_path="./knowledge/vector_wave_guidelines.txt",
        metadata={"type": "editorial_guidelines"}
    ),
    TextFileKnowledgeSource(
        file_path="./knowledge/content_strategies.txt", 
        metadata={"type": "content_strategy"}
    ),
    TextFileKnowledgeSource(
        file_path="./knowledge/controversial_topics.txt",
        metadata={"type": "controversy_detection"}
    )
]

crew = Crew(
    agents=[...],
    tasks=[...],
    knowledge_sources=knowledge_sources,
    knowledge_storage_path="./knowledge_embeddings"
)
```

### 2.9 LLM Configuration

**Multi-provider setup dla Vector Wave**:

```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Primary LLM - OpenAI GPT-4
primary_llm = ChatOpenAI(
    model="gpt-4-turbo",
    temperature=0.1,  # Niskie dla faktów
    max_tokens=4096
)

# Fallback LLM - Claude
fallback_llm = ChatAnthropic(
    model="claude-3-sonnet-20240229",
    temperature=0.2
)

# Specialized LLMs per domain
content_scout_llm = ChatOpenAI(model="gpt-3.5-turbo")  # Szybki do discovery
trend_analyst_llm = ChatOpenAI(model="gpt-4")          # Precyzyjny do analizy
editorial_llm = ChatAnthropic(model="claude-3-opus")   # Przemyślany do decyzji

# Agent z custom LLM
agent = Agent(
    role="Editorial Strategist",
    llm=editorial_llm,
    fallback_llms=[primary_llm, fallback_llm]  # Fallback chain
)
```

### 2.10 Collaboration - Współpraca Agentów

```python
# Agent z możliwością delegacji
coordinator = Agent(
    role="Decision Coordinator",
    allow_delegation=True,
    delegation_enabled=True,
    max_delegation_depth=2  # Max poziom delegacji
)

# Task który może być delegowany
coordination_task = Task(
    description="Coordinate editorial decisions",
    agent=coordinator,
    delegation_allowed=True
)
```

### 2.11 Training - Trenowanie Crew

```python
# Training dataset format
training_data = [
    {
        "inputs": {
            "topic": "AI breakthrough in healthcare",
            "category": "technology"
        },
        "expected_output": {
            "decision": "approve",
            "viral_score": 0.8,
            "reasoning": "High interest, positive sentiment"
        }
    }
]

# Trenowanie crew
crew.train(
    n_iterations=10,
    filename="training_data.json",
    inputs=training_data
)
```

### 2.12 Testing - Testowanie Systemów

```python
# Test framework dla crew
from crewai.testing import CrewTestFramework

test_framework = CrewTestFramework()

# Unit test pojedynczego agenta
@test_framework.test_agent(content_scout)
def test_content_discovery():
    result = content_scout.execute("Find AI trends")
    assert len(result) > 0
    assert all("ai" in topic.lower() for topic in result)

# Integration test całego crew
@test_framework.test_crew(editorial_crew)
def test_editorial_pipeline():
    result = editorial_crew.kickoff(
        inputs={"category": "technology"}
    )
    assert result["decision"] in ["approve", "reject", "review"]
    assert 0 <= result["viral_score"] <= 1
```

## 🏗️ 3. How-to Guides & Best Practices

### 3.1 Agent Design Patterns

**1. Specialist Agent Pattern**:
```python
class SpecialistAgent:
    """Agent wyspecjalizowany w jednym obszarze"""
    def __init__(self, domain: str):
        self.agent = Agent(
            role=f"{domain} Specialist",
            tools=self._get_domain_tools(domain),
            llm=self._get_domain_llm(domain),
            allow_delegation=False  # Nie deleguje - jest ekspertem
        )
```

**2. Coordinator Agent Pattern**:
```python
class CoordinatorAgent:
    """Agent koordynujący pracę innych"""
    def __init__(self):
        self.agent = Agent(
            role="Coordinator",
            allow_delegation=True,
            tools=[
                self.delegate_task_tool,
                self.monitor_progress_tool,
                self.collect_results_tool
            ]
        )
```

**3. Human-in-Loop Agent Pattern**:
```python
class HumanInLoopAgent:
    """Agent wymagający ludzkiej interwencji"""
    def __init__(self):
        self.agent = Agent(
            role="Editorial Reviewer",
            tools=[self.controversy_detector],
            human_input=True,
            human_input_prompt="Review this content for editorial approval"
        )
```

### 3.2 Task Orchestration Patterns

**Sequential with Conditional Routing**:
```python
async def editorial_pipeline():
    # Discovery
    topics = await discovery_task.execute()
    
    # Conditional routing
    if len(topics) > 50:
        # Batch processing
        return await batch_analysis_task.execute(topics)
    else:
        # Individual processing
        return await individual_analysis_task.execute(topics)
```

**Parallel Processing Pattern**:
```python
async def parallel_editorial_review():
    quality_task = Task(description="Quality assessment", agent=quality_agent)
    controversy_task = Task(description="Controversy check", agent=controversy_agent)
    viral_task = Task(description="Viral analysis", agent=viral_agent)
    
    # Execute in parallel
    results = await asyncio.gather(
        quality_task.execute_async(),
        controversy_task.execute_async(), 
        viral_task.execute_async()
    )
    
    return combine_results(results)
```

### 3.3 Error Handling & Resilience

```python
from crewai import Crew
import asyncio

class ResilientCrew:
    def __init__(self):
        self.crew = Crew(
            agents=[...],
            tasks=[...],
            max_retry=3,
            retry_delay=1.0,
            fallback_llm=backup_llm
        )
    
    async def execute_with_fallback(self):
        try:
            return await self.crew.kickoff_async()
        except Exception as e:
            # Log error
            await self.emit_agui_event("CREW_ERROR", {"error": str(e)})
            
            # Fallback to simpler workflow
            return await self.simple_fallback_crew.kickoff_async()
```

## 🚀 4. Vector Wave Implementation Plan

### 4.1 MVP Roadmap z CrewAI Features

**Phase 1: Foundation (Weeks 1-2)**
```bash
# Scaffolding
crewai create ai-kolegium-redakcyjne
cd ai-kolegium-redakcyjne

# Basic crew setup
- [ ] Content Scout agent with RSS tools
- [ ] Basic sequential workflow
- [ ] AG-UI event integration
- [ ] Docker container setup
```

**Phase 2: Core Agents (Weeks 3-4)**
```python
# Implementacja wszystkich 5 agentów
agents = [
    ContentScoutAgent(),      # Discovery
    TrendAnalystAgent(),      # Analytics  
    EditorialStrategistAgent(), # Decisions
    QualityAssessorAgent(),   # QA
    DecisionCoordinatorAgent() # Orchestration
]

# Sequential crew
crew = Crew(agents=agents, process="sequential")
```

**Phase 3: Human-in-Loop (Week 5)**
```python
# Przejście na CrewAI Flows
from crewai.flow.flow import Flow, listen, start, router

class EditorialDecisionFlow(Flow):
    @start()
    async def discover_content(self): ...
    
    @router(analyze_content)
    async def route_by_controversy(self, analysis): 
        if analysis["controversy"] > 0.7:
            return "human_review"
        return "auto_approve"
```

**Phase 4: Production Features (Week 6)**
- Memory integration (PostgreSQL)
- Knowledge sources (editorial guidelines)
- Batch processing flows
- Performance monitoring

**Phase 5: Advanced Features (Week 7)**
- Agent training on historical data
- Dynamic agent creation
- Multi-LLM fallbacks
- Distributed execution

### 4.2 Architektura Docelowa

```
kolegium/
├── src/
│   ├── domains/
│   │   ├── content/
│   │   │   ├── agents/
│   │   │   │   ├── content_scout.py       # CrewAI Agent
│   │   │   │   └── tools/
│   │   │   │       ├── rss_monitor.py     # @tool decorator
│   │   │   │       └── trend_analyzer.py  # Custom tool
│   │   │   ├── flows/
│   │   │   │   └── discovery_flow.py      # CrewAI Flow
│   │   │   └── crews/
│   │   │       └── content_crew.py        # CrewAI Crew
│   │   ├── analytics/
│   │   │   ├── agents/
│   │   │   │   └── trend_analyst.py
│   │   │   └── flows/
│   │   │       └── analysis_flow.py
│   │   ├── editorial/
│   │   │   ├── agents/
│   │   │   │   └── editorial_strategist.py
│   │   │   └── flows/
│   │   │       └── decision_flow.py       # Main editorial flow
│   │   ├── quality/
│   │   │   ├── agents/
│   │   │   │   └── quality_assessor.py
│   │   │   └── tools/
│   │   │       ├── fact_checker.py
│   │   │       └── plagiarism_detector.py
│   │   └── orchestration/
│   │       ├── agents/
│   │       │   └── decision_coordinator.py
│   │       └── flows/
│   │           ├── batch_processing_flow.py
│   │           └── main_editorial_flow.py
│   ├── infrastructure/
│   │   ├── agui/
│   │   │   └── crew_events.py             # AG-UI integration
│   │   ├── llm/
│   │   │   ├── providers.py               # LLM configurations
│   │   │   └── fallbacks.py               # Fallback chains
│   │   └── memory/
│   │       ├── postgresql_store.py        # Memory storage
│   │       └── knowledge_sources.py       # Knowledge integration
│   └── knowledge/
│       ├── editorial_guidelines.txt
│       ├── content_strategies.txt
│       └── controversial_topics.txt
├── tests/
│   ├── unit/
│   │   ├── test_agents.py
│   │   └── test_tools.py
│   ├── integration/
│   │   ├── test_crews.py
│   │   └── test_flows.py
│   └── e2e/
│       └── test_editorial_pipeline.py
├── config/
│   ├── agents.yaml                        # Agent configurations
│   ├── crews.yaml                         # Crew definitions
│   └── knowledge.yaml                     # Knowledge sources
├── docker-compose.yml
├── requirements.txt
└── pyproject.toml
```

### 4.3 Integration z Existing Architecture

**AG-UI Event Integration**:
```python
# src/infrastructure/agui/crew_events.py
from crewai.tools import tool
from src.shared.agui.events import emit_agui_event

@tool("Emit AGUI Event")
def emit_crew_event(event_type: str, data: dict):
    """Emit AG-UI event from CrewAI tools"""
    return emit_agui_event(event_type, data)

# Usage w agent tools
@tool("Content Discovery")
def discover_content():
    topics = fetch_rss_feeds()
    
    # Emit AG-UI event
    emit_crew_event("TOPICS_DISCOVERED", {
        "count": len(topics),
        "topics": topics
    })
    
    return topics
```

**Event Sourcing Integration**:
```python
# src/infrastructure/events/crew_event_store.py
class CrewEventStore:
    async def store_crew_execution(self, crew_result):
        event = CrewExecutionEvent(
            crew_id=crew_result.crew_id,
            agents_used=crew_result.agents,
            tasks_completed=crew_result.tasks,
            execution_time=crew_result.duration,
            final_result=crew_result.output
        )
        await self.event_store.append(event)
```

**Docker Integration**:
```dockerfile
# Dockerfile.kolegium
FROM python:3.11-slim

# CrewAI dependencies
RUN pip install crewai crewai-tools

# Vector Wave specific
COPY requirements.txt .
RUN pip install -r requirements.txt

# App
COPY src/ /app/src/
WORKDIR /app

# CrewAI entry point
CMD ["crewai", "run"]
```

### 4.4 Digital Ocean Deployment

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  kolegium:
    build: 
      context: .
      dockerfile: Dockerfile.kolegium
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - POSTGRES_URL=${POSTGRES_URL}
      - REDIS_URL=${REDIS_URL}
    volumes:
      - ./knowledge:/app/knowledge
      - ./crew_memory:/app/crew_memory
    ports:
      - "8080:8080"
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: crew_memory
      POSTGRES_USER: crew
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## 📈 5. Performance & Monitoring

### 5.1 CrewAI Callbacks dla Monitoring

```python
from crewai import Crew
from opentelemetry import trace

class OpenTelemetryCallback:
    def __init__(self):
        self.tracer = trace.get_tracer(__name__)
    
    def on_task_start(self, task):
        span = self.tracer.start_span(f"crew_task_{task.description}")
        span.set_attribute("agent", task.agent.role)
        
    def on_task_complete(self, task, output):
        span.set_attribute("output_length", len(str(output)))
        span.end()

crew = Crew(
    agents=[...],
    tasks=[...],
    callbacks=[OpenTelemetryCallback()]
)
```

### 5.2 Metrics dla Vector Wave

```python
# Custom metrics dla Prometheus
from prometheus_client import Counter, Histogram, Gauge

crew_tasks_total = Counter(
    'crew_tasks_total',
    'Total number of crew tasks executed',
    ['agent_role', 'task_type', 'status']
)

crew_execution_duration = Histogram(
    'crew_execution_duration_seconds',
    'Time spent executing crew tasks',
    ['agent_role', 'task_type']
)

active_agents = Gauge(
    'active_agents_total',
    'Number of currently active agents'
)
```

## 🔐 6. Security & Compliance

### 6.1 LLM API Key Management

```python
# Secure key rotation
from crewai import LLM
import os
from datetime import datetime, timedelta

class SecureLLMProvider:
    def __init__(self):
        self.key_rotation_interval = timedelta(days=30)
        self.last_rotation = datetime.now()
    
    def get_llm(self):
        if self._should_rotate_key():
            self._rotate_api_key()
        
        return ChatOpenAI(
            api_key=self._get_current_key(),
            request_timeout=30,
            max_retries=3
        )
    
    def _should_rotate_key(self):
        return datetime.now() - self.last_rotation > self.key_rotation_interval
```

### 6.2 Content Safety

```python
@tool("Content Safety Check")
def content_safety_check(content: str) -> Dict[str, Any]:
    """Check content for safety issues"""
    safety_results = {
        "hate_speech": detect_hate_speech(content),
        "harassment": detect_harassment(content), 
        "adult_content": detect_adult_content(content),
        "violence": detect_violence(content)
    }
    
    safety_score = calculate_safety_score(safety_results)
    
    if safety_score < 0.7:
        # Block unsafe content
        emit_agui_event("UNSAFE_CONTENT_DETECTED", {
            "content_hash": hash(content),
            "safety_score": safety_score,
            "violations": safety_results
        })
        
        return {"safe": False, "score": safety_score}
    
    return {"safe": True, "score": safety_score}
```

## 🎯 7. Success Metrics & KPIs

### 7.1 Business KPIs

- **Decision Accuracy**: >85% human approval rate
- **Time to Decision**: <5 minut od discovery do decision  
- **Human Intervention Rate**: 15-25% (optimal dla controversial topics)
- **Content Quality Score**: >80% average quality rating

### 7.2 Technical KPIs

- **Crew Execution Time**: <3 minut dla standardowego workflow
- **Agent Response Time**: <30s per task
- **LLM API Success Rate**: >99.5%
- **Memory Retrieval Speed**: <100ms dla knowledge queries

### 7.3 Quality KPIs

- **Test Coverage**: >85% dla core crew logic
- **Agent Consistency**: <5% variance w decisions dla similar content
- **False Positive Rate**: <10% dla controversy detection

## 🚀 8. Quick Start Implementation

### 8.1 First 3 Steps

```bash
# 1. Project scaffolding
crewai create ai-kolegium-redakcyjne
cd ai-kolegium-redakcyjne

# 2. Install Vector Wave dependencies  
pip install -r ../requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with API keys
```

### 8.2 Minimal Viable Crew

```python
# src/ai_kolegium_redakcyjne/main.py
from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool

# Minimal Content Scout
content_scout = Agent(
    role="Content Scout",
    goal="Find trending topics",
    backstory="Expert at discovering viral content",
    tools=[SerperDevTool()],
    verbose=True
)

# Discovery task
discovery_task = Task(
    description="Find 5 trending topics in AI",
    expected_output="List of 5 trending AI topics with sources",
    agent=content_scout
)

# Minimal crew
crew = Crew(
    agents=[content_scout],
    tasks=[discovery_task],
    verbose=True
)

# Execute
if __name__ == "__main__":
    result = crew.kickoff()
    print(result)
```

### 8.3 Verification Commands

```bash
# Test basic crew
crewai run

# Check agent memory
crewai show-memory

# Run tests
crewai test

# Check crew configuration
crewai validate
```

## 📋 9. Iterative Development Plan

### 9.1 Week-by-Week Roadmap

**Week 1**: Foundation
- [x] CrewAI project scaffolding
- [ ] Basic Content Scout agent  
- [ ] RSS feed integration
- [ ] Docker containerization

**Week 2**: Core Functionality
- [ ] All 5 agents implemented
- [ ] Sequential crew workflow
- [ ] AG-UI event integration
- [ ] Basic testing framework

**Week 3**: Advanced Features
- [ ] CrewAI Flows implementation
- [ ] Human-in-the-loop workflow
- [ ] Memory integration (PostgreSQL)
- [ ] Knowledge sources setup

**Week 4**: Production Ready
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Monitoring & observability
- [ ] Deployment to Digital Ocean

## 💡 10. Key Recommendations

### 10.1 Architecture Decisions

1. **Use CrewAI Flows** instead of basic Crews for decision-making
2. **Implement memory with PostgreSQL** for persistence
3. **Custom tools with AG-UI integration** for event-driven architecture
4. **Multi-LLM setup** with OpenAI primary, Claude fallback
5. **Knowledge sources** for editorial guidelines and strategies

### 10.2 Development Best Practices

1. **Start with Sequential Process** → Migrate to Hierarchical → Eventually Flows
2. **Custom Tools First** → Built-in tools as supplements
3. **Memory from Day 1** → Essential for editorial consistency  
4. **Human-in-Loop Early** → Critical for controversial content
5. **Monitoring Everything** → OpenTelemetry + Prometheus integration

### 10.3 Performance Optimizations

1. **Async Execution** dla parallel tasks
2. **LLM Caching** dla repeated queries
3. **Batch Processing** dla bulk content analysis
4. **Memory Optimization** przez embeddings similarity search
5. **Rate Limiting** per LLM provider

---

## 🎉 Conclusion

CrewAI jest idealnym wyborem dla Vector Wave - AI Kolegium Redakcyjne. Framework zapewnia wszystkie potrzebne features:

- ✅ **Multi-agent orchestration** 
- ✅ **Human-in-the-loop workflows**
- ✅ **Sophisticated memory systems**
- ✅ **Custom tools integration**
- ✅ **Deterministic flows for decisions**
- ✅ **Built-in testing & training**
- ✅ **Production-ready features**

Rekomendowana implementacja w 4 tygodnie z wykorzystaniem CrewAI Flows dla decision-making i pełną integracją z existing Vector Wave architecture przez AG-UI events i Event Sourcing.

**Next Steps**: 
1. Wykonaj project scaffolding
2. Zaimplementuj Content Scout agent
3. Skonfiguruj AG-UI integration
4. Deploy minimal crew na Digital Ocean

CrewAI + Vector Wave = Powerful Editorial AI System! 🚀