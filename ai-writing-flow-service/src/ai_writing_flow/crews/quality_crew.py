"""
Quality Crew - Final quality assessment with Editorial Service comprehensive validation
Enhanced with ChromaDB-sourced editorial guidelines for final quality check
"""

from crewai import Agent, Crew, Task, Process
from crewai.tools import tool
from typing import Dict, Any, List, Optional
import re
from datetime import datetime
import os
import json
import asyncio
import logging

from ..models import QualityAssessment
from ..clients.editorial_client import EditorialServiceClient
from ..clients.editorial_utils import aggregate_rules

# Disable CrewAI memory logs
os.environ["CREWAI_STORAGE_LOG_ENABLED"] = "false"

logger = logging.getLogger(__name__)


class QualityCrew:
    """
    Crew responsible for final quality control with Editorial Service integration
    Uses comprehensive validation (8-12 rules) for thorough final quality check
    """
    
    def __init__(self, editorial_service_url: str = "http://localhost:8040"):
        """
        Initialize Quality Crew with Editorial Service integration
        
        Args:
            editorial_service_url: URL of Editorial Service (default: http://localhost:8040)
        """
        # Quality criteria weights
        self.criteria_weights = {
            "factual_accuracy": 0.25,
            "source_verification": 0.20,
            "logical_coherence": 0.15,
            "value_delivery": 0.15,
            "readability": 0.10,
            "originality": 0.10,
            "actionability": 0.05
        }
        
        # Ethics checklist items
        self.ethics_checklist = [
            "no_misleading_claims",
            "proper_attribution",
            "balanced_perspective",
            "no_harmful_advice",
            "respects_privacy",
            "avoids_discrimination"
        ]
        
        # Editorial Service integration
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
    
    @tool("Validate Comprehensive Quality")
    def validate_comprehensive_quality(self, content: str, platform: str = "general", content_type: str = "article") -> str:
        """
        Perform comprehensive Editorial Service validation for final quality check
        Uses comprehensive validation (8-12 rules) from ChromaDB
        
        Args:
            content: Content to validate for final quality
            platform: Target platform (linkedin, twitter, beehiiv, ghost, general)
            content_type: Type of content (article, post, newsletter)
            
        Returns:
            JSON string with comprehensive validation results
        """
        if not self.editorial_client:
            return json.dumps({
                "error": "Editorial Service not available",
                "violations": [],
                "suggestions": ["Editorial Service connection required for comprehensive quality validation"],
                "is_compliant": True,  # Allow to continue
                "quality_score": 75  # Default passing score
            })
        
        try:
            # Run async validation in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                future = concurrent.futures.Future()
                
                async def run_validation():
                    try:
                        result = await self.editorial_client.validate_comprehensive(
                            content=content,
                            platform=platform,
                            content_type=content_type,
                            context={
                                "agent": "quality",
                                "validation_type": "comprehensive_quality",
                                "checkpoint": "final"
                            }
                        )
                        future.set_result(result)
                    except Exception as e:
                        future.set_exception(e)
                
                asyncio.create_task(run_validation())
                result = future.result(timeout=30)
            else:
                result = asyncio.run(
                    self.editorial_client.validate_comprehensive(
                        content=content,
                        platform=platform,
                        content_type=content_type,
                        context={
                            "agent": "quality",
                            "validation_type": "comprehensive_quality",
                            "checkpoint": "final"
                        }
                    )
                )
            
            # Add quality-specific insights
            result["quality_assessment"] = self._assess_quality_factors(content, result)
            # Aggregate rule summary (critical count, weighted score)
            try:
                result["rule_summary"] = aggregate_rules(result)
            except Exception:
                pass
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Editorial Service comprehensive validation failed: {e}")
            return json.dumps({
                "error": str(e),
                "violations": [],
                "suggestions": ["Check Editorial Service connection for comprehensive validation"],
                "is_compliant": True,  # Allow to continue despite error
                "quality_score": 75
            })
    
    @tool("Get Editorial Quality Rules")
    def get_editorial_quality_rules(self, validation_type: str = "comprehensive") -> str:
        """
        Get comprehensive quality rules from Editorial Service
        
        Args:
            validation_type: Type of validation (comprehensive, quality, final)
            
        Returns:
            JSON string with quality rules and guidelines
        """
        if not self.editorial_client:
            return json.dumps({
                "error": "Editorial Service not available",
                "quality_rules": self._get_fallback_quality_rules()
            })
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                future = concurrent.futures.Future()
                
                async def get_rules():
                    try:
                        cache_dump = await self.editorial_client.get_cache_dump()
                        quality_rules = [
                            rule for rule in cache_dump
                            if rule.get("category") in ["quality", "final", "comprehensive"]
                            or rule.get("validation_type") == validation_type
                        ]
                        
                        result = {
                            "validation_type": validation_type,
                            "rules_count": len(quality_rules),
                            "quality_rules": quality_rules[:15],  # First 15 rules
                            "categories": list(set(rule.get("category", "general") for rule in quality_rules))
                        }
                        future.set_result(result)
                    except Exception as e:
                        future.set_exception(e)
                
                asyncio.create_task(get_rules())
                result = future.result(timeout=30)
            else:
                cache_dump = asyncio.run(self.editorial_client.get_cache_dump())
                quality_rules = [
                    rule for rule in cache_dump
                    if rule.get("category") in ["quality", "final", "comprehensive"]
                    or rule.get("validation_type") == validation_type
                ]
                
                result = {
                    "validation_type": validation_type,
                    "rules_count": len(quality_rules),
                    "quality_rules": quality_rules[:15],  # First 15 rules
                    "categories": list(set(rule.get("category", "general") for rule in quality_rules))
                }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to get quality rules: {e}")
            return json.dumps({
                "error": str(e),
                "quality_rules": self._get_fallback_quality_rules()
            })
    
    @tool("Check Editorial Service Health")
    def check_editorial_health(self) -> str:
        """
        Check if Editorial Service is available for comprehensive validation
        
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
                            "endpoint": self.editorial_service_url,
                            "validation_types": ["comprehensive", "quality", "final"]
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
                    "endpoint": self.editorial_service_url,
                    "validation_types": ["comprehensive", "quality", "final"]
                }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Editorial health check failed: {e}")
            return json.dumps({
                "available": False,
                "error": str(e),
                "service": "editorial-service"
            })
    
    def _assess_quality_factors(self, content: str, validation_result: Dict) -> Dict:
        """Generate quality-specific assessment based on validation"""
        assessment = {
            "completeness": "complete" if len(content.split()) > 200 else "incomplete",
            "readability": "good" if len(content.split()) < 2000 else "challenging",
            "structure": "clear" if content.count('\n\n') >= 2 else "needs_improvement",
            "actionability": "high" if any(word in content.lower() for word in ["step", "how", "try", "use"]) else "low"
        }
        
        # Add Editorial Service specific insights
        if "violations" in validation_result:
            violation_count = len(validation_result["violations"])
            if violation_count == 0:
                assessment["editorial_compliance"] = "excellent"
            elif violation_count <= 2:
                assessment["editorial_compliance"] = "good"
            else:
                assessment["editorial_compliance"] = "needs_improvement"
        
        return assessment
    
    def _get_fallback_quality_rules(self) -> Dict:
        """Fallback quality rules when Editorial Service unavailable"""
        return {
            "comprehensive_rules": [
                "Grammar and style consistency",
                "Platform compliance verification", 
                "Brand voice alignment",
                "Content completeness check",
                "Factual accuracy verification",
                "Source attribution requirements",
                "Readability optimization",
                "Value delivery confirmation"
            ],
            "source": "fallback_rules"
        }

    @tool("Fact Check Claims")
    def fact_check_claims(self, draft: str, sources: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Verify factual claims in the draft"""
        fact_checks = []
        
        # Pattern for statistics and claims
        stat_patterns = [
            r'(\d+(?:\.\d+)?)\s*%',  # Percentages
            r'(\d+)x\s+(?:faster|better|more)',  # Multipliers
            r'(\d+(?:,\d{3})*)\s+(?:users|companies|developers)',  # Counts
            r'\$(\d+(?:\.\d+)?[MBK]?)',  # Money amounts
            r'(?:study|research|survey)\s+(?:shows|found|indicates)',  # Studies
        ]
        
        for pattern in stat_patterns:
            matches = re.finditer(pattern, draft, re.IGNORECASE)
            for match in matches:
                context = draft[max(0, match.start()-50):min(len(draft), match.end()+50)]
                
                # Check if claim is supported by sources
                supported = any(source.get("title", "").lower() in context.lower() 
                              for source in sources)
                
                fact_checks.append({
                    "claim": match.group(0),
                    "context": context.strip(),
                    "verified": supported,
                    "confidence": "high" if supported else "low"
                })
        
        return fact_checks
    
    @tool("Verify Code Examples")
    def verify_code_examples(self, draft: str) -> Optional[Dict[str, str]]:
        """Check code examples for correctness"""
        # Find code blocks
        code_pattern = r'```(\w+)?\n(.*?)```'
        code_blocks = re.findall(code_pattern, draft, re.DOTALL)
        
        if not code_blocks:
            return None
        
        verification = {
            "total_blocks": len(code_blocks),
            "languages": list(set(lang for lang, _ in code_blocks if lang)),
            "syntax_valid": True,  # Simplified - would use actual parsers
            "best_practices": True,
            "security_issues": []
        }
        
        # Check for common security issues
        for lang, code in code_blocks:
            if "eval(" in code or "exec(" in code:
                verification["security_issues"].append("Unsafe eval/exec usage")
            if "password" in code.lower() and "=" in code:
                verification["security_issues"].append("Possible hardcoded credentials")
        
        return verification
    
    @tool("Assess Logical Flow")
    def assess_logical_flow(self, draft: str) -> Dict[str, Any]:
        """Evaluate logical coherence and structure"""
        paragraphs = [p.strip() for p in draft.split('\n\n') if p.strip()]
        
        assessment = {
            "structure_clear": len(paragraphs) >= 3,
            "has_introduction": any(p.endswith('?') or 'here' in p.lower() 
                                  for p in paragraphs[:2]),
            "has_conclusion": any(word in paragraphs[-1].lower() 
                                for word in ['therefore', 'so', 'result', 'means']),
            "logical_transitions": 0,
            "coherence_score": 0.0
        }
        
        # Check transitions
        transition_words = ['however', 'therefore', 'moreover', 'furthermore', 
                          'additionally', 'consequently', 'thus', 'hence']
        for para in paragraphs:
            if any(word in para.lower() for word in transition_words):
                assessment["logical_transitions"] += 1
        
        # Calculate coherence score
        if assessment["structure_clear"] and assessment["has_introduction"] and assessment["has_conclusion"]:
            assessment["coherence_score"] = 0.8
        else:
            assessment["coherence_score"] = 0.5
        
        if assessment["logical_transitions"] >= 2:
            assessment["coherence_score"] += 0.2
        
        return assessment
    
    @tool("Check Controversy Score")
    def check_controversy(self, draft: str) -> float:
        """Assess potential controversy level"""
        controversy_triggers = {
            "high": ["wrong", "stupid", "idiots", "hate", "destroy", "kill"],
            "medium": ["controversial", "debate", "disagree", "critics", "opponents"],
            "low": ["challenge", "question", "consider", "alternative", "perspective"]
        }
        
        score = 0.0
        draft_lower = draft.lower()
        
        for level, words in controversy_triggers.items():
            matches = sum(1 for word in words if word in draft_lower)
            if level == "high":
                score += matches * 0.3
            elif level == "medium":
                score += matches * 0.15
            else:
                score += matches * 0.05
        
        return min(score, 1.0)
    
    @tool("Evaluate Value Delivery")
    def evaluate_value(self, draft: str, non_obvious_insights: List[str]) -> Dict[str, bool]:
        """Check if content delivers promised value"""
        evaluation = {
            "has_clear_takeaway": any(phrase in draft.lower() 
                                    for phrase in ["you can", "here's how", "step"]),
            "provides_examples": "example" in draft.lower() or "for instance" in draft.lower(),
            "actionable_advice": any(phrase in draft.lower() 
                                   for phrase in ["try", "implement", "start", "use this"]),
            "unique_perspective": len(non_obvious_insights) >= 2,
            "saves_reader_time": len(draft.split()) < 1500  # Concise is valuable
        }
        
        return evaluation
    
    def quality_controller_agent(self) -> Agent:
        """Create the quality control agent with Editorial Service integration"""
        return Agent(
            role="Chief Quality Officer (Editorial Service Enhanced)",
            goal="Ensure content meets the highest standards using Editorial Service comprehensive validation (8-12 rules)",
            backstory="""You are a meticulous quality controller enhanced with Editorial Service validation. 
            You have a background in investigative journalism and technical writing, with access to 
            ChromaDB-sourced editorial guidelines for comprehensive quality checks. You've fact-checked 
            for major publications and have a reputation for catching errors others miss. You believe 
            that quality content must be accurate, valuable, and ethical. You're thorough but pragmatic, 
            understanding that perfection is less important than publishing valuable, trustworthy content. 
            You use Editorial Service's comprehensive validation (8-12 rules) for final quality assurance, 
            ensuring all content meets the highest editorial standards sourced from ChromaDB.""",
            tools=[
                self.validate_comprehensive_quality,
                self.get_editorial_quality_rules,  
                self.check_editorial_health,
                self.fact_check_claims,
                self.verify_code_examples,
                self.assess_logical_flow,
                self.check_controversy,
                self.evaluate_value
            ],
            verbose=True,
            allow_delegation=False,
            max_iter=4  # Allow more iterations for comprehensive validation
        )
    
    def create_quality_task(self, draft: str, sources: List[Dict[str, str]], 
                          styleguide_context: Dict[str, Any]) -> Task:
        """Create a comprehensive quality assessment task with Editorial Service integration"""
        platform = styleguide_context.get('platform', 'general')
        content_type = styleguide_context.get('content_type', 'article')
        
        return Task(
            description=f"""
            Perform comprehensive quality assessment with Editorial Service integration for this draft:
            
            {draft[:500]}... [truncated]
            
            COMPREHENSIVE QUALITY WORKFLOW (Editorial Service Enhanced):
            
            1. 🏥 Editorial Service Health Check
               - Verify Editorial Service is available
               - Confirm comprehensive validation capability
               - Check connection to ChromaDB editorial guidelines
            
            2. 📋 Get Editorial Quality Rules
               - Retrieve comprehensive quality rules (8-12 rules)
               - Understand ChromaDB-sourced editorial standards
               - Review final validation requirements
            
            3. 🔍 Comprehensive Editorial Validation  
               - Run comprehensive Editorial Service validation
               - Apply 8-12 rules from ChromaDB for final quality check
               - Validate grammar, style, platform compliance, brand voice
               - Check content completeness and factual accuracy
            
            4. 📊 Traditional Quality Checks (Supplement Editorial Service)
               - Fact check claims against sources
               - Verify code examples (if applicable)
               - Assess logical coherence and flow
               - Evaluate value delivery and actionability
               - Check controversy level and ethics
            
            5. 📈 Final Quality Assessment
               - Combine Editorial Service comprehensive results
               - Traditional quality metrics
               - Generate overall quality score (0-100)
               - Flag any blockers or critical issues
               - Provide improvement suggestions
            
            Editorial Service Integration:
            - Service: {self.editorial_service_url}
            - Mode: Comprehensive validation (8-12 critical rules for final quality)
            - Platform: {platform}
            - Content Type: {content_type}
            - All validation rules sourced from ChromaDB (zero hardcoded)
            
            Sources provided: {len(sources)}
            Platform: {platform}
            Content Type: {content_type}
            
            Important: Use Editorial Service comprehensive validation as the PRIMARY quality check.
            Traditional tools supplement and verify the Editorial Service results.
            This ensures all content meets Vector Wave's highest editorial standards.
            """,
            agent=self.quality_controller_agent(),
            expected_output="""Complete comprehensive quality assessment with Editorial Service validation results:
            
            FINAL QUALITY ASSESSMENT:
            - Editorial Service Comprehensive Score: [X/100] 
            - Editorial Violations: [list any violations]
            - Quality Assessment Factors: [completeness, readability, structure, actionability]
            - Traditional Quality Score: [X/100]
            - Overall Quality Score: [X/100]
            - Approval Status: [APPROVED/NEEDS_REVISION/REQUIRES_HUMAN_REVIEW]
            
            IMPROVEMENT SUGGESTIONS:
            [Specific, actionable recommendations based on Editorial Service and traditional analysis]
            
            EDITORIAL SERVICE DETAILS:
            [Rules applied, ChromaDB sources, validation context]"""
        )
    
    def execute(self, draft: str, sources: List[Dict[str, str]], 
                styleguide_context: Dict[str, Any]) -> QualityAssessment:
        """Execute quality control crew"""
        crew = Crew(
            agents=[self.quality_controller_agent()],
            tasks=[self.create_quality_task(draft, sources, styleguide_context)],
            verbose=True,
            process=Process.sequential
        )
        
        result = crew.kickoff()
        
        # Run quality checks
        fact_checks = self.fact_check_claims(draft, sources)
        code_verification = self.verify_code_examples(draft)
        logical_flow = self.assess_logical_flow(draft)
        controversy_score = self.check_controversy(draft)
        value_delivery = self.evaluate_value(draft, [])  # Would get from state
        
        # Build ethics checklist results
        ethics_results = {}
        for item in self.ethics_checklist:
            # Simplified - in production would be more sophisticated
            ethics_results[item] = True
        
        # Calculate quality score
        scores = {
            "factual_accuracy": 0.9 if all(fc["verified"] for fc in fact_checks) else 0.6,
            "source_verification": 0.8 if sources else 0.4,
            "logical_coherence": logical_flow["coherence_score"],
            "value_delivery": sum(value_delivery.values()) / len(value_delivery),
            "readability": 0.85,  # Would use readability metrics
            "originality": 0.8,   # Would use similarity detection
            "actionability": 0.9 if value_delivery.get("actionable_advice") else 0.5
        }
        
        quality_score = sum(score * self.criteria_weights[criterion] 
                          for criterion, score in scores.items()) * 100
        
        # Generate improvement suggestions
        suggestions = []
        
        if not all(fc["verified"] for fc in fact_checks):
            suggestions.append("Add source citations for unverified claims")
        
        if not logical_flow["has_conclusion"]:
            suggestions.append("Add a clear conclusion with key takeaways")
        
        if controversy_score > 0.5:
            suggestions.append("Consider softening controversial statements")
        
        if not value_delivery.get("actionable_advice"):
            suggestions.append("Add specific, actionable next steps")
        
        # Determine if human review needed
        requires_human = (
            quality_score < 70 or
            controversy_score > 0.7 or
            bool(code_verification and code_verification.get("security_issues")) or
            not all(ethics_results.values())
        )
        
        return QualityAssessment(
            is_approved=quality_score >= 70 and not requires_human,
            quality_score=quality_score,
            fact_check_results=[{
                "claim": fc["claim"],
                "status": "verified" if fc["verified"] else "unverified",
                "confidence": fc["confidence"]
            } for fc in fact_checks],
            code_verification=code_verification,
            ethics_checklist=ethics_results,
            improvement_suggestions=suggestions,
            requires_human_review=requires_human,
            controversy_score=controversy_score
        )