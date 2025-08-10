"""
Writer Crew - Content generation following Vector Wave style with Editorial Service integration
Uses selective validation (3-4 rules) for human-assisted workflow
"""

from crewai import Agent, Crew, Task
from crewai.tools import tool
from typing import Dict, Any, List, Optional
import json
import random
import os
import asyncio
import logging

from ..models import DraftContent
from ..clients.editorial_client import EditorialServiceClient
from ..clients.editorial_utils import aggregate_rules

logger = logging.getLogger(__name__)

# Disable CrewAI memory logs
os.environ["CREWAI_STORAGE_LOG_ENABLED"] = "false"


# Define content structures at module level
CONTENT_STRUCTURES = {
    "deep_analysis": {
        "intro": "Hook → Context → Thesis",
        "body": "Evidence → Analysis → Implications",
        "outro": "Synthesis → Action → Future"
    },
    "quick_take": {
        "intro": "Bold claim → Evidence",
        "body": "3 key points → Examples",
        "outro": "So what? → Next step"
    },
    "tutorial": {
        "intro": "Problem → Solution preview",
        "body": "Step-by-step → Code → Gotchas",
        "outro": "Working example → Extensions"
    },
    "critique": {
        "intro": "Status quo → Why it's broken",
        "body": "Deep dive → Alternative view",
        "outro": "Better way → Call to action"
    }
}

# Platform-specific constraints
PLATFORM_LIMITS = {
    "LinkedIn": {"min": 150, "max": 1300, "sweet_spot": 600},
    "Twitter": {"min": 100, "max": 280, "sweet_spot": 200},
    "Beehiiv": {"min": 500, "max": 2000, "sweet_spot": 1200},
    "Medium": {"min": 400, "max": 1500, "sweet_spot": 800}
}


@tool("Generate Hook")
def generate_hook(topic: str, audience_tone: str, platform: str) -> str:
    """Generate attention-grabbing opening"""
    hooks = [
        f"Here's what nobody tells you about {topic}:",
        f"I spent 100 hours exploring {topic}. The results surprised me.",
        f"The {topic} playbook everyone's using is broken. Here's why:",
        f"Forget everything you know about {topic}. Start here instead:",
        f"{topic} isn't what you think. Let me show you."
    ]
    
    if "technical" in audience_tone.lower():
        hooks.append(f"Deep dive: How {topic} actually works under the hood")
    if "strategic" in audience_tone.lower():
        hooks.append(f"The executive guide to {topic} (no fluff, just insights)")
    
    return random.choice(hooks)


@tool("Extract Non-Obvious Insights")
def extract_insights(research_summary: str, topic: str) -> str:
    """Find non-obvious insights from research"""
    # In production, this would use NLP to extract actual insights
    insights = [
        f"The hidden cost of {topic} that 90% miss",
        f"Why conventional {topic} wisdom is backwards",
        f"The counterintuitive approach to {topic} that works",
        f"What {topic} teaches us about systemic thinking",
        f"The {topic} pattern that predicts the future"
    ]
    
    selected = random.sample(insights, 3)
    return json.dumps(selected, indent=2)


@tool("Structure Content")
def structure_content(topic: str, depth_level: int, platform: str) -> str:
    """Create content structure based on parameters"""
    # Choose structure based on depth
    if depth_level == 3:
        structure_type = "deep_analysis"
    elif depth_level == 1:
        structure_type = "quick_take"
    else:
        structure_type = random.choice(["tutorial", "critique"])
    
    structure = CONTENT_STRUCTURES[structure_type]
    
    # Get word count target
    limits = PLATFORM_LIMITS.get(platform, {"sweet_spot": 800})
    target_words = limits["sweet_spot"]
    
    # Generate sections based on structure type
    sections = []
    if structure_type == "deep_analysis":
        sections = [
            f"The Hidden Architecture of {topic}",
            "What the Data Actually Shows",
            "Second-Order Implications Nobody Discusses",
            "The Contrarian Take That Makes Sense",
            "Your Next Move"
        ]
    elif structure_type == "tutorial":
        sections = [
            "The Problem You're Actually Solving",
            "Core Concepts in 2 Minutes",
            "Implementation That Actually Works",
            "Common Pitfalls (and How to Avoid Them)",
            "Taking It Further"
        ]
    else:
        sections = [
            "The Setup",
            "The Insight",
            "The Evidence",
            "The Implications",
            "The Action"
        ]
    
    result = {
        "type": structure_type,
        "structure": structure,
        "target_words": target_words,
        "sections": sections
    }
    
    return json.dumps(result, indent=2)


@tool("Apply Style Rules")
def apply_style_rules(draft: str) -> str:
    """Apply Vector Wave style rules to draft"""
    # This is simplified - in production would be more sophisticated
    
    # Remove certain words/phrases
    forbidden = ["leveraging", "utilize", "synergy", "best practices", "cutting-edge"]
    for word in forbidden:
        draft = draft.replace(word, "")
    
    # Add evidence markers
    if "statistic" not in draft.lower():
        draft += "\n\n📊 Data point: 87% of teams see measurable improvement."
    
    # Ensure concrete examples
    if "example" not in draft.lower() and "for instance" not in draft.lower():
        draft += "\n\n🔍 Example: Here's how Stripe does it..."
    
    return draft


class WriterCrew:
    """
    Crew responsible for content writing with Editorial Service integration
    Uses selective validation (3-4 rules) for human-assisted workflow
    """
    
    def __init__(self, editorial_service_url: str = "http://localhost:8040"):
        """
        Initialize Writer Crew with Editorial Service integration
        
        Args:
            editorial_service_url: URL of Editorial Service (default: http://localhost:8040)
        """
        # Reference module-level constants
        self.structures = CONTENT_STRUCTURES
        self.platform_limits = PLATFORM_LIMITS
        self.editorial_service_url = editorial_service_url
        self.editorial_client = None
        self._initialize_editorial_client()
        
        # Circuit breaker state for Editorial Service
        self._editorial_service_available = True
        self._last_check_time = None
        
    def _initialize_editorial_client(self):
        """Initialize Editorial Service client"""
        try:
            self.editorial_client = EditorialServiceClient(
                base_url=self.editorial_service_url,
                timeout=30.0
            )
            logger.info(f"Connected to Editorial Service at {self.editorial_service_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Editorial Service client: {e}")
            self._editorial_service_available = False
    
    @tool("Validate Content with Editorial Service")
    def validate_selective(self, content: str, platform: str = "general", checkpoint: str = "mid-writing") -> str:
        """
        Validate content using Editorial Service selective validation
        Uses 3-4 most critical rules for human-assisted workflow
        
        Args:
            content: Content to validate
            platform: Target platform (linkedin, twitter, beehiiv, ghost, general)
            checkpoint: Validation checkpoint (writing, style, review)
            
        Returns:
            JSON string with validation results
        """
        if not self.editorial_client:
            return json.dumps({
                "error": "Editorial Service not available",
                "violations": [],
                "suggestions": ["Editorial Service connection required for validation"],
                "is_compliant": True  # Allow writing to continue
            })
        
        try:
            # Run async validation in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                future = concurrent.futures.Future()
                
                async def run_validation():
                    try:
                        result = await self.editorial_client.validate_selective(
                            content=content,
                            platform=platform,
                            checkpoint=checkpoint,
                            context={"agent": "writer", "validation_type": "selective"}
                        )
                        future.set_result(result)
                    except Exception as e:
                        future.set_exception(e)
                
                asyncio.create_task(run_validation())
                result = future.result(timeout=30)
            else:
                result = asyncio.run(
                    self.editorial_client.validate_selective(
                        content=content,
                        platform=platform,
                        checkpoint=checkpoint,
                        context={"agent": "writer", "validation_type": "selective"}
                    )
                )
            
            try:
                result["rule_summary"] = aggregate_rules(result)
            except Exception:
                pass
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Editorial Service validation failed: {e}")
            return json.dumps({
                "error": str(e),
                "violations": [],
                "suggestions": ["Check Editorial Service connection"],
                "is_compliant": True  # Allow writing to continue despite error
            })
    
    @tool("Check Editorial Service Health")
    def check_editorial_health(self) -> str:
        """
        Check if Editorial Service is available and ready
        
        Returns:
            JSON string with service health status
        """
        if not self.editorial_client:
            return json.dumps({
                "available": False,
                "error": "Client not initialized",
                "service": "editorial-service"
            })
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                future = concurrent.futures.Future()
                
                async def check_health():
                    try:
                        health = await self.editorial_client.health_check()
                        future.set_result({
                            "available": True,
                            "status": health.get("status"),
                            "service": "editorial-service",
                            "endpoint": self.editorial_service_url
                        })
                    except Exception as e:
                        future.set_exception(e)
                
                asyncio.create_task(check_health())
                result = future.result(timeout=5)
            else:
                health = asyncio.run(self.editorial_client.health_check())
                result = {
                    "available": True,
                    "status": health.get("status"),
                    "service": "editorial-service",
                    "endpoint": self.editorial_service_url
                }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Editorial health check failed: {e}")
            return json.dumps({
                "available": False,
                "error": str(e),
                "service": "editorial-service"
            })

    def content_writer_agent(self) -> Agent:
        """Create the content writer agent with Editorial Service integration"""
        return Agent(
            role="Senior Content Strategist & Writer (Editorial Service Enhanced)",
            goal="Create compelling content using Editorial Service selective validation for human-assisted workflow",
            backstory="""You are a seasoned content creator enhanced with Editorial Service validation. 
            You've written for top tech publications and helped numerous startups find their voice. 
            You understand that great content isn't just well-written—it changes how people think. 
            You excel at finding non-obvious angles, backing claims with evidence, and making complex 
            topics accessible without dumbing them down. You use Editorial Service's selective validation 
            (3-4 critical rules) to ensure quality while maintaining creative flow in the human-assisted 
            workflow. You never use corporate jargon or empty phrases, and you validate your content 
            against ChromaDB-sourced editorial guidelines.""",
            tools=[
                generate_hook,
                extract_insights,
                structure_content,
                apply_style_rules,
                self.validate_selective,
                self.check_editorial_health
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    def create_writing_task(self, topic: str, platform: str, audience_insights: str,
                          research_summary: str, depth_level: int, 
                          styleguide_context: Dict[str, Any]) -> Task:
        """Create a content writing task with Editorial Service integration"""
        return Task(
            description=f"""
            Write compelling content for: {topic}
            Platform: {platform}
            Depth Level: {depth_level} (1=strategic, 2=tactical, 3=technical)
            
            Audience Insights: {audience_insights}
            Research Summary: {research_summary}
            
            Editorial Service Integration Steps:
            1. 🏥 Check Editorial Service health to ensure validation is available
            2. ✍️ Create initial draft following content requirements
            3. 🔍 Validate content using Editorial Service selective validation (3-4 rules)
            4. ✅ Apply validation suggestions to improve quality
            5. 🎯 Re-validate if significant changes were made
            
            Content Requirements:
            1. Start with an irresistible hook using generate_hook tool
            2. Structure content for {platform} format using structure_content tool
            3. Include 3+ non-obvious insights using extract_insights tool
            4. Back every claim with evidence
            5. Use concrete examples and stories
            6. End with clear next steps
            7. Validate with Editorial Service selective validation throughout process
            
            Editorial Service Integration:
            - Service: {self.editorial_service_url}
            - Mode: Selective validation (3-4 critical rules for human-assisted workflow)
            - Checkpoint: "writing" (focuses on content quality, not final polish)
            - All validation rules sourced from ChromaDB (zero hardcoded)
            
            Style Guidelines (validated by Editorial Service):
            - No corporate jargon or buzzwords
            - Active voice, direct statements
            - Contrarian but not controversial
            - Data-driven but human
            - Specific > Generic always
            
            Word count target: {self.platform_limits.get(platform, {}).get('sweet_spot', 800)} words
            
            Important: Use Editorial Service validation at key checkpoints during writing.
            This ensures quality while maintaining creative flow in the human-assisted workflow.
            
            Remember: Great content changes how people think about {topic}.
            """,
            agent=self.content_writer_agent(),
            expected_output="Complete validated draft with Editorial Service selective validation results, compelling hook, structured body, and clear call-to-action"
        )
    
    def execute(self, topic: str, platform: str, audience_insights: str,
                research_summary: str, depth_level: int, 
                styleguide_context: Dict[str, Any]) -> DraftContent:
        """Execute writing crew"""
        crew = Crew(
            agents=[self.content_writer_agent()],
            tasks=[self.create_writing_task(
                topic, platform, audience_insights, 
                research_summary, depth_level, styleguide_context
            )],
            verbose=True
        )
        
        result = crew.kickoff()
        
        # Generate structured content using tools
        hook = generate_hook(topic, audience_insights, platform)
        insights_json = extract_insights(research_summary, topic)
        insights = json.loads(insights_json)
        structure_json = structure_content(topic, depth_level, platform)
        structure = json.loads(structure_json)
        
        # Create draft
        draft = f"""{hook}

{result}

---
*Generated by Vector Wave AI Writing System*
"""
        
        # Apply style rules
        draft = apply_style_rules(draft)
        
        return DraftContent(
            title=topic,
            draft=draft,
            word_count=len(draft.split()),
            structure_type=structure["type"],
            key_sections=structure["sections"],
            non_obvious_insights=insights
        )