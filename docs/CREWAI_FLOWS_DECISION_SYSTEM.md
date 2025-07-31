# CrewAI Flows - Lepsze Rozwiązanie dla Editorial Decision System

## 🚀 Dlaczego Flows zamiast podstawowych Crews?

Po analizie dokumentacji CrewAI, **Flows** są znacznie lepszym wyborem dla naszego systemu decyzyjnego redakcyjnego niż podstawowe Crews.

### Kluczowe Różnice

| Aspekt | Crews | Flows |
|--------|-------|--------|
| **Kontrola** | Autonomiczne agenty | Deterministyczna egzekucja |
| **Decision Making** | Open-ended | Strukturalne drzewa decyzyjne |
| **Stan** | Ograniczony | Pełne zarządzanie stanem |
| **Routing** | Brak | Conditional routing z @router |
| **Audytowalność** | Podstawowa | Pełna ścieżka decyzyjna |

## 🏗️ Architektura Editorial Flow

### 1. Główny Flow Redakcyjny

```python
from crewai.flow.flow import Flow, listen, start, router
from typing import Dict, Any
from pydantic import BaseModel

class EditorialState(BaseModel):
    """Stan przepływu redakcyjnego"""
    topic_id: str
    title: str
    content: str
    viral_score: float = 0.0
    controversy_level: float = 0.0
    quality_score: float = 0.0
    editorial_decision: str = "pending"
    human_review_required: bool = False
    rejection_reason: str = ""

class EditorialDecisionFlow(Flow[EditorialState]):
    """Główny flow decyzyjny dla treści"""
    
    def __init__(self):
        super().__init__()
        self.content_scout = ContentScoutAgent()
        self.trend_analyst = TrendAnalystAgent()
        self.controversy_detector = ControversyDetector()
        self.quality_assessor = QualityAssessorAgent()
    
    @start()
    async def discover_content(self) -> Dict[str, Any]:
        """Start: Odkrywanie nowych treści"""
        topics = await self.content_scout.discover_topics()
        
        # Emituj AG-UI event
        await self.emit_agui_event("TOPICS_DISCOVERED", {
            "count": len(topics),
            "topics": topics
        })
        
        # Zapisz do stanu
        self.state.topic_id = topics[0]["id"]
        self.state.title = topics[0]["title"]
        self.state.content = topics[0]["content"]
        
        return {"topics": topics}
    
    @listen(discover_content)
    async def analyze_viral_potential(self, topics: Dict) -> float:
        """Analiza potencjału viralowego"""
        score = await self.trend_analyst.analyze(self.state.content)
        self.state.viral_score = score
        
        await self.emit_agui_event("VIRAL_ANALYSIS_COMPLETE", {
            "topic_id": self.state.topic_id,
            "score": score
        })
        
        return score
    
    @router(analyze_viral_potential)
    async def route_by_viral_score(self, score: float) -> str:
        """Routing bazujący na viral score"""
        if score < 0.3:
            self.state.rejection_reason = "Low viral potential"
            return "reject"
        elif score > 0.7:
            return "fast_track"
        else:
            return "standard_review"
    
    @listen("reject")
    async def reject_content(self) -> None:
        """Odrzucenie treści"""
        self.state.editorial_decision = "rejected"
        
        await self.emit_agui_event("CONTENT_REJECTED", {
            "topic_id": self.state.topic_id,
            "reason": self.state.rejection_reason
        })
    
    @listen("fast_track")
    async def fast_track_review(self) -> None:
        """Szybka ścieżka dla wysokiego potencjału"""
        # Tylko podstawowe sprawdzenie kontrowersji
        controversy = await self.controversy_detector.quick_check(self.state.content)
        self.state.controversy_level = controversy
        
        if controversy > 0.8:
            self.state.human_review_required = True
            return await self.request_human_review()
        
        self.state.editorial_decision = "approved"
        await self.publish_content()
    
    @listen("standard_review")
    async def standard_review_process(self) -> Dict[str, float]:
        """Standardowy proces review"""
        # Pełna analiza kontrowersji i jakości
        controversy = await self.controversy_detector.deep_analysis(self.state.content)
        quality = await self.quality_assessor.assess(self.state.content)
        
        self.state.controversy_level = controversy
        self.state.quality_score = quality
        
        return {"controversy": controversy, "quality": quality}
    
    @router(standard_review_process)
    async def route_by_review_results(self, results: Dict) -> str:
        """Routing po standardowym review"""
        if results["quality"] < 0.5:
            self.state.rejection_reason = "Quality below threshold"
            return "reject"
        elif results["controversy"] > 0.7:
            return "human_review"
        else:
            return "approve"
    
    @listen("human_review")
    async def request_human_review(self) -> None:
        """Żądanie ludzkiej interwencji"""
        self.state.human_review_required = True
        
        await self.emit_agui_event("HUMAN_INPUT_REQUEST", {
            "topic_id": self.state.topic_id,
            "title": self.state.title,
            "controversy_level": self.state.controversy_level,
            "quality_score": self.state.quality_score,
            "suggested_action": self._suggest_action()
        })
        
        # Czekaj na decyzję człowieka
        human_decision = await self.wait_for_human_input()
        self.state.editorial_decision = human_decision
    
    @listen("approve")
    async def approve_and_publish(self) -> None:
        """Zatwierdzenie i publikacja"""
        self.state.editorial_decision = "approved"
        await self.publish_content()
    
    async def publish_content(self) -> None:
        """Publikacja zatwierdzonej treści"""
        await self.emit_agui_event("CONTENT_APPROVED", {
            "topic_id": self.state.topic_id,
            "title": self.state.title,
            "viral_score": self.state.viral_score,
            "quality_score": self.state.quality_score
        })
        
        # Trigger publikacji na różnych platformach
        await self.trigger_publishing_flow()
```

### 2. Human-in-the-Loop Integration

```python
class HumanReviewFlow(Flow[EditorialState]):
    """Sub-flow dla ludzkiej interwencji"""
    
    @start()
    async def present_for_review(self) -> None:
        """Prezentacja treści do review"""
        # Generuj UI component dla redaktora
        ui_component = self.generate_review_ui()
        
        await self.emit_agui_event("UI_COMPONENT", {
            "type": "editorial_review",
            "component": ui_component,
            "data": {
                "topic": self.state.title,
                "controversy_analysis": self.get_controversy_details(),
                "quality_metrics": self.get_quality_metrics()
            }
        })
    
    @listen(present_for_review)
    async def await_decision(self) -> str:
        """Czekanie na decyzję redaktora"""
        # Timeout 5 minut
        decision = await self.wait_for_event("HUMAN_DECISION", timeout=300)
        
        if decision is None:
            # Brak decyzji - eskalacja
            return await self.escalate_to_senior_editor()
        
        return decision["action"]  # "approve", "reject", "modify"
    
    @router(await_decision)
    async def process_human_decision(self, action: str) -> str:
        """Przetworzenie decyzji człowieka"""
        if action == "approve":
            return "publish"
        elif action == "reject":
            return "archive"
        elif action == "modify":
            return "edit"
    
    @listen("edit")
    async def handle_modifications(self) -> None:
        """Obsługa modyfikacji przez redaktora"""
        modifications = await self.get_modifications()
        self.state.content = modifications["new_content"]
        self.state.title = modifications.get("new_title", self.state.title)
        
        # Ponowna analiza po modyfikacjach
        return "reanalyze"
```

### 3. Batch Processing Flow

```python
class BatchEditorialFlow(Flow):
    """Flow do przetwarzania wielu treści jednocześnie"""
    
    @start()
    async def load_content_batch(self) -> List[Dict]:
        """Załadowanie batcha treści"""
        topics = await self.content_scout.discover_batch(limit=50)
        return topics
    
    @listen(load_content_batch)
    async def parallel_analysis(self, topics: List[Dict]) -> Dict[str, Any]:
        """Równoległa analiza wielu treści"""
        # CrewAI Flows wspierają równoległe wykonanie
        results = await asyncio.gather(*[
            self.analyze_single_topic(topic) for topic in topics
        ])
        
        return {
            "analyzed": len(results),
            "approved": sum(1 for r in results if r["decision"] == "approved"),
            "rejected": sum(1 for r in results if r["decision"] == "rejected"),
            "human_review": sum(1 for r in results if r["requires_human"])
        }
    
    @router(parallel_analysis)
    async def route_batch_results(self, results: Dict) -> str:
        """Routing na podstawie wyników batcha"""
        if results["human_review"] > 5:
            return "alert_editorial_team"
        elif results["approved"] > results["rejected"]:
            return "schedule_publishing"
        else:
            return "review_rejection_patterns"
```

## 🔄 Migracja z Crews do Flows

### Przed (Crews):
```python
# Stary sposób - mniej kontroli
crew = Crew(
    agents=[scout, analyst, editor],
    tasks=[discover, analyze, decide],
    process="sequential"
)
result = crew.kickoff()
```

### Po (Flows):
```python
# Nowy sposób - pełna kontrola przepływu
editorial_flow = EditorialDecisionFlow()
result = await editorial_flow.kickoff()

# Możemy też uruchomić od konkretnego punktu
result = await editorial_flow.analyze_viral_potential(topics)
```

## 🎯 Korzyści dla Systemu Redakcyjnego

1. **Deterministyczne Ścieżki Decyzyjne**
   - Jasno zdefiniowane routing rules
   - Przewidywalne wyniki
   - Łatwe do audytu

2. **Zarządzanie Stanem**
   - Pełny stan procesu w każdym momencie
   - Możliwość wznowienia od dowolnego punktu
   - Persystencja decyzji

3. **Human-in-the-Loop**
   - Natywne wsparcie dla oczekiwania na input
   - Timeout handling
   - Eskalacja do senior editors

4. **Skalowalność**
   - Batch processing
   - Równoległe przetwarzanie
   - Efektywne wykorzystanie zasobów

5. **Integracja z AG-UI**
   - Events emitowane w kluczowych punktach
   - Real-time updates do frontend
   - Generative UI components

## 📊 Przykład Pełnego Przepływu

```python
# Inicjalizacja głównego flow
editorial_system = EditorialDecisionFlow()

# Konfiguracja event handlers
editorial_system.on_event("HUMAN_INPUT_REQUEST", notify_editors)
editorial_system.on_event("CONTENT_APPROVED", trigger_publishing)

# Uruchomienie systemu
async def run_editorial_system():
    while True:
        # Odkrywanie nowych treści co 30 minut
        await editorial_system.kickoff()
        await asyncio.sleep(1800)

# Start
asyncio.run(run_editorial_system())
```

## 🔧 Implementacja w Projekcie

Flows powinny zastąpić podstawowe Crews w następujących miejscach:
1. **Phase 3**: Editorial Strategist → `EditorialDecisionFlow`
2. **Phase 4**: Decision Coordinator → `BatchEditorialFlow`
3. **Phase 5**: Dynamic Agent Creation → `DynamicAgentFlow`

To zapewni nam pełną kontrolę nad procesem decyzyjnym z zachowaniem możliwości AI.