"""
Domain Entity: ValidationResponse
Represents the result of a validation operation.
"""
from dataclasses import dataclass
from typing import List
from datetime import datetime

from .validation_rule import ValidationRule
from .validation_request import ValidationMode, CheckpointType


@dataclass(frozen=True)
class ValidationResponse:
    """
    Immutable validation response containing applied rules and metadata.
    
    Provides transparency about which rules were applied and their ChromaDB origin.
    """
    mode: ValidationMode
    checkpoint: CheckpointType | None
    rules_applied: List[ValidationRule]
    processing_time_ms: float
    timestamp: datetime
    metadata: dict = None
    
    def __post_init__(self):
        """Validate response integrity"""
        if self.processing_time_ms < 0:
            raise ValueError("Processing time cannot be negative")
        
        # Validate rule count expectations
        expected_min, expected_max = self._get_expected_rule_count()
        actual_count = len(self.rules_applied)
        
        if not (expected_min <= actual_count <= expected_max):
            raise ValueError(
                f"Rule count {actual_count} outside expected range "
                f"[{expected_min}-{expected_max}] for mode {self.mode.value}"
            )
    
    def _get_expected_rule_count(self) -> tuple[int, int]:
        """Get expected rule count range for validation mode"""
        if self.mode == ValidationMode.COMPREHENSIVE:
            return (8, 12)  # Kolegium: comprehensive validation
        else:
            return (3, 4)   # AI Writing Flow: selective validation
    
    @property
    def rule_count(self) -> int:
        """Get the number of rules applied"""
        return len(self.rules_applied)
    
    @property
    def is_comprehensive(self) -> bool:
        """Check if this was a comprehensive validation"""
        return self.mode == ValidationMode.COMPREHENSIVE
    
    @property
    def is_selective(self) -> bool:
        """Check if this was a selective validation"""
        return self.mode == ValidationMode.SELECTIVE
    
    def get_critical_rules(self) -> List[ValidationRule]:
        """Get only critical severity rules"""
        return [rule for rule in self.rules_applied if rule.is_critical()]
    
    def get_rules_by_type(self, rule_type: str) -> List[ValidationRule]:
        """Get rules filtered by type"""
        return [rule for rule in self.rules_applied if rule.rule_type.value == rule_type]
    
    def get_chromadb_collections_used(self) -> set[str]:
        """Get set of ChromaDB collections that provided rules"""
        return {rule.get_origin_collection() for rule in self.rules_applied}
    
    def has_platform_specific_rules(self) -> bool:
        """Check if response contains platform-specific rules"""
        return any(rule.is_platform_specific() for rule in self.rules_applied)
    
    def get_workflow_name(self) -> str:
        """Get human-readable workflow name"""
        return "Kolegium" if self.is_comprehensive else "AI Writing Flow"