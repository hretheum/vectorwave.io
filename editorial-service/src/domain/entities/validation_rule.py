"""
Domain Entity: ValidationRule
Core business entity representing a validation rule from ChromaDB.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class RuleSeverity(Enum):
    """Severity levels for validation rules"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RuleType(Enum):
    """Types of validation rules"""
    STYLE = "style"
    EDITORIAL = "editorial"
    PLATFORM = "platform"
    CONTENT = "content"
    TECHNICAL = "technical"


@dataclass(frozen=True)
class ValidationRule:
    """
    Immutable domain entity representing a validation rule.
    
    All validation rules must originate from ChromaDB - no hardcoded rules allowed.
    """
    rule_id: str
    rule_name: str
    rule_type: RuleType
    description: str
    severity: RuleSeverity
    collection_source: str
    chromadb_origin_metadata: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate rule integrity"""
        if not self.rule_id:
            raise ValueError("Rule ID cannot be empty")
        
        if not self.chromadb_origin_metadata:
            raise ValueError("ChromaDB origin metadata is required - no hardcoded rules allowed")
        
        # Ensure ChromaDB metadata contains required fields
        required_metadata = {'collection_name', 'document_id', 'timestamp'}
        if not all(key in self.chromadb_origin_metadata for key in required_metadata):
            raise ValueError(f"ChromaDB metadata must contain: {required_metadata}")
    
    def is_critical(self) -> bool:
        """Check if rule is critical severity"""
        return self.severity == RuleSeverity.CRITICAL
    
    def is_platform_specific(self) -> bool:
        """Check if rule is platform-specific"""
        return self.rule_type == RuleType.PLATFORM
    
    def get_origin_collection(self) -> str:
        """Get the ChromaDB collection this rule originated from"""
        return self.chromadb_origin_metadata.get('collection_name', '')
    
    def get_document_id(self) -> str:
        """Get the ChromaDB document ID this rule originated from"""
        return self.chromadb_origin_metadata.get('document_id', '')