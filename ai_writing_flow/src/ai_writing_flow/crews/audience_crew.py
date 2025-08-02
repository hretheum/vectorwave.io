"""
Audience Crew - Maps content to target audiences and calibrates messaging
"""

from crewai import Agent, Crew, Task
from crewai.tools import tool
from typing import Dict, Any
import json

from ..models import AudienceAlignment


class AudienceCrew:
    """Crew responsible for audience alignment and messaging calibration"""
    
    def __init__(self):
        # Define Vector Wave target audiences
        self.audiences = {
            "technical_founder": {
                "description": "Pragmatic builders seeking efficient solutions",
                "values": ["ROI", "scalability", "proven results"],
                "pain_points": ["time constraints", "technical debt", "team productivity"],
                "preferred_depth": 2
            },
            "senior_engineer": {
                "description": "Tech leaders evaluating tools and practices",
                "values": ["code quality", "best practices", "innovation"],
                "pain_points": ["legacy systems", "team alignment", "technical excellence"],
                "preferred_depth": 3
            },
            "decision_maker": {
                "description": "Strategic thinkers planning digital transformation",
                "values": ["business impact", "competitive advantage", "risk management"],
                "pain_points": ["market pressure", "resource allocation", "change management"],
                "preferred_depth": 1
            },
            "skeptical_learner": {
                "description": "Critical thinkers questioning AI hype",
                "values": ["evidence", "transparency", "realistic expectations"],
                "pain_points": ["information overload", "unproven claims", "implementation complexity"],
                "preferred_depth": 2
            }
        }
    
    @tool("Analyze Topic Fit")
    def analyze_topic_fit(self, topic: str, audience_key: str) -> float:
        """Calculate how well a topic fits a specific audience"""
        audience = self.audiences.get(audience_key, {})
        
        # Simplified scoring - in production would use NLP
        score = 0.5  # Base score
        
        # Check if topic addresses pain points
        topic_lower = topic.lower()
        for pain_point in audience.get("pain_points", []):
            if any(word in topic_lower for word in pain_point.split()):
                score += 0.1
        
        # Check if topic aligns with values
        for value in audience.get("values", []):
            if any(word in topic_lower for word in value.split()):
                score += 0.1
        
        # Platform-specific adjustments
        if "LinkedIn" in topic and audience_key in ["technical_founder", "decision_maker"]:
            score += 0.1
        elif "Twitter" in topic and audience_key == "senior_engineer":
            score += 0.1
        
        return min(score, 1.0)
    
    @tool("Generate Key Messages")
    def generate_key_messages(self, topic: str, audience_key: str, platform: str) -> str:
        """Generate key messages for specific audience"""
        audience = self.audiences.get(audience_key, {})
        
        messages = {
            "technical_founder": f"How {topic} drives 3x productivity without adding complexity",
            "senior_engineer": f"Deep dive: Implementing {topic} with clean architecture patterns",
            "decision_maker": f"Strategic guide: Why {topic} is your competitive advantage in 2024",
            "skeptical_learner": f"No BS analysis: What {topic} actually delivers (with data)"
        }
        
        return messages.get(audience_key, f"Exploring {topic}")
    
    @tool("Calibrate Tone")
    def calibrate_tone(self, scores: Dict[str, float]) -> str:
        """Determine optimal tone based on audience scores"""
        # Find primary audience
        primary_audience = max(scores.items(), key=lambda x: x[1])[0]
        
        tone_map = {
            "technical_founder": "Direct, practical, ROI-focused. Skip theory, show results.",
            "senior_engineer": "Technical but accessible. Include code examples and architecture.",
            "decision_maker": "Strategic and visionary. Focus on outcomes and transformation.",
            "skeptical_learner": "Honest and evidence-based. Address concerns upfront."
        }
        
        return tone_map.get(primary_audience, "Balanced and informative")
    
    def audience_mapper_agent(self) -> Agent:
        """Create the audience mapping specialist agent"""
        return Agent(
            role="Audience Strategy Specialist",
            goal="Map content to target audiences and optimize messaging for maximum resonance",
            backstory="""You are a seasoned audience strategist with deep expertise in technical 
            content marketing. You understand the unique needs of developers, technical founders, 
            and decision-makers in the tech space. Your superpower is translating complex topics 
            into messages that resonate with specific audience segments while maintaining 
            authenticity and technical accuracy.""",
            tools=[
                self.analyze_topic_fit,
                self.generate_key_messages,
                self.calibrate_tone
            ],
            verbose=True,
            allow_delegation=False
        )
    
    def create_audience_task(self, topic: str, platform: str, research_summary: str, 
                           editorial_recommendations: str) -> Task:
        """Create an audience alignment task"""
        return Task(
            description=f"""
            Analyze audience alignment for: {topic}
            Platform: {platform}
            
            Research Summary: {research_summary}
            Editorial Guidance: {editorial_recommendations}
            
            Steps:
            1. Score topic fit for each target audience:
               - Technical Founders (pragmatic builders)
               - Senior Engineers (tech leaders)
               - Decision Makers (strategic thinkers)
               - Skeptical Learners (critical thinkers)
            
            2. Generate key messages for each audience segment
            
            3. Recommend optimal tone and depth level (1-3):
               - Level 1: High-level strategic (Decision Makers)
               - Level 2: Balanced tactical (Founders, Learners)
               - Level 3: Deep technical (Engineers)
            
            4. Provide specific messaging calibration advice
            
            Consider platform-specific factors:
            - LinkedIn: Professional, thought leadership
            - Twitter: Concise, engaging hooks
            - Newsletter: In-depth, value-packed
            """,
            agent=self.audience_mapper_agent(),
            expected_output="Audience alignment scores, key messages, and tone recommendations"
        )
    
    def execute(self, topic: str, platform: str, research_summary: str, 
                editorial_recommendations: str) -> AudienceAlignment:
        """Execute audience mapping crew"""
        crew = Crew(
            agents=[self.audience_mapper_agent()],
            tasks=[self.create_audience_task(topic, platform, research_summary, editorial_recommendations)],
            verbose=True
        )
        
        result = crew.kickoff()
        
        # Calculate audience scores
        scores = {
            "technical_founder": self.analyze_topic_fit(topic, "technical_founder"),
            "senior_engineer": self.analyze_topic_fit(topic, "senior_engineer"),
            "decision_maker": self.analyze_topic_fit(topic, "decision_maker"),
            "skeptical_learner": self.analyze_topic_fit(topic, "skeptical_learner")
        }
        
        # Determine recommended depth
        primary_audience = max(scores.items(), key=lambda x: x[1])[0]
        recommended_depth = self.audiences[primary_audience]["preferred_depth"]
        
        # Generate key messages
        key_messages = {
            audience: self.generate_key_messages(topic, audience, platform)
            for audience in self.audiences
        }
        
        return AudienceAlignment(
            technical_founder_score=scores["technical_founder"],
            senior_engineer_score=scores["senior_engineer"],
            decision_maker_score=scores["decision_maker"],
            skeptical_learner_score=scores["skeptical_learner"],
            recommended_depth=recommended_depth,
            tone_calibration=self.calibrate_tone(scores),
            key_messages=key_messages
        )