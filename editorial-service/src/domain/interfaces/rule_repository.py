"""
Domain Interface: IRuleRepository
Abstract interface for rule repository implementing Repository pattern.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from ..entities import ValidationRule, RuleType, RuleSeverity, CheckpointType


class IRuleRepository(ABC):
    """
    Abstract interface for rule repository.
    
    Implements Repository pattern to abstract ChromaDB access.
    All rules must be sourced from ChromaDB - no hardcoded rules allowed.
    """
    
    @abstractmethod
    async def get_comprehensive_rules(self, content: str) -> List[ValidationRule]:
        """
        Get comprehensive rule set for Kolegium workflow.
        
        Returns 8-12 rules covering all validation aspects.
        
        Args:
            content: Content to validate (for context-specific rules)
            
        Returns:
            List of ValidationRule objects from ChromaDB (8-12 rules)
        """
        pass
    
    @abstractmethod
    async def get_selective_rules(
        self, 
        content: str, 
        checkpoint: CheckpointType
    ) -> List[ValidationRule]:
        """
        Get selective rule set for AI Writing Flow workflow.
        
        Returns 3-4 rules specific to the checkpoint.
        
        Args:
            content: Content to validate
            checkpoint: Specific checkpoint (pre/mid/post writing)
            
        Returns:
            List of ValidationRule objects from ChromaDB (3-4 rules)
        """
        pass
    
    @abstractmethod
    async def get_rules_by_type(
        self, 
        rule_type: RuleType,
        limit: Optional[int] = None
    ) -> List[ValidationRule]:
        """
        Get rules filtered by type.
        
        Args:
            rule_type: Type of rules to retrieve
            limit: Maximum number of rules to return
            
        Returns:
            List of ValidationRule objects matching the type
        """
        pass
    
    @abstractmethod
    async def get_rules_by_severity(
        self, 
        severity: RuleSeverity,
        limit: Optional[int] = None
    ) -> List[ValidationRule]:
        """
        Get rules filtered by severity level.
        
        Args:
            severity: Severity level to filter by
            limit: Maximum number of rules to return
            
        Returns:
            List of ValidationRule objects matching the severity
        """
        pass
    
    @abstractmethod
    async def search_rules(
        self, 
        query: str, 
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ValidationRule]:
        """
        Search rules using semantic search.
        
        Args:
            query: Search query for semantic matching
            limit: Maximum number of results
            filters: Optional filters (type, severity, collection, etc.)
            
        Returns:
            List of ValidationRule objects matching the search
        """
        pass
    
    @abstractmethod
    async def get_rule_by_id(self, rule_id: str) -> Optional[ValidationRule]:
        """
        Get specific rule by its ID.
        
        Args:
            rule_id: Unique identifier for the rule
            
        Returns:
            ValidationRule if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about ChromaDB collections.
        
        Returns:
            Dictionary with collection names, counts, and health status
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if repository connection is healthy.
        
        Returns:
            True if connection is working, False otherwise
        """
        pass