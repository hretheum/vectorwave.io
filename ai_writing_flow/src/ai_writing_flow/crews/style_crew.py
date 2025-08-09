"""
Style Crew - Validates content against Vector Wave styleguide using Editorial Service
Migrated to ChromaDB-centric architecture without hardcoded rules
"""

from crewai import Agent, Crew, Task
from crewai.tools import tool
from typing import Dict, Any, List, Optional
import os
import asyncio
import logging

from ..models import StyleValidation
from ..clients.editorial_client import EditorialServiceClient

# Disable CrewAI memory logs
os.environ["CREWAI_STORAGE_LOG_ENABLED"] = "false"

logger = logging.getLogger(__name__)


class StyleCrew:
    """
    Crew responsible for style validation and compliance
    All validation rules sourced from Editorial Service (ChromaDB)
    """
    
    def __init__(self, editorial_service_url: str = "http://localhost:8040"):
        """
        Initialize Style Crew with Editorial Service integration
        
        Args:
            editorial_service_url: URL of Editorial Service (default: http://localhost:8040)
        """
        self.editorial_service_url = editorial_service_url
        self.editorial_client = None
        self._initialize_client()
        
        # Circuit breaker state for resilience
        self._service_available = True
        self._last_check_time = None
        
    def _initialize_client(self):
        """Initialize Editorial Service client"""
        try:
            self.editorial_client = EditorialServiceClient(
                base_url=self.editorial_service_url,
                timeout=30.0
            )
            logger.info(f"Connected to Editorial Service at {self.editorial_service_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Editorial Service client: {e}")
            self._service_available = False
    
    @tool("Validate Style with Editorial Service")
    def validate_style_comprehensive(self, draft: str, platform: str = "general") -> Dict[str, Any]:
        """
        Validate content style using Editorial Service comprehensive validation
        Uses 8-12 rules for thorough style checking
        
        Args:
            draft: Content to validate
            platform: Target platform (linkedin, twitter, beehiiv, ghost, general)
            
        Returns:
            Dict with validation results from Editorial Service
        """
        if not self.editorial_client:
            return {
                "error": "Editorial Service not available",
                "violations": [],
                "suggestions": ["Editorial Service connection required for validation"]
            }
        
        try:
            # Run async validation in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, use run_coroutine_threadsafe
                import concurrent.futures
                future = concurrent.futures.Future()
                
                async def run_validation():
                    try:
                        result = await self.editorial_client.validate_comprehensive(
                            content=draft,
                            platform=platform,
                            content_type="article",
                            context={"validation_type": "style", "agent": "style_crew"}
                        )
                        future.set_result(result)
                    except Exception as e:
                        future.set_exception(e)
                
                asyncio.create_task(run_validation())
                return future.result(timeout=30)
            else:
                # Create new loop if none exists
                return asyncio.run(
                    self.editorial_client.validate_comprehensive(
                        content=draft,
                        platform=platform,
                        content_type="article",
                        context={"validation_type": "style", "agent": "style_crew"}
                    )
                )
        except Exception as e:
            logger.error(f"Editorial Service validation failed: {e}")
            return {
                "error": str(e),
                "violations": [],
                "suggestions": ["Check Editorial Service connection"]
            }
    
    @tool("Check Forbidden Phrases via Editorial Service")
    def check_forbidden_phrases(self, draft: str) -> List[str]:
        """
        Identify forbidden phrases using Editorial Service
        All forbidden phrases are stored in ChromaDB, zero hardcoded
        
        Args:
            draft: Content to check
            
        Returns:
            List of found forbidden phrases with context
        """
        validation_result = self.validate_style_comprehensive(draft, "general")
        
        if "error" in validation_result:
            logger.warning(f"Editorial Service error: {validation_result['error']}")
            return []
        
        # Extract forbidden phrase violations from Editorial Service response
        forbidden_violations = [
            v for v in validation_result.get("violations", [])
            if v.get("type") == "forbidden_phrase" or 
               v.get("rule_category") == "style_forbidden" or
               "forbidden" in v.get("description", "").lower()
        ]
        
        return [v.get("description", "") for v in forbidden_violations]
    
    @tool("Validate Required Elements via Editorial Service")
    def validate_required_elements(self, draft: str) -> Dict[str, bool]:
        """
        Check if draft contains required elements using Editorial Service
        Requirements defined in ChromaDB, not hardcoded
        
        Args:
            draft: Content to validate
            
        Returns:
            Dict with element validation status
        """
        validation_result = self.validate_style_comprehensive(draft, "general")
        
        if "error" in validation_result:
            logger.warning(f"Editorial Service error: {validation_result['error']}")
            return {
                "evidence": False,
                "specificity": False,
                "conclusion": False,
                "non_obvious_insight": False,
                "clear_value": False
            }
        
        # Parse Editorial Service response for required elements
        element_status = {}
        
        # Check violations for missing elements
        missing_elements = [
            v for v in validation_result.get("violations", [])
            if v.get("type") == "missing_element" or 
               v.get("rule_category") == "required_element"
        ]
        
        # Determine which elements are present based on violations
        common_elements = ["evidence", "specificity", "conclusion", "non_obvious_insight", "clear_value"]
        
        for element in common_elements:
            # Element is present if not in violations
            element_status[element] = not any(
                element in v.get("description", "").lower() 
                for v in missing_elements
            )
        
        # Additional check from suggestions
        if "suggestions" in validation_result:
            for suggestion in validation_result["suggestions"]:
                if "add evidence" in suggestion.lower():
                    element_status["evidence"] = False
                if "be more specific" in suggestion.lower():
                    element_status["specificity"] = False
        
        return element_status
    
    @tool("Analyze Style Patterns via Editorial Service")
    def analyze_style_patterns(self, draft: str) -> Dict[str, List[str]]:
        """
        Analyze writing style patterns using Editorial Service
        Pattern rules stored in ChromaDB
        
        Args:
            draft: Content to analyze
            
        Returns:
            Dict with identified style issues and examples
        """
        validation_result = self.validate_style_comprehensive(draft, "general")
        
        if "error" in validation_result:
            logger.warning(f"Editorial Service error: {validation_result['error']}")
            return {}
        
        # Parse style pattern violations from Editorial Service
        style_issues = {}
        
        pattern_categories = [
            "passive_voice", "weasel_words", "weak_verbs", 
            "redundancy", "long_sentences", "repeated_sentence_starts"
        ]
        
        for violation in validation_result.get("violations", []):
            violation_type = violation.get("type", "")
            
            # Map Editorial Service violation types to our pattern categories
            for pattern in pattern_categories:
                if pattern in violation_type.lower() or pattern in violation.get("rule_category", "").lower():
                    if pattern not in style_issues:
                        style_issues[pattern] = []
                    
                    # Extract examples from violation description
                    description = violation.get("description", "")
                    if description:
                        style_issues[pattern].append(description)
        
        # Limit examples to first 5 for each pattern
        for pattern in style_issues:
            style_issues[pattern] = style_issues[pattern][:5]
        
        return style_issues
    
    @tool("Generate Style Suggestions via Editorial Service")
    def generate_suggestions(self, draft: str, platform: str = "general") -> List[str]:
        """
        Generate improvement suggestions using Editorial Service
        
        Args:
            draft: Content to improve
            platform: Target platform
            
        Returns:
            List of specific improvement suggestions
        """
        validation_result = self.validate_style_comprehensive(draft, platform)
        
        if "error" in validation_result:
            return ["Unable to generate suggestions - Editorial Service unavailable"]
        
        # Get suggestions directly from Editorial Service
        suggestions = validation_result.get("suggestions", [])
        
        # Add platform-specific suggestions if available
        if platform != "general" and "platform_suggestions" in validation_result:
            suggestions.extend(validation_result["platform_suggestions"])
        
        # Prioritize and limit suggestions
        return suggestions[:10]  # Top 10 suggestions
    
    @tool("Check Editorial Service Health")
    def check_service_health(self) -> Dict[str, Any]:
        """
        Check if Editorial Service is available and has rules loaded
        
        Returns:
            Dict with service health status
        """
        if not self.editorial_client:
            return {
                "available": False,
                "error": "Client not initialized"
            }
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                future = concurrent.futures.Future()
                
                async def check_health():
                    try:
                        health = await self.editorial_client.health_check()
                        stats = await self.editorial_client.get_cache_stats()
                        future.set_result({
                            "available": True,
                            "status": health.get("status"),
                            "total_rules": stats.get("total_rules", 0),
                            "service": "editorial-service"
                        })
                    except Exception as e:
                        future.set_exception(e)
                
                asyncio.create_task(check_health())
                return future.result(timeout=5)
            else:
                health = asyncio.run(self.editorial_client.health_check())
                stats = asyncio.run(self.editorial_client.get_cache_stats())
                return {
                    "available": True,
                    "status": health.get("status"),
                    "total_rules": stats.get("total_rules", 0),
                    "service": "editorial-service"
                }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "available": False,
                "error": str(e)
            }
    
    def style_validator_agent(self) -> Agent:
        """Create the style validation agent"""
        return Agent(
            role="Editorial Style Guardian (ChromaDB-Powered)",
            goal="Ensure all content meets Vector Wave's style standards using Editorial Service validation",
            backstory="""You are the guardian of Vector Wave's distinctive voice, now enhanced 
            with ChromaDB-powered validation. You work with the Editorial Service to check content 
            against 355+ dynamically loaded rules. No hardcoded rules - everything comes from 
            the vector database. You validate style, check for forbidden phrases, ensure required 
            elements, and provide actionable suggestions. Your validation is comprehensive, 
            using 8-12 rules per check for thorough quality assurance.""",
            tools=[
                self.validate_style_comprehensive,
                self.check_forbidden_phrases,
                self.validate_required_elements,
                self.analyze_style_patterns,
                self.generate_suggestions,
                self.check_service_health
            ],
            verbose=True,
            allow_delegation=False
        )
    
    def create_validation_task(self, draft: str, styleguide_context: Dict[str, Any]) -> Task:
        """Create a style validation task"""
        platform = styleguide_context.get("platform", "general")
        
        return Task(
            description=f"""
            Validate this draft against Vector Wave style standards using Editorial Service:
            
            {draft}
            
            Platform: {platform}
            
            Validation Process (ChromaDB-Powered):
            1. 🔍 Comprehensive Validation: Use Editorial Service to check against all style rules
            2. ❌ Forbidden Phrases: Identify banned corporate jargon from ChromaDB
            3. ✅ Required Elements: Verify evidence, specificity, clear value from database
            4. 📝 Style Patterns: Analyze passive voice, weak verbs using vector rules
            5. 💡 Suggestions: Get specific improvements from Editorial Service
            
            Editorial Service Integration:
            - Endpoint: {self.editorial_service_url}
            - Mode: Comprehensive (8-12 rules)
            - Source: 100% ChromaDB (zero hardcoded rules)
            
            First, check Editorial Service health to ensure connection.
            Then perform comprehensive validation.
            Finally, compile all findings into actionable feedback.
            
            Be thorough but constructive. All rules come from Editorial Service.
            """,
            agent=self.style_validator_agent(),
            expected_output="Complete style validation report from Editorial Service with violations and suggestions"
        )
    
    def execute(self, draft: str, styleguide_context: Dict[str, Any]) -> StyleValidation:
        """Execute style validation crew"""
        platform = styleguide_context.get("platform", "general")
        
        # First check Editorial Service availability
        health = self.check_service_health()
        if not health.get("available"):
            logger.error(f"Editorial Service unavailable: {health.get('error')}")
            return StyleValidation(
                is_compliant=False,
                violations=[{
                    "type": "service_error",
                    "severity": "critical",
                    "description": f"Editorial Service unavailable: {health.get('error')}"
                }],
                forbidden_phrases=[],
                suggestions=["Please ensure Editorial Service is running on port 8040"],
                compliance_score=0
            )
        
        logger.info(f"Editorial Service healthy with {health.get('total_rules', 0)} rules loaded")
        
        # Create and execute crew
        crew = Crew(
            agents=[self.style_validator_agent()],
            tasks=[self.create_validation_task(draft, styleguide_context)],
            verbose=True
        )
        
        result = crew.kickoff()
        
        # Get comprehensive validation from Editorial Service
        validation_result = self.validate_style_comprehensive(draft, platform)
        
        if "error" in validation_result:
            return StyleValidation(
                is_compliant=False,
                violations=[{
                    "type": "validation_error",
                    "severity": "high",
                    "description": validation_result["error"]
                }],
                forbidden_phrases=[],
                suggestions=["Check Editorial Service connection"],
                compliance_score=0
            )
        
        # Extract violations from Editorial Service response
        violations = validation_result.get("violations", [])
        
        # Extract forbidden phrases
        forbidden_phrases = [
            v.get("phrase", "") 
            for v in violations 
            if v.get("type") == "forbidden_phrase"
        ]
        
        # Get suggestions from Editorial Service
        suggestions = validation_result.get("suggestions", [])[:10]
        
        # Calculate compliance score from Editorial Service metrics
        compliance_score = validation_result.get("compliance_score", 0)
        
        # If no score provided, calculate based on violations
        if compliance_score == 0 and not violations:
            compliance_score = 100
        elif compliance_score == 0:
            base_score = 100
            high_violations = len([v for v in violations if v.get("severity") == "high"])
            medium_violations = len([v for v in violations if v.get("severity") == "medium"])
            low_violations = len([v for v in violations if v.get("severity") == "low"])
            
            compliance_score = max(0, base_score - (high_violations * 15) - 
                                  (medium_violations * 10) - (low_violations * 5))
        
        return StyleValidation(
            is_compliant=compliance_score >= 70,
            violations=violations,
            forbidden_phrases=forbidden_phrases,
            suggestions=suggestions,
            compliance_score=compliance_score
        )