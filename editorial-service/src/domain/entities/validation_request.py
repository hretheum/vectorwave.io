"""
Domain Entity: ValidationRequest
Represents a request for content validation with specific workflow mode.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class ValidationMode(Enum):
    """Validation modes for dual workflow support"""
    COMPREHENSIVE = "comprehensive"  # Kolegium - Full AI validation (8-12 rules)
    SELECTIVE = "selective"          # AI Writing Flow - Human-assisted (3-4 rules)


class CheckpointType(Enum):
    """Checkpoint types for selective validation mode"""
    PRE_WRITING = "pre-writing"      # Before content creation
    MID_WRITING = "mid-writing"      # During content creation  
    POST_WRITING = "post-writing"    # After content creation


@dataclass(frozen=True)
class ValidationRequest:
    """
    Immutable validation request containing content and workflow parameters.
    
    Supports dual workflow architecture:
    - Kolegium: comprehensive validation with all applicable rules
    - AI Writing Flow: selective validation at specific checkpoints
    """
    content: str
    mode: ValidationMode
    checkpoint: Optional[CheckpointType] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate request integrity"""
        if not self.content.strip():
            raise ValueError("Content cannot be empty")
        
        # Selective mode requires checkpoint
        if self.mode == ValidationMode.SELECTIVE and self.checkpoint is None:
            raise ValueError("Selective validation mode requires a checkpoint type")
        
        # Comprehensive mode should not specify checkpoint
        if self.mode == ValidationMode.COMPREHENSIVE and self.checkpoint is not None:
            raise ValueError("Comprehensive validation mode should not specify checkpoint")
    
    def is_comprehensive(self) -> bool:
        """Check if request is for comprehensive validation (Kolegium)"""
        return self.mode == ValidationMode.COMPREHENSIVE
    
    def is_selective(self) -> bool:
        """Check if request is for selective validation (AI Writing Flow)"""
        return self.mode == ValidationMode.SELECTIVE
    
    def get_expected_rule_count_range(self) -> tuple[int, int]:
        """Get expected range of rules for this validation mode"""
        if self.is_comprehensive():
            return (8, 12)  # Kolegium: comprehensive validation
        else:
            return (3, 4)   # AI Writing Flow: selective validation
    
    def get_workflow_name(self) -> str:
        """Get human-readable workflow name"""
        return "Kolegium" if self.is_comprehensive() else "AI Writing Flow"