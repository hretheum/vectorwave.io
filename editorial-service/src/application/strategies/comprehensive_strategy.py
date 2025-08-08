"""
Application Strategy: ComprehensiveStrategy
Implements comprehensive validation for Kolegium workflow (8-12 rules).
"""
from typing import List
import structlog

from ...domain.entities import ValidationRequest, ValidationRule, ValidationMode
from ...domain.interfaces import IValidationStrategy, IRuleRepository

logger = structlog.get_logger()


class ComprehensiveStrategy(IValidationStrategy):
    """
    Comprehensive validation strategy for Kolegium workflow.
    
    Returns 8-12 rules covering all validation aspects:
    - Style and editorial rules
    - Platform-specific guidelines  
    - Content structure requirements
    - Technical accuracy standards
    
    All rules sourced exclusively from ChromaDB collections.
    """
    
    def __init__(self, rule_repository: IRuleRepository):
        """
        Initialize comprehensive strategy with rule repository.
        
        Args:
            rule_repository: Repository for accessing ChromaDB rules
        """
        self.rule_repository = rule_repository
        self._min_rules = 8
        self._max_rules = 12
    
    async def validate(self, request: ValidationRequest) -> List[ValidationRule]:
        """
        Perform comprehensive validation using all applicable rules.
        
        Retrieves 8-12 rules from ChromaDB covering:
        - Critical editorial standards
        - Style guide compliance  
        - Platform optimization
        - Content quality metrics
        
        Args:
            request: ValidationRequest for comprehensive validation
            
        Returns:
            List of 8-12 ValidationRule objects from ChromaDB
            
        Raises:
            ValueError: If request is not for comprehensive mode
            RuntimeError: If ChromaDB connection fails
        """
        if not self.supports_request(request):
            raise ValueError(
                f"ComprehensiveStrategy only supports comprehensive mode, "
                f"got {request.mode.value}"
            )
        
        logger.info(
            "Starting comprehensive validation",
            mode=request.mode.value,
            content_length=len(request.content),
            strategy="comprehensive"
        )
        
        try:
            # Get comprehensive rule set from repository
            rules = await self.rule_repository.get_comprehensive_rules(request.content)
            
            # Validate rule count expectations
            if not (self._min_rules <= len(rules) <= self._max_rules):
                logger.warning(
                    "Rule count outside expected range",
                    expected_min=self._min_rules,
                    expected_max=self._max_rules,
                    actual=len(rules),
                    strategy="comprehensive"
                )
            
            # Verify all rules have ChromaDB origin
            for rule in rules:
                if not rule.chromadb_origin_metadata:
                    raise RuntimeError(
                        f"Rule {rule.rule_id} lacks ChromaDB origin metadata - "
                        f"hardcoded rules not allowed"
                    )
            
            logger.info(
                "Comprehensive validation completed",
                rules_count=len(rules),
                collections_used=len({rule.get_origin_collection() for rule in rules}),
                strategy="comprehensive"
            )
            
            return rules
            
        except Exception as e:
            logger.error(
                "Comprehensive validation failed",
                error=str(e),
                strategy="comprehensive"
            )
            raise RuntimeError(f"Comprehensive validation failed: {str(e)}")
    
    def get_expected_rule_count_range(self) -> tuple[int, int]:
        """Get expected rule count range for comprehensive validation"""
        return (self._min_rules, self._max_rules)
    
    def supports_request(self, request: ValidationRequest) -> bool:
        """Check if request is for comprehensive validation"""
        return request.mode == ValidationMode.COMPREHENSIVE
    
    def get_strategy_name(self) -> str:
        """Get strategy name"""
        return "Comprehensive"
    
    def get_workflow_name(self) -> str:
        """Get target workflow name"""
        return "Kolegium"