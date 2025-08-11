# PHASE 3: Human-in-the-Loop & Advanced Features

## 📋 Bloki Zadań Atomowych

### Blok 9: Editorial Domain Foundation
**Czas**: 4h | **Agent**: project-coder | **Dependencies**: Phase 2 complete

**Task 3.0**: Editorial domain implementation

#### Execution Steps:
1. **Create editorial domain structure** (lokalnie!)
   ```bash
   cd /Users/hretheum/dev/bezrobocie/vector-wave/kolegium
   mkdir -p src/domains/editorial/{domain/{entities,value_objects,repositories,services},application/{use_cases,handlers,dto},infrastructure/{repositories,services,agents}}
   ```

2. **Define editorial entities**
   ```python
   # src/domains/editorial/domain/entities/editorial_decision.py
   from dataclasses import dataclass
   from datetime import datetime
   from typing import Optional, List
   from uuid import UUID, uuid4
   from enum import Enum
   
   class DecisionType(Enum):
       APPROVE = "approve"
       REJECT = "reject"
       MODIFY = "modify"
       ESCALATE = "escalate"
   
   class ControversyLevel(Enum):
       LOW = "low"
       MEDIUM = "medium"
       HIGH = "high"
       CRITICAL = "critical"
   
   @dataclass
   class EditorialDecision:
       id: UUID
       topic_id: UUID
       decision_type: DecisionType
       reasoning: str
       human_required: bool
       controversy_level: ControversyLevel
       made_by: str  # human or agent id
       made_at: datetime
       guidelines_applied: List[str]
       modifications: Optional[dict] = None
       
       @classmethod
       def create(cls, topic_id: UUID, decision_type: DecisionType,
                  reasoning: str, human_required: bool,
                  controversy_level: ControversyLevel,
                  made_by: str, guidelines: List[str]) -> 'EditorialDecision':
           return cls(
               id=uuid4(),
               topic_id=topic_id,
               decision_type=decision_type,
               reasoning=reasoning,
               human_required=human_required,
               controversy_level=controversy_level,
               made_by=made_by,
               made_at=datetime.utcnow(),
               guidelines_applied=guidelines
           )
   ```

3. **Create editorial guidelines entity**
   ```python
   # src/domains/editorial/domain/entities/editorial_guidelines.py
   from dataclasses import dataclass
   from typing import List, Dict
   from uuid import UUID, uuid4
   
   @dataclass
   class EditorialGuideline:
       id: UUID
       name: str
       description: str
       rules: List[str]
       keywords_to_flag: List[str]
       auto_reject_patterns: List[str]
       requires_human_review: bool
       priority: int
       
       def matches_content(self, content: str) -> bool:
           """Check if content matches any flagged patterns"""
           content_lower = content.lower()
           return any(keyword in content_lower for keyword in self.keywords_to_flag)
   ```

4. **Define repository interfaces**
   ```python
   # src/domains/editorial/domain/repositories/editorial_repository.py
   from abc import ABC, abstractmethod
   from typing import List, Optional
   from uuid import UUID
   
   from ..entities.editorial_decision import EditorialDecision
   from ..entities.editorial_guidelines import EditorialGuideline
   
   class IEditorialDecisionRepository(ABC):
       @abstractmethod
       async def save(self, decision: EditorialDecision) -> None:
           pass
           
       @abstractmethod
       async def find_by_topic_id(self, topic_id: UUID) -> Optional[EditorialDecision]:
           pass
           
       @abstractmethod
       async def find_pending_human_decisions(self) -> List[EditorialDecision]:
           pass
   
   class IEditorialGuidelineRepository(ABC):
       @abstractmethod
       async def find_all_active(self) -> List[EditorialGuideline]:
           pass
           
       @abstractmethod
       async def find_by_priority(self, min_priority: int) -> List[EditorialGuideline]:
           pass
   ```

5. **Create editorial service**
   ```python
   # src/domains/editorial/domain/services/editorial_decision_service.py
   from typing import List, Optional
   from uuid import UUID
   
   from ..entities.editorial_decision import EditorialDecision, DecisionType, ControversyLevel
   from ..entities.editorial_guidelines import EditorialGuideline
   from ..repositories.editorial_repository import IEditorialGuidelineRepository
   
   class EditorialDecisionService:
       def __init__(self, guideline_repo: IEditorialGuidelineRepository):
           self.guideline_repo = guideline_repo
           
       async def evaluate_topic(self, topic_id: UUID, content: str, 
                                title: str) -> tuple[DecisionType, ControversyLevel, bool]:
           """Evaluate topic against editorial guidelines"""
           guidelines = await self.guideline_repo.find_all_active()
           
           controversy_level = ControversyLevel.LOW
           requires_human = False
           decision = DecisionType.APPROVE
           
           for guideline in sorted(guidelines, key=lambda g: g.priority, reverse=True):
               if guideline.matches_content(content) or guideline.matches_content(title):
                   if guideline.requires_human_review:
                       requires_human = True
                       controversy_level = ControversyLevel.HIGH
                   
                   # Check auto-reject patterns
                   for pattern in guideline.auto_reject_patterns:
                       if pattern in content.lower() or pattern in title.lower():
                           decision = DecisionType.REJECT
                           controversy_level = ControversyLevel.CRITICAL
                           break
           
           return decision, controversy_level, requires_human
   ```

**Success Criteria**:
- [ ] Editorial domain entities defined with full typing
- [ ] Repository interfaces following DIP
- [ ] Editorial decision service with guideline evaluation
- [ ] Unit tests for domain logic

---

### Blok 10: Controversy Detection System
**Czas**: 4h | **Agent**: project-coder | **Dependencies**: Blok 9

**Task 3.1**: Controversy detection algorithm

#### Execution Steps:
1. **Create controversy detector service**
   ```python
   # src/domains/editorial/infrastructure/services/controversy_detector.py
   import re
   from typing import List, Dict, Tuple
   import numpy as np
   from dataclasses import dataclass
   
   @dataclass
   class ControversySignal:
       keyword: str
       weight: float
       category: str
   
   class ControversyDetector:
       def __init__(self):
           self.controversy_signals = self._load_controversy_signals()
           self.sensitive_topics = self._load_sensitive_topics()
           
       def _load_controversy_signals(self) -> List[ControversySignal]:
           """Load predefined controversy signals"""
           return [
               # Political
               ControversySignal("election", 0.3, "political"),
               ControversySignal("politician", 0.4, "political"),
               ControversySignal("scandal", 0.8, "political"),
               
               # Social issues
               ControversySignal("discrimination", 0.9, "social"),
               ControversySignal("protest", 0.6, "social"),
               ControversySignal("controversy", 0.7, "social"),
               
               # Health/Science
               ControversySignal("vaccine", 0.5, "health"),
               ControversySignal("climate change", 0.4, "science"),
               ControversySignal("conspiracy", 0.9, "misinformation"),
               
               # Violence/Crime
               ControversySignal("violence", 0.8, "safety"),
               ControversySignal("attack", 0.7, "safety"),
               ControversySignal("terrorism", 0.95, "safety"),
           ]
           
       def _load_sensitive_topics(self) -> Dict[str, float]:
           """Topics that always require review"""
           return {
               "religion": 0.7,
               "race": 0.8,
               "gender": 0.6,
               "sexuality": 0.7,
               "minors": 0.9,
               "death": 0.6,
               "medical": 0.5,
           }
           
       def calculate_controversy_score(self, text: str, title: str) -> Tuple[float, List[str]]:
           """Calculate controversy score and return triggered signals"""
           text_lower = text.lower()
           title_lower = title.lower()
           combined = f"{title_lower} {text_lower}"
           
           score = 0.0
           triggered_signals = []
           
           # Check controversy signals
           for signal in self.controversy_signals:
               if signal.keyword in combined:
                   count = combined.count(signal.keyword)
                   score += signal.weight * min(count, 3)  # Cap at 3 occurrences
                   triggered_signals.append(f"{signal.category}:{signal.keyword}")
                   
           # Check sensitive topics
           for topic, weight in self.sensitive_topics.items():
               if topic in combined:
                   score += weight
                   triggered_signals.append(f"sensitive:{topic}")
                   
           # Check for ALL CAPS (emotional content)
           caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
           if caps_ratio > 0.3:
               score += 0.3
               triggered_signals.append("style:excessive_caps")
               
           # Check for multiple exclamation marks
           if text.count("!") > 3:
               score += 0.2
               triggered_signals.append("style:excessive_exclamation")
               
           # Normalize score to 0-1 range
           normalized_score = min(score / 5.0, 1.0)
           
           return normalized_score, triggered_signals
       
       def get_controversy_level(self, score: float) -> str:
           """Map score to controversy level"""
           if score < 0.2:
               return "low"
           elif score < 0.5:
               return "medium"
           elif score < 0.8:
               return "high"
           else:
               return "critical"
   ```

2. **Create ML-based controversy detector**
   ```python
   # src/domains/editorial/infrastructure/services/ml_controversy_detector.py
   import pickle
   from typing import Optional, Tuple, List
   import numpy as np
   from sklearn.feature_extraction.text import TfidfVectorizer
   from sklearn.ensemble import RandomForestClassifier
   
   class MLControversyDetector:
       def __init__(self, model_path: Optional[str] = None):
           self.vectorizer = None
           self.model = None
           if model_path:
               self.load_model(model_path)
           else:
               # Use simple rule-based until model is trained
               self.fallback_detector = ControversyDetector()
               
       def load_model(self, model_path: str):
           """Load pre-trained model and vectorizer"""
           try:
               with open(f"{model_path}/vectorizer.pkl", "rb") as f:
                   self.vectorizer = pickle.load(f)
               with open(f"{model_path}/model.pkl", "rb") as f:
                   self.model = pickle.load(f)
           except FileNotFoundError:
               print("Model files not found, using fallback detector")
               
       def predict_controversy(self, text: str, title: str) -> Tuple[float, List[str]]:
           """Predict controversy using ML model"""
           if self.model and self.vectorizer:
               combined = f"{title} {text}"
               features = self.vectorizer.transform([combined])
               
               # Get probability of controversy
               proba = self.model.predict_proba(features)[0]
               controversy_score = proba[1]  # Assuming binary classification
               
               # Get feature importance for explainability
               feature_names = self.vectorizer.get_feature_names_out()
               feature_scores = features.toarray()[0]
               
               # Get top contributing words
               top_indices = np.argsort(feature_scores)[-10:]
               triggered_signals = [f"ml:{feature_names[i]}" for i in top_indices if feature_scores[i] > 0]
               
               return controversy_score, triggered_signals
           else:
               # Fallback to rule-based
               return self.fallback_detector.calculate_controversy_score(text, title)
   ```

3. **Create configuration for sensitivity levels**
   ```python
   # src/domains/editorial/infrastructure/config/controversy_config.py
   from pydantic import BaseModel
   from typing import Dict, List
   
   class ControversyConfig(BaseModel):
       """Configuration for controversy detection"""
       
       # Thresholds for human review
       human_review_threshold: float = 0.5
       auto_reject_threshold: float = 0.9
       
       # Category-specific weights
       category_weights: Dict[str, float] = {
           "political": 1.2,
           "social": 1.1,
           "health": 1.0,
           "misinformation": 1.5,
           "safety": 1.3,
       }
       
       # Time-based sensitivity (e.g., elections)
       temporal_sensitivity: Dict[str, float] = {
           "election_period": 1.5,
           "crisis_period": 1.3,
           "normal_period": 1.0,
       }
       
       # Trusted sources that reduce controversy score
       trusted_sources: List[str] = [
           "reuters.com",
           "apnews.com",
           "bbc.com",
           "nature.com",
           "science.org",
       ]
       
       # Keywords that always trigger human review
       always_review_keywords: List[str] = [
           "breaking news",
           "unconfirmed",
           "alleged",
           "rumor",
           "leaked",
       ]
   ```

4. **Integration with editorial service**
   ```python
   # src/domains/editorial/application/use_cases/evaluate_content.py
   from typing import Tuple
   from uuid import UUID
   
   from ...domain.services.editorial_decision_service import EditorialDecisionService
   from ...infrastructure.services.controversy_detector import ControversyDetector
   from ...infrastructure.services.ml_controversy_detector import MLControversyDetector
   from ...infrastructure.config.controversy_config import ControversyConfig
   
   class EvaluateContentUseCase:
       def __init__(self, 
                    editorial_service: EditorialDecisionService,
                    controversy_detector: ControversyDetector,
                    ml_detector: MLControversyDetector,
                    config: ControversyConfig):
           self.editorial_service = editorial_service
           self.controversy_detector = controversy_detector
           self.ml_detector = ml_detector
           self.config = config
           
       async def execute(self, topic_id: UUID, title: str, 
                        content: str, source: str) -> dict:
           """Evaluate content for controversy and editorial decisions"""
           
           # Get rule-based controversy score
           rule_score, rule_signals = self.controversy_detector.calculate_controversy_score(
               content, title
           )
           
           # Get ML-based controversy score
           ml_score, ml_signals = self.ml_detector.predict_controversy(content, title)
           
           # Combine scores (weighted average)
           final_score = (rule_score * 0.4 + ml_score * 0.6)
           
           # Adjust based on source trust
           if any(source in trusted for trusted in self.config.trusted_sources):
               final_score *= 0.7  # Reduce score for trusted sources
               
           # Check always-review keywords
           requires_human = False
           for keyword in self.config.always_review_keywords:
               if keyword in content.lower() or keyword in title.lower():
                   requires_human = True
                   break
                   
           # Determine if human review needed
           if final_score > self.config.human_review_threshold:
               requires_human = True
               
           # Get editorial decision
           decision_type, controversy_level, editorial_human_required = \
               await self.editorial_service.evaluate_topic(topic_id, content, title)
               
           requires_human = requires_human or editorial_human_required
           
           return {
               "topic_id": str(topic_id),
               "controversy_score": final_score,
               "controversy_level": self.controversy_detector.get_controversy_level(final_score),
               "decision_type": decision_type.value,
               "requires_human_review": requires_human,
               "triggered_signals": list(set(rule_signals + ml_signals)),
               "source_trusted": any(source in trusted for trusted in self.config.trusted_sources),
           }
   ```

**Success Criteria**:
- [ ] Rule-based controversy detection implemented
- [ ] ML-ready controversy detection structure
- [ ] Configurable sensitivity levels
- [ ] Integration with editorial decision service
- [ ] Comprehensive unit tests

---

### Blok 11: Editorial Strategist Agent
**Czas**: 4h | **Agent**: project-coder | **Dependencies**: Blok 10

**Task 3.2**: Editorial Strategist agent with human-in-the-loop

#### Execution Steps:
1. **Create Editorial Strategist agent**
   ```python
   # src/domains/editorial/infrastructure/agents/editorial_strategist.py
   from typing import Dict, Any, Optional
   from uuid import UUID
   import asyncio
   from datetime import datetime, timedelta
   
   from crewai import Agent, Task
   from langchain.tools import Tool
   
   from ....shared.domain.events.agui_events import AGUIEvent, AGUIEventType
   from ....shared.infrastructure.agui.event_emitter import AGUIEventEmitter
   from ...application.use_cases.evaluate_content import EvaluateContentUseCase
   from ...domain.entities.editorial_decision import EditorialDecision, DecisionType
   
   class EditorialStrategistAgent(Agent):
       def __init__(self, 
                    event_emitter: AGUIEventEmitter,
                    evaluate_content_use_case: EvaluateContentUseCase,
                    human_timeout_seconds: int = 300):
           
           self.event_emitter = event_emitter
           self.evaluate_content = evaluate_content_use_case
           self.human_timeout = human_timeout_seconds
           self.pending_human_decisions = {}
           
           # Define agent tools
           tools = [
               Tool(
                   name="evaluate_content_controversy",
                   func=self._evaluate_content,
                   description="Evaluate content for controversy and editorial guidelines"
               ),
               Tool(
                   name="request_human_input",
                   func=self._request_human_input,
                   description="Request human input for controversial decisions"
               ),
           ]
           
           super().__init__(
               role="Editorial Strategist",
               goal="Make balanced editorial decisions considering controversy and human input",
               backstory="""You are an experienced editorial strategist who ensures 
               content aligns with editorial guidelines while maintaining journalistic 
               integrity. You know when to escalate decisions to humans.""",
               tools=tools,
               verbose=True
           )
           
       async def _evaluate_content(self, topic_id: str, title: str, 
                                  content: str, source: str) -> Dict[str, Any]:
           """Evaluate content and determine if human input needed"""
           
           # Emit progress event
           await self.event_emitter.emit(AGUIEvent(
               type=AGUIEventType.PROGRESS_UPDATE,
               agent_id=self.role,
               data={
                   "task": "content_evaluation",
                   "status": "evaluating",
                   "topic_id": topic_id
               }
           ))
           
           # Evaluate content
           evaluation = await self.evaluate_content.execute(
               UUID(topic_id), title, content, source
           )
           
           # Emit content analysis event
           await self.event_emitter.emit(AGUIEvent(
               type=AGUIEventType.CONTENT_ANALYSIS,
               agent_id=self.role,
               data={
                   "topic_id": topic_id,
                   "analysis": evaluation,
                   "timestamp": datetime.utcnow().isoformat()
               }
           ))
           
           return evaluation
           
       async def _request_human_input(self, topic_id: str, 
                                     evaluation: Dict[str, Any]) -> Dict[str, Any]:
           """Request human input for controversial content"""
           
           request_id = f"{topic_id}_{datetime.utcnow().timestamp()}"
           
           # Create human input request
           human_request = {
               "request_id": request_id,
               "topic_id": topic_id,
               "type": "editorial_decision",
               "urgency": "high" if evaluation["controversy_level"] == "critical" else "normal",
               "context": {
                   "controversy_score": evaluation["controversy_score"],
                   "controversy_level": evaluation["controversy_level"],
                   "triggered_signals": evaluation["triggered_signals"],
                   "suggested_decision": evaluation["decision_type"],
               },
               "timeout_seconds": self.human_timeout,
               "requested_at": datetime.utcnow().isoformat()
           }
           
           # Store pending request
           self.pending_human_decisions[request_id] = {
               "request": human_request,
               "future": asyncio.Future()
           }
           
           # Emit human input request event
           await self.event_emitter.emit(AGUIEvent(
               type=AGUIEventType.HUMAN_INPUT_REQUEST,
               agent_id=self.role,
               data=human_request
           ))
           
           # Wait for human response with timeout
           try:
               response = await asyncio.wait_for(
                   self.pending_human_decisions[request_id]["future"],
                   timeout=self.human_timeout
               )
               
               # Emit human feedback received event
               await self.event_emitter.emit(AGUIEvent(
                   type=AGUIEventType.HUMAN_FEEDBACK,
                   agent_id=self.role,
                   data={
                       "request_id": request_id,
                       "feedback": response,
                       "response_time": (
                           datetime.utcnow() - 
                           datetime.fromisoformat(human_request["requested_at"])
                       ).total_seconds()
                   }
               ))
               
               return response
               
           except asyncio.TimeoutError:
               # Handle timeout - use automated decision
               timeout_response = {
                   "decision": "auto_approved_on_timeout",
                   "reasoning": f"No human response within {self.human_timeout}s",
                   "modified_by_human": False
               }
               
               await self.event_emitter.emit(AGUIEvent(
                   type=AGUIEventType.HUMAN_FEEDBACK,
                   agent_id=self.role,
                   data={
                       "request_id": request_id,
                       "feedback": timeout_response,
                       "timeout": True
                   }
               ))
               
               return timeout_response
           finally:
               # Clean up pending request
               del self.pending_human_decisions[request_id]
               
       async def process_human_response(self, request_id: str, response: Dict[str, Any]):
           """Process incoming human response"""
           if request_id in self.pending_human_decisions:
               self.pending_human_decisions[request_id]["future"].set_result(response)
               
       async def make_editorial_decision(self, topic: Dict[str, Any]) -> EditorialDecision:
           """Main method to make editorial decision"""
           
           # Evaluate content
           evaluation = await self._evaluate_content(
               topic["id"], 
               topic["title"], 
               topic["content"], 
               topic["source"]
           )
           
           # Determine if human input needed
           if evaluation["requires_human_review"]:
               human_response = await self._request_human_input(topic["id"], evaluation)
               
               # Create decision based on human input
               decision = EditorialDecision.create(
                   topic_id=UUID(topic["id"]),
                   decision_type=DecisionType(human_response["decision"]),
                   reasoning=human_response["reasoning"],
                   human_required=True,
                   controversy_level=evaluation["controversy_level"],
                   made_by=human_response.get("reviewer_id", "human"),
                   guidelines=evaluation.get("triggered_signals", [])
               )
           else:
               # Automated decision
               decision = EditorialDecision.create(
                   topic_id=UUID(topic["id"]),
                   decision_type=DecisionType(evaluation["decision_type"]),
                   reasoning=f"Automated decision based on controversy score: {evaluation['controversy_score']}",
                   human_required=False,
                   controversy_level=evaluation["controversy_level"],
                   made_by=self.role,
                   guidelines=evaluation.get("triggered_signals", [])
               )
               
           # Emit editorial decision event
           await self.event_emitter.emit(AGUIEvent(
               type=AGUIEventType.EDITORIAL_DECISION,
               agent_id=self.role,
               data={
                   "topic_id": str(decision.topic_id),
                   "decision": decision.decision_type.value,
                   "controversy_level": decision.controversy_level.value,
                   "human_involved": decision.human_required,
                   "reasoning": decision.reasoning,
                   "made_at": decision.made_at.isoformat()
               }
           ))
           
           return decision
   ```

2. **Create human input handler**
   ```python
   # src/interfaces/api/controllers/human_input_controller.py
   from fastapi import APIRouter, HTTPException, Depends
   from pydantic import BaseModel
   from typing import Dict, Any, Optional
   from datetime import datetime
   
   from dependency_injector.wiring import inject, Provide
   
   from src.domains.editorial.infrastructure.agents.editorial_strategist import EditorialStrategistAgent
   from src.shared.infrastructure.container import Container
   
   router = APIRouter(prefix="/api/human-input", tags=["human-input"])
   
   class HumanDecisionRequest(BaseModel):
       request_id: str
       decision: str  # approve, reject, modify, escalate
       reasoning: str
       modifications: Optional[Dict[str, Any]] = None
       reviewer_id: str
       reviewer_name: str
   
   router.post("/editorial-decision")
   @inject
   async def submit_editorial_decision(
       request: HumanDecisionRequest,
       editorial_agent: EditorialStrategistAgent = Provide[Container.editorial_strategist_agent]
   ):
       """Submit human decision for editorial review"""
       
       try:
           response = {
               "decision": request.decision,
               "reasoning": request.reasoning,
               "modified_by_human": True,
               "reviewer_id": request.reviewer_id,
               "reviewer_name": request.reviewer_name,
               "reviewed_at": datetime.utcnow().isoformat(),
               "modifications": request.modifications
           }
           
           await editorial_agent.process_human_response(request.request_id, response)
           
           return {
               "status": "success",
               "message": "Decision submitted successfully",
               "request_id": request.request_id
           }
           
       except Exception as e:
           raise HTTPException(status_code=400, detail=str(e))
   
   router.get("/pending-decisions")
   @inject
   async def get_pending_decisions(
       editorial_agent: EditorialStrategistAgent = Provide[Container.editorial_strategist_agent]
   ):
       """Get all pending human decisions"""
       
       pending = []
       for request_id, data in editorial_agent.pending_human_decisions.items():
           pending.append({
               "request_id": request_id,
               **data["request"]
           })
           
       return {
           "count": len(pending),
           "decisions": pending
       }
   ```

3. **Create agent task definitions**
   ```python
   # src/domains/editorial/infrastructure/agents/tasks.py
   from crewai import Task
   from typing import Dict, Any
   
   def create_editorial_review_task(agent, topic: Dict[str, Any]) -> Task:
       """Create editorial review task"""
       return Task(
           description=f"""
           Review the following content for editorial approval:
           
           Title: {topic['title']}
           Source: {topic['source']}
           Content: {topic['content'][:500]}...
           
           Evaluate for:
           1. Controversy level and sensitive topics
           2. Alignment with editorial guidelines
           3. Factual accuracy concerns
           4. Need for human review
           
           Make a decision: approve, reject, modify, or escalate
           """,
           agent=agent,
           expected_output="""
           A comprehensive editorial decision including:
           - Decision type (approve/reject/modify/escalate)
           - Controversy assessment
           - Reasoning for the decision
           - Whether human review is needed
           - Any recommended modifications
           """
       )
   ```

4. **Integration with AG-UI event system**
   ```python
   # src/domains/editorial/infrastructure/services/editorial_event_handler.py
   from typing import Dict, Any
   import asyncio
   
   from ....shared.domain.events.agui_events import AGUIEvent, AGUIEventType
   from ....shared.infrastructure.agui.event_emitter import AGUIEventEmitter
   
   class EditorialEventHandler:
       def __init__(self, event_emitter: AGUIEventEmitter):
           self.event_emitter = event_emitter
           self.setup_event_handlers()
           
       def setup_event_handlers(self):
           """Setup event handlers for editorial events"""
           
           # Subscribe to topic discovered events
           asyncio.create_task(
               self.event_emitter.subscribe(
                   AGUIEventType.TOPIC_DISCOVERED.value,
                   self.handle_topic_discovered
               )
           )
           
           # Subscribe to human feedback events
           asyncio.create_task(
               self.event_emitter.subscribe(
                   AGUIEventType.HUMAN_FEEDBACK.value,
                   self.handle_human_feedback
               )
           )
           
       async def handle_topic_discovered(self, event: AGUIEvent):
           """Handle new topic for editorial review"""
           topic_data = event.data
           
           # Log for monitoring
           print(f"Editorial: New topic discovered - {topic_data.get('title', 'Unknown')}")
           
           # Additional processing can be added here
           
       async def handle_human_feedback(self, event: AGUIEvent):
           """Handle human feedback events"""
           feedback_data = event.data
           
           # Emit UI update for feedback received
           await self.event_emitter.emit(AGUIEvent(
               type=AGUIEventType.UI_UPDATE,
               agent_id="editorial_event_handler",
               data={
                   "component": "pending_decisions",
                   "action": "remove",
                   "request_id": feedback_data.get("request_id")
               }
           ))
   ```

**Success Criteria**:
- [ ] Editorial Strategist agent with CrewAI integration
- [ ] Human-in-the-loop workflow implemented
- [ ] Timeout handling for human decisions
- [ ] API endpoints for human input
- [ ] Full AG-UI event integration
- [ ] Integration tests for human interaction flow

---

### Blok 12: Human Input UI Components
**Czas**: 4h | **Agent**: project-coder | **Dependencies**: Blok 11

**Task 3.3**: Human input UI components

#### Execution Steps:
1. **Create pending decisions panel component**
   ```typescript
   // frontend/src/components/editorial/PendingDecisionsPanel.tsx
   import React, { useState, useEffect } from 'react';
   import { useAGUIConnection } from '../../hooks/useAGUIConnection';
   import { AGUIEventType } from '../../types/agui';
   import { DecisionCard } from './DecisionCard';
   import { Badge } from '../ui/Badge';
   
   interface PendingDecision {
     request_id: string;
     topic_id: string;
     type: string;
     urgency: 'high' | 'normal' | 'low';
     context: {
       controversy_score: number;
       controversy_level: string;
       triggered_signals: string[];
       suggested_decision: string;
     };
     timeout_seconds: number;
     requested_at: string;
   }
   
   export const PendingDecisionsPanel: React.FC = () => {
     const [decisions, setDecisions] = useState<PendingDecision[]>([]);
     const [loading, setLoading] = useState(true);
     const { subscribe, unsubscribe } = useAGUIConnection();
     
     useEffect(() => {
       // Fetch initial pending decisions
       fetchPendingDecisions();
       
       // Subscribe to human input requests
       const handleHumanInputRequest = (event: any) => {
         if (event.type === AGUIEventType.HUMAN_INPUT_REQUEST) {
           setDecisions(prev => [...prev, event.data as PendingDecision]);
         }
       };
       
       // Subscribe to UI updates (for removing completed decisions)
       const handleUIUpdate = (event: any) => {
         if (event.type === AGUIEventType.UI_UPDATE && 
             event.data.component === 'pending_decisions' &&
             event.data.action === 'remove') {
           setDecisions(prev => 
             prev.filter(d => d.request_id !== event.data.request_id)
           );
         }
       };
       
       subscribe(AGUIEventType.HUMAN_INPUT_REQUEST, handleHumanInputRequest);
       subscribe(AGUIEventType.UI_UPDATE, handleUIUpdate);
       
       return () => {
         unsubscribe(AGUIEventType.HUMAN_INPUT_REQUEST, handleHumanInputRequest);
         unsubscribe(AGUIEventType.UI_UPDATE, handleUIUpdate);
       };
     }, [subscribe, unsubscribe]);
     
     const fetchPendingDecisions = async () => {
       try {
         const response = await fetch('/api/human-input/pending-decisions');
         const data = await response.json();
         setDecisions(data.decisions);
       } catch (error) {
         console.error('Failed to fetch pending decisions:', error);
       } finally {
         setLoading(false);
       }
     };
     
     const handleDecisionSubmit = async (requestId: string) => {
       // Remove from local state immediately for better UX
       setDecisions(prev => prev.filter(d => d.request_id !== requestId));
     };
     
     const getUrgencyColor = (urgency: string) => {
       switch (urgency) {
         case 'high': return 'red';
         case 'normal': return 'yellow';
         case 'low': return 'green';
         default: return 'gray';
       }
     };
     
     if (loading) {
       return (
         <div className="flex items-center justify-center h-64">
           <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
         </div>
       );
     }
     
     return (
       <div className="space-y-4">
         <div className="flex items-center justify-between mb-6">
           <h2 className="text-2xl font-bold text-gray-900">
             Pending Editorial Decisions
           </h2>
           <Badge variant="primary" size="lg">
             {decisions.length} Pending
           </Badge>
         </div>
         
         {decisions.length === 0 ? (
           <div className="text-center py-12 bg-gray-50 rounded-lg">
             <p className="text-gray-500">No pending decisions at the moment</p>
           </div>
         ) : (
           <div className="grid gap-4">
             {decisions
               .sort((a, b) => {
                 // Sort by urgency then by time
                 const urgencyOrder = { high: 0, normal: 1, low: 2 };
                 const urgencyDiff = urgencyOrder[a.urgency] - urgencyOrder[b.urgency];
                 if (urgencyDiff !== 0) return urgencyDiff;
                 return new Date(a.requested_at).getTime() - new Date(b.requested_at).getTime();
               })
               .map(decision => (
                 <DecisionCard
                   key={decision.request_id}
                   decision={decision}
                   onSubmit={handleDecisionSubmit}
                 />
               ))}
           </div>
         )}
       </div>
     );
   };
   ```

2. **Create decision card component**
   ```typescript
   // frontend/src/components/editorial/DecisionCard.tsx
   import React, { useState, useEffect } from 'react';
   import { formatDistanceToNow } from 'date-fns';
   import { AlertTriangle, Clock, CheckCircle, XCircle, Edit } from 'lucide-react';
   import { Button } from '../ui/Button';
   import { Textarea } from '../ui/Textarea';
   import { Badge } from '../ui/Badge';
   import { Progress } from '../ui/Progress';
   
   interface DecisionCardProps {
     decision: {
       request_id: string;
       topic_id: string;
       urgency: 'high' | 'normal' | 'low';
       context: {
         controversy_score: number;
         controversy_level: string;
         triggered_signals: string[];
         suggested_decision: string;
       };
       timeout_seconds: number;
       requested_at: string;
     };
     onSubmit: (requestId: string) => void;
   }
   
   export const DecisionCard: React.FC<DecisionCardProps> = ({ decision, onSubmit }) => {
     const [selectedDecision, setSelectedDecision] = useState<string>('');
     const [reasoning, setReasoning] = useState('');
     const [timeRemaining, setTimeRemaining] = useState(0);
     const [submitting, setSubmitting] = useState(false);
     
     useEffect(() => {
       // Calculate time remaining
       const timer = setInterval(() => {
         const elapsed = Date.now() - new Date(decision.requested_at).getTime();
         const remaining = Math.max(0, decision.timeout_seconds * 1000 - elapsed);
         setTimeRemaining(remaining);
         
         if (remaining === 0) {
           clearInterval(timer);
         }
       }, 1000);
       
       return () => clearInterval(timer);
     }, [decision.requested_at, decision.timeout_seconds]);
     
     const handleSubmit = async () => {
       if (!selectedDecision || !reasoning.trim()) {
         alert('Please select a decision and provide reasoning');
         return;
       }
       
       setSubmitting(true);
       
       try {
         const response = await fetch('/api/human-input/editorial-decision', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({
             request_id: decision.request_id,
             decision: selectedDecision,
             reasoning: reasoning,
             reviewer_id: 'current_user_id', // TODO: Get from auth context
             reviewer_name: 'Current User', // TODO: Get from auth context
           }),
         });
         
         if (response.ok) {
           onSubmit(decision.request_id);
         } else {
           throw new Error('Failed to submit decision');
         }
       } catch (error) {
         console.error('Error submitting decision:', error);
         alert('Failed to submit decision. Please try again.');
       } finally {
         setSubmitting(false);
       }
     };
     
     const getControversyColor = (level: string) => {
       switch (level) {
         case 'critical': return 'text-red-600 bg-red-50';
         case 'high': return 'text-orange-600 bg-orange-50';
         case 'medium': return 'text-yellow-600 bg-yellow-50';
         case 'low': return 'text-green-600 bg-green-50';
         default: return 'text-gray-600 bg-gray-50';
       }
     };
     
     const timeRemainingMinutes = Math.floor(timeRemaining / 60000);
     const timeRemainingSeconds = Math.floor((timeRemaining % 60000) / 1000);
     const timeProgress = (timeRemaining / (decision.timeout_seconds * 1000)) * 100;
     
     return (
       <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
         {/* Header */}
         <div className="flex items-start justify-between mb-4">
           <div className="flex items-center space-x-3">
             <AlertTriangle className={`h-6 w-6 ${
               decision.urgency === 'high' ? 'text-red-500' : 'text-yellow-500'
             }`} />
             <div>
               <h3 className="text-lg font-semibold">Editorial Review Required</h3>
               <p className="text-sm text-gray-500">
                 Requested {formatDistanceToNow(new Date(decision.requested_at))} ago
               </p>
             </div>
           </div>
           <Badge variant={decision.urgency === 'high' ? 'danger' : 'warning'}>
             {decision.urgency.toUpperCase()} Priority
           </Badge>
         </div>
         
         {/* Time remaining */}
         <div className="mb-4">
           <div className="flex items-center justify-between text-sm mb-1">
             <span className="flex items-center text-gray-600">
               <Clock className="h-4 w-4 mr-1" />
               Time Remaining
             </span>
             <span className={timeRemainingMinutes < 1 ? 'text-red-600 font-semibold' : ''}>
               {timeRemainingMinutes}:{timeRemainingSeconds.toString().padStart(2, '0')}
             </span>
           </div>
           <Progress value={timeProgress} className="h-2" />
         </div>
         
         {/* Controversy info */}
         <div className="mb-4 p-4 bg-gray-50 rounded-lg">
           <div className="flex items-center justify-between mb-2">
             <span className="text-sm font-medium">Controversy Assessment</span>
             <span className={`px-2 py-1 rounded text-xs font-semibold ${
               getControversyColor(decision.context.controversy_level)
             }`}>
               {decision.context.controversy_level.toUpperCase()}
             </span>
           </div>
           <div className="text-sm text-gray-600">
             Score: {(decision.context.controversy_score * 100).toFixed(0)}%
           </div>
         </div>
         
         {/* Triggered signals */}
         {decision.context.triggered_signals.length > 0 && (
           <div className="mb-4">
             <p className="text-sm font-medium mb-2">Triggered Signals:</p>
             <div className="flex flex-wrap gap-2">
               {decision.context.triggered_signals.map((signal, idx) => (
                 <Badge key={idx} variant="secondary" size="sm">
                   {signal}
                 </Badge>
               ))}
             </div>
           </div>
         )}
         
         {/* AI suggestion */}
         <div className="mb-4 p-3 bg-blue-50 rounded-lg">
           <p className="text-sm">
             <span className="font-medium">AI Suggestion:</span>{' '}
             <span className="capitalize">{decision.context.suggested_decision}</span>
           </p>
         </div>
         
         {/* Decision buttons */}
         <div className="mb-4">
           <p className="text-sm font-medium mb-2">Your Decision:</p>
           <div className="grid grid-cols-4 gap-2">
             <Button
               variant={selectedDecision === 'approve' ? 'primary' : 'outline'}
               size="sm"
               onClick={() => setSelectedDecision('approve')}
               className="flex items-center justify-center"
             >
               <CheckCircle className="h-4 w-4 mr-1" />
               Approve
             </Button>
             <Button
               variant={selectedDecision === 'reject' ? 'danger' : 'outline'}
               size="sm"
               onClick={() => setSelectedDecision('reject')}
               className="flex items-center justify-center"
             >
               <XCircle className="h-4 w-4 mr-1" />
               Reject
             </Button>
             <Button
               variant={selectedDecision === 'modify' ? 'warning' : 'outline'}
               size="sm"
               onClick={() => setSelectedDecision('modify')}
               className="flex items-center justify-center"
             >
               <Edit className="h-4 w-4 mr-1" />
               Modify
             </Button>
             <Button
               variant={selectedDecision === 'escalate' ? 'secondary' : 'outline'}
               size="sm"
               onClick={() => setSelectedDecision('escalate')}
             >
               Escalate
             </Button>
           </div>
         </div>
         
         {/* Reasoning textarea */}
         <div className="mb-4">
           <label className="block text-sm font-medium mb-2">
             Reasoning (Required)
           </label>
           <Textarea
             value={reasoning}
             onChange={(e) => setReasoning(e.target.value)}
             placeholder="Provide reasoning for your decision..."
             rows={3}
             className="w-full"
           />
         </div>
         
         {/* Submit button */}
         <Button
           variant="primary"
           className="w-full"
           onClick={handleSubmit}
           disabled={!selectedDecision || !reasoning.trim() || submitting}
         >
           {submitting ? 'Submitting...' : 'Submit Decision'}
         </Button>
       </div>
     );
   };
   ```

3. **Create real-time notifications component**
   ```typescript
   // frontend/src/components/editorial/NotificationToast.tsx
   import React, { useEffect, useState } from 'react';
   import { useAGUIConnection } from '../../hooks/useAGUIConnection';
   import { AGUIEventType } from '../../types/agui';
   import { X, AlertCircle, CheckCircle, Info } from 'lucide-react';
   
   interface Notification {
     id: string;
     type: 'info' | 'success' | 'warning' | 'error';
     title: string;
     message: string;
     timestamp: Date;
   }
   
   export const NotificationToast: React.FC = () => {
     const [notifications, setNotifications] = useState<Notification[]>([]);
     const { subscribe, unsubscribe } = useAGUIConnection();
     
     useEffect(() => {
       const handleHumanInputRequest = (event: any) => {
         if (event.type === AGUIEventType.HUMAN_INPUT_REQUEST) {
           const urgency = event.data.urgency;
           addNotification({
             type: urgency === 'high' ? 'warning' : 'info',
             title: 'Editorial Review Required',
             message: `New ${urgency} priority decision requested`,
           });
         }
       };
       
       const handleEditorialDecision = (event: any) => {
         if (event.type === AGUIEventType.EDITORIAL_DECISION) {
           if (event.data.human_involved) {
             addNotification({
               type: 'success',
               title: 'Decision Made',
               message: `Editorial decision: ${event.data.decision}`,
             });
           }
         }
       };
       
       subscribe(AGUIEventType.HUMAN_INPUT_REQUEST, handleHumanInputRequest);
       subscribe(AGUIEventType.EDITORIAL_DECISION, handleEditorialDecision);
       
       return () => {
         unsubscribe(AGUIEventType.HUMAN_INPUT_REQUEST, handleHumanInputRequest);
         unsubscribe(AGUIEventType.EDITORIAL_DECISION, handleEditorialDecision);
       };
     }, [subscribe, unsubscribe]);
     
     const addNotification = (notification: Omit<Notification, 'id' | 'timestamp'>) => {
       const newNotification: Notification = {
         ...notification,
         id: Date.now().toString(),
         timestamp: new Date(),
       };
       
       setNotifications(prev => [...prev, newNotification]);
       
       // Auto-remove after 5 seconds
       setTimeout(() => {
         removeNotification(newNotification.id);
       }, 5000);
     };
     
     const removeNotification = (id: string) => {
       setNotifications(prev => prev.filter(n => n.id !== id));
     };
     
     const getIcon = (type: string) => {
       switch (type) {
         case 'success': return <CheckCircle className="h-5 w-5 text-green-500" />;
         case 'warning': return <AlertCircle className="h-5 w-5 text-yellow-500" />;
         case 'error': return <AlertCircle className="h-5 w-5 text-red-500" />;
         default: return <Info className="h-5 w-5 text-blue-500" />;
       }
     };
     
     const getStyles = (type: string) => {
       switch (type) {
         case 'success': return 'bg-green-50 border-green-200';
         case 'warning': return 'bg-yellow-50 border-yellow-200';
         case 'error': return 'bg-red-50 border-red-200';
         default: return 'bg-blue-50 border-blue-200';
       }
     };
     
     return (
       <div className="fixed bottom-4 right-4 z-50 space-y-2">
         {notifications.map(notification => (
           <div
             key={notification.id}
             className={`flex items-start p-4 rounded-lg shadow-lg border ${
               getStyles(notification.type)
             } max-w-sm animate-slide-in-right`}
           >
             <div className="flex-shrink-0">
               {getIcon(notification.type)}
             </div>
             <div className="ml-3 flex-1">
               <p className="text-sm font-medium text-gray-900">
                 {notification.title}
               </p>
               <p className="text-sm text-gray-600">
                 {notification.message}
               </p>
             </div>
             <button
               onClick={() => removeNotification(notification.id)}
               className="ml-4 flex-shrink-0"
             >
               <X className="h-4 w-4 text-gray-400 hover:text-gray-600" />
             </button>
           </div>
         ))}
       </div>
     );
   };
   ```

4. **Create decision history view**
   ```typescript
   // frontend/src/components/editorial/DecisionHistory.tsx
   import React, { useState, useEffect } from 'react';
   import { format } from 'date-fns';
   import { User, Bot, Clock, AlertTriangle } from 'lucide-react';
   import { Badge } from '../ui/Badge';
   
   interface HistoricalDecision {
     id: string;
     topic_id: string;
     topic_title: string;
     decision_type: string;
     reasoning: string;
     human_required: boolean;
     controversy_level: string;
     made_by: string;
     made_at: string;
     guidelines_applied: string[];
   }
   
   export const DecisionHistory: React.FC = () => {
     const [decisions, setDecisions] = useState<HistoricalDecision[]>([]);
     const [loading, setLoading] = useState(true);
     const [filter, setFilter] = useState<'all' | 'human' | 'automated'>('all');
     
     useEffect(() => {
       fetchDecisionHistory();
     }, []);
     
     const fetchDecisionHistory = async () => {
       try {
         const response = await fetch('/api/editorial/decisions/history');
         const data = await response.json();
         setDecisions(data.decisions);
       } catch (error) {
         console.error('Failed to fetch decision history:', error);
       } finally {
         setLoading(false);
       }
     };
     
     const filteredDecisions = decisions.filter(decision => {
       if (filter === 'all') return true;
       if (filter === 'human') return decision.human_required;
       if (filter === 'automated') return !decision.human_required;
       return true;
     });
     
     const getDecisionColor = (type: string) => {
       switch (type) {
         case 'approve': return 'text-green-600';
         case 'reject': return 'text-red-600';
         case 'modify': return 'text-yellow-600';
         case 'escalate': return 'text-purple-600';
         default: return 'text-gray-600';
       }
     };
     
     if (loading) {
       return (
         <div className="flex items-center justify-center h-64">
           <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
         </div>
       );
     }
     
     return (
       <div className="space-y-4">
         {/* Header with filters */}
         <div className="flex items-center justify-between mb-6">
           <h2 className="text-2xl font-bold text-gray-900">Decision History</h2>
           <div className="flex space-x-2">
             <button
               onClick={() => setFilter('all')}
               className={`px-3 py-1 rounded-md text-sm font-medium ${
                 filter === 'all'
                   ? 'bg-blue-100 text-blue-700'
                   : 'text-gray-500 hover:text-gray-700'
               }`}
             >
               All ({decisions.length})
             </button>
             <button
               onClick={() => setFilter('human')}
               className={`px-3 py-1 rounded-md text-sm font-medium ${
                 filter === 'human'
                   ? 'bg-blue-100 text-blue-700'
                   : 'text-gray-500 hover:text-gray-700'
               }`}
             >
               Human ({decisions.filter(d => d.human_required).length})
             </button>
             <button
               onClick={() => setFilter('automated')}
               className={`px-3 py-1 rounded-md text-sm font-medium ${
                 filter === 'automated'
                   ? 'bg-blue-100 text-blue-700'
                   : 'text-gray-500 hover:text-gray-700'
               }`}
             >
               Automated ({decisions.filter(d => !d.human_required).length})
             </button>
           </div>
         </div>
         
         {/* Decision list */}
         <div className="space-y-4">
           {filteredDecisions.map(decision => (
             <div
               key={decision.id}
               className="bg-white rounded-lg shadow-sm border border-gray-200 p-4"
             >
               <div className="flex items-start justify-between">
                 <div className="flex-1">
                   {/* Title and decision */}
                   <div className="flex items-center space-x-3 mb-2">
                     <h3 className="text-lg font-medium text-gray-900">
                       {decision.topic_title}
                     </h3>
                     <span className={`font-semibold ${getDecisionColor(decision.decision_type)}`}>
                       {decision.decision_type.toUpperCase()}
                     </span>
                   </div>
                   
                   {/* Metadata */}
                   <div className="flex items-center space-x-4 text-sm text-gray-500 mb-2">
                     <span className="flex items-center">
                       {decision.human_required ? (
                         <User className="h-4 w-4 mr-1" />
                       ) : (
                         <Bot className="h-4 w-4 mr-1" />
                       )}
                       {decision.made_by}
                     </span>
                     <span className="flex items-center">
                       <Clock className="h-4 w-4 mr-1" />
                       {format(new Date(decision.made_at), 'PPp')}
                     </span>
                     <span className="flex items-center">
                       <AlertTriangle className="h-4 w-4 mr-1" />
                       {decision.controversy_level}
                     </span>
                   </div>
                   
                   {/* Reasoning */}
                   <p className="text-sm text-gray-600 mb-2">
                     {decision.reasoning}
                   </p>
                   
                   {/* Guidelines */}
                   {decision.guidelines_applied.length > 0 && (
                     <div className="flex flex-wrap gap-1">
                       {decision.guidelines_applied.map((guideline, idx) => (
                         <Badge key={idx} variant="secondary" size="xs">
                           {guideline}
                         </Badge>
                       ))}
                     </div>
                   )}
                 </div>
               </div>
             </div>
           ))}
         </div>
       </div>
     );
   };
   ```

**Success Criteria**:
- [ ] Pending decisions panel with real-time updates
- [ ] Decision card with timeout visualization
- [ ] Real-time notification system
- [ ] Decision history view with filtering
- [ ] Responsive UI design
- [ ] Integration with AG-UI events
- [ ] E2E tests for UI components

**Deploy Test**: Po ukończeniu tego bloku, deploy frontend components na droplet