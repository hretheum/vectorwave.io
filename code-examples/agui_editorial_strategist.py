# Human-in-the-Loop Editorial Strategist

```python
# src/agents/agui_editorial_strategist.py
from crewai import Agent
from src.agui.events import AGUIEvent, AGUIEventType
from src.agui.emitter import AGUIEventEmitter
from src.tools.editorial_guidelines import EditorialGuidelinesTool
from src.tools.audience_analysis import AudienceAnalysisTool
import asyncio
from datetime import datetime, timedelta

class AGUIEditorialStrategist(Agent):
    def __init__(self, agui_emitter: AGUIEventEmitter):
        super().__init__(
            role='Editorial Strategist with Human Collaboration',
            goal='Strategiczna ocena tematów z możliwością konsultacji z redaktorami',
            backstory='''Jesteś doświadczonym strategiem redakcyjnym z intuicją 
                         do collaborative AI. Specjalizujesz się w rozpoznawaniu
                         kontrowersyjnych tematów i facilitation human-AI collaboration.''',
            tools=[
                EditorialGuidelinesTool(),
                AudienceAnalysisTool(),
            ],
            verbose=True
        )
        self.emitter = agui_emitter
        self.agent_id = "editorial_strategist"
        self.human_input_timeout = 300  # 5 minutes
        self.pending_decisions = {}
    
    async def evaluate_topics(self, topics: list):
        """Ocena tematów z możliwością human-in-the-loop"""
        
        await self.emitter.emit(AGUIEvent(
            type=AGUIEventType.PROGRESS_UPDATE,
            data={
                "stage": "editorial_evaluation_start",
                "message": "📋 Rozpoczynam strategiczną ocenę tematów...",
                "progress": 0,
                "total_topics": len(topics)
            },
            agent_id=self.agent_id
        ))
```        
        controversial_topics = []
        evaluated_topics = []
        
        for i, topic in enumerate(topics):
            # Perform AI analysis
            analysis = await self._analyze_topic(topic)
            
            # Emit analysis in real-time
            await self.emitter.emit(AGUIEvent(
                type=AGUIEventType.CONTENT_ANALYSIS,
                data={
                    "topic_id": topic.id,
                    "topic_title": topic.title,
                    "analysis": {
                        "editorial_fit": analysis.editorial_fit,
                        "audience_relevance": analysis.audience_relevance,
                        "controversy_level": analysis.controversy_level,
                        "resource_requirements": analysis.resource_requirements,
                        "strategic_value": analysis.strategic_value,
                        "risk_assessment": analysis.risk_assessment
                    },
                    "ai_recommendation": analysis.recommendation,
                    "confidence_score": analysis.confidence,
                    "reasoning": analysis.reasoning
                },
                agent_id=self.agent_id
            ))
            
            # Check if human input is needed
            if (analysis.controversy_level > 7 or 
                analysis.risk_assessment == "high" or 
                analysis.confidence < 0.7):
                
                controversial_topics.append(topic)
                human_decision = await self._request_human_input(topic, analysis)
                
                if human_decision:
                    final_decision = await self._incorporate_human_feedback(
                        analysis, human_decision
                    )
                else:
                    # Timeout - use AI recommendation with note
                    final_decision = analysis
                    final_decision.human_timeout = True
```                
                # Emit final editorial decision
                await self.emitter.emit(AGUIEvent(
                    type=AGUIEventType.EDITORIAL_DECISION,
                    data={
                        "topic_id": topic.id,
                        "decision": final_decision.decision,
                        "reasoning": final_decision.reasoning,
                        "human_override": human_decision is not None,
                        "final_score": final_decision.score,
                        "priority": final_decision.priority,
                        "recommended_timeline": final_decision.timeline,
                        "resource_allocation": final_decision.resources
                    },
                    agent_id=self.agent_id
                ))
            
            else:
                # Auto-approve low-controversy topics
                await self.emitter.emit(AGUIEvent(
                    type=AGUIEventType.EDITORIAL_DECISION,
                    data={
                        "topic_id": topic.id,
                        "decision": analysis.recommendation,
                        "reasoning": "Automatyczna akceptacja - niski poziom kontrowersji",
                        "human_override": False,
                        "final_score": analysis.score,
                        "auto_approved": True
                    },
                    agent_id=self.agent_id
                ))
            
            evaluated_topics.append(topic)
            
            # Progress update
            await self.emitter.emit(AGUIEvent(
                type=AGUIEventType.PROGRESS_UPDATE,
                data={
                    "stage": "topic_evaluation",
                    "progress": ((i + 1) / len(topics)) * 100,
                    "topics_evaluated": i + 1,
                    "topics_remaining": len(topics) - i - 1,
                    "controversial_count": len(controversial_topics)
                },
                agent_id=self.agent_id
            ))
```