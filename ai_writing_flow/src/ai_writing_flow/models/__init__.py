"""Models package for FlowControlState and related models."""

from .flow_stage import FlowStage
from .flow_control_state import FlowControlState
from .stage_execution import StageExecution

# Import legacy models from parent module for compatibility
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, parent_dir)

try:
    from models import WritingFlowState, HumanFeedbackDecision
except ImportError:
    # Fallback - create minimal compatibility models
    from pydantic import BaseModel, Field
    from typing import List, Dict, Any, Optional, Literal
    from datetime import datetime
    
    class WritingFlowState(BaseModel):
        """Legacy WritingFlowState compatibility model"""
        topic_title: str = ""
        platform: str = ""
        file_path: str = ""
        source_files: List[str] = Field(default_factory=list)
        content_type: str = "STANDALONE"
        content_ownership: str = "EXTERNAL"
        viral_score: float = 0.0
        editorial_recommendations: str = ""
        skip_research: bool = False
        human_feedback_type: Optional[str] = None
        current_stage: str = "initialized"
        research_sources: List[Dict[str, str]] = Field(default_factory=list) 
        research_summary: str = ""
        audience_scores: Dict[str, float] = Field(default_factory=dict)
        audience_insights: str = ""
        target_depth_level: int = 1
        draft_versions: List[str] = Field(default_factory=list)
        current_draft: str = ""
        human_feedback: Optional[str] = None
        style_violations: List[Dict[str, str]] = Field(default_factory=list)
        forbidden_phrases_found: List[str] = Field(default_factory=list)
        style_score: float = 0.0
        quality_score: float = 0.0
        quality_issues: List[str] = Field(default_factory=list)
        revision_count: int = 0
        final_draft: str = ""
        platform_variants: Dict[str, str] = Field(default_factory=dict)
        publication_metadata: Dict[str, Any] = Field(default_factory=dict)
        final_output: Optional[Dict[str, Any]] = None
        flow_start_time: datetime = Field(default_factory=datetime.now)
        total_processing_time: float = 0.0
        agents_executed: List[str] = Field(default_factory=list)
    
    class HumanFeedbackDecision(BaseModel):
        """Legacy HumanFeedbackDecision compatibility model"""
        feedback_text: str = ""
        feedback_type: str = ""

__all__ = [
    "FlowStage", 
    "FlowControlState", 
    "StageExecution",
    "WritingFlowState",
    "HumanFeedbackDecision"
]
