"""
Application Service: ValidationStrategyFactory
Factory for creating appropriate validation strategies based on mode.
"""
from typing import Dict, Type
import structlog

from ...domain.entities import ValidationMode
from ...domain.interfaces import IValidationStrategy, IRuleRepository
from ..strategies import ComprehensiveStrategy, SelectiveStrategy

logger = structlog.get_logger()


class ValidationStrategyFactory:
    """
    Factory for creating validation strategies based on validation mode.
    
    Implements Factory pattern to abstract strategy creation and ensure
    clean separation between workflow types.
    
    Supported strategies:
    - 'comprehensive': ComprehensiveStrategy for Kolegium workflow
    - 'selective': SelectiveStrategy for AI Writing Flow workflow
    """
    
    def __init__(self, rule_repository: IRuleRepository):
        """
        Initialize factory with rule repository.
        
        Args:
            rule_repository: Repository for accessing ChromaDB rules
        """
        self.rule_repository = rule_repository
        
        # Strategy registry mapping mode to strategy class
        self._strategies: Dict[ValidationMode, Type[IValidationStrategy]] = {
            ValidationMode.COMPREHENSIVE: ComprehensiveStrategy,
            ValidationMode.SELECTIVE: SelectiveStrategy
        }
        
        logger.info(
            "ValidationStrategyFactory initialized",
            strategies_available=list(mode.value for mode in self._strategies.keys())
        )
    
    def create(self, mode: str) -> IValidationStrategy:
        """
        Create validation strategy for specified mode.
        
        Args:
            mode: Validation mode string ('comprehensive' or 'selective')
            
        Returns:
            Concrete IValidationStrategy implementation
            
        Raises:
            ValueError: If mode is not supported
            
        Examples:
            >>> factory = ValidationStrategyFactory(repo)
            >>> strategy = factory.create('comprehensive')
            >>> isinstance(strategy, ComprehensiveStrategy)
            True
            
            >>> strategy = factory.create('selective')  
            >>> isinstance(strategy, SelectiveStrategy)
            True
        """
        # Convert string to ValidationMode enum
        try:
            validation_mode = ValidationMode(mode.lower())
        except ValueError:
            available_modes = [mode.value for mode in ValidationMode]
            raise ValueError(
                f"Unsupported validation mode: '{mode}'. "
                f"Available modes: {available_modes}"
            )
        
        # Get strategy class from registry
        strategy_class = self._strategies.get(validation_mode)
        if strategy_class is None:
            raise ValueError(
                f"No strategy implementation found for mode: {validation_mode.value}"
            )
        
        # Create and return strategy instance
        strategy = strategy_class(self.rule_repository)
        
        logger.info(
            "Validation strategy created",
            mode=validation_mode.value,
            strategy_class=strategy_class.__name__,
            workflow=strategy.get_workflow_name()
        )
        
        return strategy
    
    def get_available_modes(self) -> list[str]:
        """
        Get list of available validation modes.
        
        Returns:
            List of mode strings that can be used with create()
        """
        return [mode.value for mode in self._strategies.keys()]
    
    def is_mode_supported(self, mode: str) -> bool:
        """
        Check if validation mode is supported.
        
        Args:
            mode: Validation mode string to check
            
        Returns:
            True if mode is supported, False otherwise
        """
        try:
            ValidationMode(mode.lower())
            return True
        except ValueError:
            return False
    
    def get_strategy_info(self, mode: str) -> dict:
        """
        Get information about strategy for given mode.
        
        Args:
            mode: Validation mode string
            
        Returns:
            Dictionary with strategy information
            
        Raises:
            ValueError: If mode is not supported
        """
        if not self.is_mode_supported(mode):
            raise ValueError(f"Unsupported validation mode: '{mode}'")
        
        validation_mode = ValidationMode(mode.lower())
        strategy_class = self._strategies[validation_mode]
        
        # Create temporary instance to get info (without expensive initialization)
        temp_strategy = strategy_class(self.rule_repository)
        
        return {
            'mode': validation_mode.value,
            'strategy_name': temp_strategy.get_strategy_name(),
            'workflow_name': temp_strategy.get_workflow_name(),
            'expected_rule_range': temp_strategy.get_expected_rule_count_range(),
            'class_name': strategy_class.__name__
        }