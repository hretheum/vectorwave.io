# CrewAI Integration Guide - AI Kolegium Redakcyjne

## 🚀 Overview

Projekt AI Kolegium Redakcyjne wykorzystuje **CrewAI** jako główny framework do orkiestracji wieloagentowych zespołów AI. CrewAI umożliwia tworzenie autonomicznych agentów współpracujących ze sobą w celu realizacji złożonych zadań redakcyjnych.

## 📦 Jak Instalujemy CrewAI?

**CrewAI to biblioteka Python** - nie forkujemy ani nie klonujemy jej repo. Instalujemy ją jako dependency przez pip:

```bash
# Instalacja podstawowej wersji CrewAI
pip install crewai

# Instalacja z dodatkowymi narzędziami
pip install 'crewai[tools]'

# W naszym projekcie (requirements.txt):
crewai==0.30.11
crewai-tools==0.4.26
```

### Co to oznacza praktycznie?

1. **Nie modyfikujemy kodu CrewAI** - używamy go jako "black box" framework
2. **Importujemy klasy CrewAI** w naszym kodzie:
   ```python
   from crewai import Agent, Task, Crew
   from crewai.tools import tool
   ```
3. **Budujemy na bazie CrewAI** - tworzymy własnych agentów używając klas z biblioteki
4. **Dokumentacja CrewAI**: https://docs.crewai.com/ - to nasza biblia

### Struktura plików w projekcie
```
kolegium/
├── requirements.txt          # Tu jest crewai==0.30.11
├── src/
│   ├── domains/
│   │   ├── content/         # Nasz kod używający CrewAI
│   │   │   └── agents/
│   │   │       └── content_scout.py  # Import: from crewai import Agent
│   │   ├── analytics/
│   │   └── editorial/
│   └── shared/
└── docker-compose.yml       # CrewAI działa w kontenerze
```

## ⚡ WAŻNE: CrewAI Flows dla Decision Making

Po analizie dokumentacji CrewAI, dla systemu decyzyjnego **używamy CrewAI Flows** zamiast podstawowych Crews:

- **Flows** = Deterministyczna kontrola przepływu, routing warunkowy, zarządzanie stanem
- **Crews** = Autonomiczne agenty dla zadań kreatywnych

Szczegóły: [CrewAI Flows Decision System](./CREWAI_FLOWS_DECISION_SYSTEM.md)

## 🏗️ Architektura CrewAI w Projekcie

### 1. Podstawowa Struktura Agenta

```python
from crewai import Agent, Task, Crew
from crewai.tools import tool

class ContentScoutAgent:
    """Przykład agenta wykorzystującego CrewAI"""
    
    def __init__(self, discovery_service, event_emitter):
        self.agent = Agent(
            role="Content Scout",
            goal="Discover trending topics with viral potential",
            backstory="Expert at finding emerging trends across multiple sources",
            verbose=True,
            allow_delegation=False,  # Może delegować zadania do innych agentów
            tools=[
                self.rss_checker_tool,
                self.trend_analyzer_tool,
                self.keyword_extractor_tool
            ]
        )
```

### 2. Definiowanie Narzędzi (Tools)

```python
@tool("Check RSS Feeds")
def rss_checker_tool(category: str = None) -> List[Dict]:
    """Tool dla sprawdzania RSS feeds"""
    # Implementacja sprawdzania RSS
    # Emitowanie AG-UI events
    # Zwracanie odkrytych tematów
    return discovered_topics

@tool("Analyze Trends") 
def trend_analyzer_tool(topic: str) -> Dict[str, Any]:
    """Tool do analizy trendów"""
    # Analiza Google Trends
    # Sentiment analysis
    # Viral potential scoring
    return analysis_results
```

### 3. Tworzenie Zadań (Tasks)

```python
# Pojedyncze zadanie
discovery_task = Task(
    description="Discover trending topics in technology category",
    expected_output="List of 10 trending topics with viral scores",
    agent=content_scout_agent
)

# Zadanie z kontekstem od innego agenta
analysis_task = Task(
    description="Analyze viral potential of discovered topics",
    expected_output="Detailed analysis with recommendations",
    agent=trend_analyst_agent,
    context=[discovery_task]  # Używa output z discovery_task
)
```

### 4. Orkiestracja Multi-Agent (Crew)

```python
class EditorialCrew:
    """Kompletny zespół redakcyjny"""
    
    def __init__(self):
        # Inicjalizacja agentów
        self.content_scout = ContentScoutAgent()
        self.trend_analyst = TrendAnalystAgent()
        self.editorial_strategist = EditorialStrategistAgent()
        self.quality_assessor = QualityAssessorAgent()
        self.decision_coordinator = DecisionCoordinatorAgent()
        
        # Utworzenie Crew
        self.crew = Crew(
            agents=[
                self.content_scout.agent,
                self.trend_analyst.agent,
                self.editorial_strategist.agent,
                self.quality_assessor.agent,
                self.decision_coordinator.agent
            ],
            tasks=[],  # Dynamicznie dodawane
            verbose=True,
            process="sequential"  # lub "hierarchical" dla bardziej złożonych flow
        )
    
    async def process_content_pipeline(self, category: str):
        """Pełny pipeline przetwarzania treści"""
        
        # 1. Discovery Phase
        discovery_task = Task(
            description=f"Find trending topics in {category}",
            agent=self.content_scout.agent
        )
        
        # 2. Analysis Phase (depends on discovery)
        analysis_task = Task(
            description="Analyze viral potential and trends",
            agent=self.trend_analyst.agent,
            context=[discovery_task]
        )
        
        # 3. Editorial Decision (depends on analysis)
        editorial_task = Task(
            description="Make editorial decisions with controversy check",
            agent=self.editorial_strategist.agent,
            context=[analysis_task],
            human_input=True  # Wymaga ludzkiej interwencji dla kontrowersji
        )
        
        # 4. Quality Assessment (parallel with editorial)
        quality_task = Task(
            description="Assess content quality and fact-check",
            agent=self.quality_assessor.agent,
            context=[analysis_task]
        )
        
        # 5. Final Coordination
        coordination_task = Task(
            description="Coordinate final decision and generate report",
            agent=self.decision_coordinator.agent,
            context=[editorial_task, quality_task]
        )
        
        # Update crew tasks
        self.crew.tasks = [
            discovery_task,
            analysis_task,
            editorial_task,
            quality_task,
            coordination_task
        ]
        
        # Execute crew
        result = await self.crew.kickoff_async()
        return result
```

## 🔄 Wzorce Użycia CrewAI

### 1. Sequential Processing
```python
# Agenty wykonują zadania sekwencyjnie
crew = Crew(
    agents=[scout, analyst, editor],
    tasks=[discover, analyze, decide],
    process="sequential"
)
```

### 2. Hierarchical Processing
```python
# Manager agent deleguje zadania do zespołu
crew = Crew(
    agents=[manager, scout, analyst, editor],
    tasks=[coordinate, discover, analyze, decide],
    process="hierarchical",
    manager_llm=OpenAI(model="gpt-4")  # Manager używa mocniejszego modelu
)
```

### 3. Human-in-the-Loop
```python
# Agent czeka na ludzką decyzję
editorial_task = Task(
    description="Review controversial content",
    agent=editor,
    human_input=True,
    human_input_prompt="This content may be controversial. Please review and provide guidance."
)
```

### 4. Parallel Execution
```python
# Zadania wykonywane równolegle
async def parallel_analysis():
    quality_crew = Crew(agents=[quality_assessor], tasks=[quality_check])
    editorial_crew = Crew(agents=[editor], tasks=[editorial_review])
    
    # Uruchom równolegle
    results = await asyncio.gather(
        quality_crew.kickoff_async(),
        editorial_crew.kickoff_async()
    )
    return results
```

## 🛠️ Implementacja w Projekcie

### Phase 2: Content Scout z CrewAI
```python
# src/domains/content/infrastructure/agents/content_scout.py
class ContentScoutAgent:
    def __init__(self):
        self.agent = Agent(
            role="Content Scout",
            tools=[
                self.check_rss_feeds,
                self.monitor_social_media,
                self.extract_keywords
            ]
        )
    
    @tool("Check RSS Feeds")
    def check_rss_feeds(self, category: str):
        # Implementacja z AG-UI events
        await self.event_emitter.emit("TOPIC_DISCOVERED", {...})
        return topics
```

### Phase 3: Editorial Strategist z Human Input
```python
# src/domains/editorial/infrastructure/agents/editorial_strategist.py
class EditorialStrategistAgent:
    def __init__(self):
        self.agent = Agent(
            role="Editorial Strategist",
            goal="Make editorial decisions with human oversight",
            tools=[
                self.controversy_detector,
                self.editorial_guidelines_checker,
                self.decision_maker
            ]
        )
    
    async def process_topic(self, topic: Topic):
        if await self.is_controversial(topic):
            # Emit human input request
            await self.event_emitter.emit("HUMAN_INPUT_REQUEST", {
                "topic_id": topic.id,
                "reason": "Controversial content detected",
                "suggested_action": self.suggest_action(topic)
            })
            
            # Wait for human decision
            human_decision = await self.wait_for_human_input(topic.id)
            return human_decision
        else:
            # Automatic decision
            return self.make_automatic_decision(topic)
```

### Phase 4: Decision Coordinator - Full Orchestration
```python
# src/domains/orchestration/infrastructure/agents/decision_coordinator.py
class DecisionCoordinatorAgent:
    """Koordynuje pracę całego zespołu"""
    
    def __init__(self):
        self.agent = Agent(
            role="Decision Coordinator",
            goal="Orchestrate multi-agent editorial workflow",
            allow_delegation=True,
            tools=[
                self.create_editorial_crew,
                self.monitor_progress,
                self.generate_report
            ]
        )
    
    @tool("Create Editorial Crew")
    def create_editorial_crew(self, topic_batch: List[Topic]):
        """Tworzy dynamiczny crew dla batch processing"""
        
        # Dynamiczne tworzenie zadań
        tasks = []
        for topic in topic_batch:
            tasks.extend([
                Task(
                    description=f"Analyze topic: {topic.title}",
                    agent=self.trend_analyst
                ),
                Task(
                    description=f"Editorial review: {topic.title}",
                    agent=self.editorial_strategist,
                    human_input=topic.is_controversial
                ),
                Task(
                    description=f"Quality check: {topic.title}",
                    agent=self.quality_assessor
                )
            ])
        
        # Utworzenie crew z dynamicznymi zadaniami
        batch_crew = Crew(
            agents=[
                self.trend_analyst,
                self.editorial_strategist,
                self.quality_assessor
            ],
            tasks=tasks,
            process="sequential"
        )
        
        return batch_crew
```

### Phase 5: Dynamic Agent Creation
```python
# src/shared/infrastructure/agents/agent_factory.py
class DynamicAgentFactory:
    """Factory do tworzenia agentów w runtime"""
    
    def create_agent_from_description(self, description: str) -> Agent:
        """Tworzy agenta na podstawie opisu w języku naturalnym"""
        
        # Parse description z LLM
        agent_config = self.parse_agent_description(description)
        
        # Utworzenie dynamicznego agenta
        dynamic_agent = Agent(
            role=agent_config['role'],
            goal=agent_config['goal'],
            backstory=agent_config['backstory'],
            tools=self.resolve_tools(agent_config['required_tools']),
            allow_delegation=agent_config.get('can_delegate', False)
        )
        
        # Rejestracja w systemie
        self.agent_registry.register(dynamic_agent)
        
        return dynamic_agent
    
    def create_dynamic_crew(self, task_description: str) -> Crew:
        """Tworzy crew na podstawie opisu zadania"""
        
        # Analiza zadania
        required_agents = self.analyze_task_requirements(task_description)
        
        # Utworzenie lub pobranie agentów
        agents = []
        for agent_spec in required_agents:
            if existing := self.agent_registry.find(agent_spec):
                agents.append(existing)
            else:
                agents.append(self.create_agent_from_description(agent_spec))
        
        # Utworzenie zadań
        tasks = self.generate_tasks_for_agents(agents, task_description)
        
        # Zwrócenie dynamicznego crew
        return Crew(
            agents=agents,
            tasks=tasks,
            process="hierarchical" if len(agents) > 3 else "sequential"
        )
```

## 📊 Przykłady Użycia

### 1. Prosty Pipeline Discovery
```python
# Uruchomienie content discovery
scout = ContentScoutAgent()
task = Task(
    description="Find AI trending topics",
    agent=scout.agent
)
crew = Crew(agents=[scout.agent], tasks=[task])
topics = crew.kickoff()
```

### 2. Kompleksowy Editorial Workflow
```python
# Pełny workflow redakcyjny
editorial_crew = EditorialCrew()
result = await editorial_crew.process_content_pipeline("technology")

# Result zawiera:
# - Discovered topics
# - Trend analysis
# - Editorial decisions
# - Quality assessments
# - Final recommendations
```

### 3. Dynamiczne Tworzenie Agenta
```python
# User request: "I need an agent that monitors GitHub trending repos"
factory = DynamicAgentFactory()
github_monitor = factory.create_agent_from_description(
    "Create an agent that monitors GitHub trending repositories, "
    "analyzes their potential impact, and suggests content ideas"
)

# Automatycznie utworzony agent z tools:
# - GitHub API integration
# - Trend analysis
# - Content suggestion generator
```

## 🔧 Best Practices

1. **Tool Design**: Każdy tool powinien być atomowy i reużywalny
2. **Event Emission**: Zawsze emituj AG-UI events dla visibility
3. **Error Handling**: Używaj retry logic i graceful degradation
4. **Human Input**: Clearly define kiedy potrzebna jest ludzka interwencja
5. **Performance**: Cache results i używaj parallel execution gdzie możliwe

## 📈 Monitoring i Debugging

```python
# Włącz verbose mode dla debugging
crew = Crew(
    agents=[...],
    tasks=[...],
    verbose=True,  # Pokazuje szczegóły wykonania
    memory=True    # Agenci pamiętają poprzednie interakcje
)

# Custom callbacks dla monitoring
crew.callback_manager.on_task_start = lambda task: 
    event_emitter.emit("CREW_TASK_STARTED", {"task": task.description})

crew.callback_manager.on_task_complete = lambda task, output:
    event_emitter.emit("CREW_TASK_COMPLETED", {"task": task.description, "output": output})
```

## 🚀 Rozszerzenia

### Planowane Features:
1. **Agent Learning**: Agenci uczą się z feedbacku
2. **Dynamic Tool Creation**: Tworzenie tools w runtime
3. **Multi-Language Support**: Agenci w różnych językach
4. **Distributed Execution**: Crews działające na wielu serwerach

---

CrewAI jest sercem systemu AI Kolegium Redakcyjne, umożliwiając skalowalne, elastyczne i inteligentne przetwarzanie treści przez współpracujące zespoły agentów AI.