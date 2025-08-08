"""
Application Strategy: SelectiveStrategy
Implements selective validation for AI Writing Flow workflow (3-4 rules).
"""
from typing import List
import structlog

from ...domain.entities import ValidationRequest, ValidationRule, ValidationMode
from ...domain.interfaces import IValidationStrategy, IRuleRepository

logger = structlog.get_logger()


class SelectiveStrategy(IValidationStrategy):
    """
    Selective validation strategy for AI Writing Flow workflow.
    
    Returns 3-4 rules specific to checkpoint phases:
    - Pre-writing: Planning and structure rules
    - Mid-writing: Content flow and coherence  
    - Post-writing: Quality and platform optimization
    
    Optimized for human-assisted workflow with focused checkpoints.
    All rules sourced exclusively from ChromaDB collections.
    """
    
    def __init__(self, rule_repository: IRuleRepository):
        """
        Initialize selective strategy with rule repository.
        
        Args:
            rule_repository: Repository for accessing ChromaDB rules
        """
        self.rule_repository = rule_repository
        self._min_rules = 3
        self._max_rules = 4
    
    async def validate(self, request: ValidationRequest) -> List[ValidationRule]:
        """
        Perform selective validation using checkpoint-specific rules.
        
        Retrieves 3-4 rules from ChromaDB tailored to specific checkpoint:
        - Pre-writing: Structure, audience, planning validation
        - Mid-writing: Flow, coherence, style consistency
        - Post-writing: Quality, optimization, platform compliance
        
        Args:
            request: ValidationRequest for selective validation with checkpoint
            
        Returns:
            List of 3-4 ValidationRule objects from ChromaDB
            
        Raises:
            ValueError: If request is not for selective mode or missing checkpoint
            RuntimeError: If ChromaDB connection fails
        """
        if not self.supports_request(request):
            raise ValueError(
                f"SelectiveStrategy only supports selective mode with checkpoint, "
                f"got mode={request.mode.value}, checkpoint={request.checkpoint}"
            )
        
        logger.info(
            "Starting selective validation",
            mode=request.mode.value,
            checkpoint=request.checkpoint.value,
            content_length=len(request.content),
            strategy="selective"
        )
        
        try:
            # Get selective rule set for specific checkpoint
            rules = await self.rule_repository.get_selective_rules(
                request.content, 
                request.checkpoint
            )
            
            # Validate rule count expectations
            if not (self._min_rules <= len(rules) <= self._max_rules):
                logger.warning(
                    "Rule count outside expected range",
                    expected_min=self._min_rules,
                    expected_max=self._max_rules,
                    actual=len(rules),
                    checkpoint=request.checkpoint.value,
                    strategy="selective"
                )
            
            # Verify all rules have ChromaDB origin
            for rule in rules:
                if not rule.chromadb_origin_metadata:
                    raise RuntimeError(
                        f"Rule {rule.rule_id} lacks ChromaDB origin metadata - "
                        f"hardcoded rules not allowed"
                    )
            
            logger.info(
                "Selective validation completed",
                rules_count=len(rules),
                checkpoint=request.checkpoint.value,
                collections_used=len({rule.get_origin_collection() for rule in rules}),
                strategy="selective"
            )
            
            return rules
            
        except Exception as e:
            logger.error(
                "Selective validation failed",
                error=str(e),
                checkpoint=request.checkpoint.value if request.checkpoint else None,
                strategy="selective"
            )
            raise RuntimeError(f"Selective validation failed: {str(e)}")
    
    def get_expected_rule_count_range(self) -> tuple[int, int]:
        """Get expected rule count range for selective validation"""
        return (self._min_rules, self._max_rules)
    
    def supports_request(self, request: ValidationRequest) -> bool:
        """Check if request is for selective validation with checkpoint"""
        return (
            request.mode == ValidationMode.SELECTIVE and 
            request.checkpoint is not None
        )
    
    def get_strategy_name(self) -> str:
        """Get strategy name"""
        return "Selective"
    
    def get_workflow_name(self) -> str:
        """Get target workflow name"""
        return "AI Writing Flow"