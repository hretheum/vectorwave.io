"""
Domain Interface: IValidationStrategy
Abstract interface for validation strategies implementing Strategy pattern.
"""
from abc import ABC, abstractmethod
from typing import List

from ..entities import ValidationRequest, ValidationRule


class IValidationStrategy(ABC):
    """
    Abstract interface for validation strategies.
    
    Implements Strategy pattern to support dual workflow architecture:
    - ComprehensiveStrategy: Full validation for Kolegium (8-12 rules)
    - SelectiveStrategy: Checkpoint-based validation for AI Writing Flow (3-4 rules)
    
    All strategies must source rules exclusively from ChromaDB - no hardcoded rules.
    """
    
    @abstractmethod
    async def validate(self, request: ValidationRequest) -> List[ValidationRule]:
        """
        Validate content according to strategy-specific logic.
        
        Args:
            request: ValidationRequest containing content and workflow parameters
            
        Returns:
            List of ValidationRule objects sourced from ChromaDB
            
        Raises:
            ValueError: If request is invalid for this strategy
            RuntimeError: If ChromaDB connection fails and no cache available
        """
        pass
    
    @abstractmethod
    def get_expected_rule_count_range(self) -> tuple[int, int]:
        """
        Get expected range of rules this strategy should return.
        
        Returns:
            Tuple of (min_rules, max_rules) for this strategy
        """
        pass
    
    @abstractmethod
    def supports_request(self, request: ValidationRequest) -> bool:
        """
        Check if this strategy supports the given validation request.
        
        Args:
            request: ValidationRequest to check
            
        Returns:
            True if strategy can handle this request, False otherwise
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """
        Get human-readable name of this validation strategy.
        
        Returns:
            Strategy name (e.g., "Comprehensive", "Selective")
        """
        pass
    
    @abstractmethod
    def get_workflow_name(self) -> str:
        """
        Get the workflow this strategy is designed for.
        
        Returns:
            Workflow name (e.g., "Kolegium", "AI Writing Flow")
        """
        pass