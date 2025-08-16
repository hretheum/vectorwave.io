"""Models package for FlowControlState and related models."""

from .flow_stage import FlowStage
from .flow_control_state import FlowControlState
from .stage_execution import StageExecution

# Import models from parent module for compatibility
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, parent_dir)

try:
    from models import (
        WritingFlowState, 
        HumanFeedbackDecision,
        ResearchResult,
        AudienceAlignment,
        DraftContent,
        StyleValidation,
        QualityAssessment,
        ContentAnalysisResult,
        MultiPlatformRequest,
        MultiPlatformResponse,
        LinkedInPromptRequest,
        LinkedInPromptResponse,
        ContentGenerationMetrics
    )
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
        error_message: str = ""  # Added for V2 compatibility
    
    class HumanFeedbackDecision(BaseModel):
        """Legacy HumanFeedbackDecision compatibility model"""
        feedback_text: str = ""
        feedback_type: str = ""
    
    class ResearchResult(BaseModel):
        """Research result model"""
        sources: List[Dict[str, str]] = Field(default_factory=list)
        summary: str = ""
        key_insights: List[str] = Field(default_factory=list)
        data_points: List[Dict[str, Any]] = Field(default_factory=list)
        methodology: str = ""
    
    class AudienceAlignment(BaseModel):
        """Audience alignment model"""
        technical_founder_score: float = 0.0
        senior_engineer_score: float = 0.0
        decision_maker_score: float = 0.0
        skeptical_learner_score: float = 0.0
        recommended_depth: int = 1
        tone_calibration: str = ""
        key_messages: Dict[str, str] = Field(default_factory=dict)
    
    class DraftContent(BaseModel):
        """Draft content model"""
        title: str = ""
        draft: str = ""
        word_count: int = 0
        structure_type: str = "deep_analysis"
        key_sections: List[str] = Field(default_factory=list)
        non_obvious_insights: List[str] = Field(default_factory=list)
    
    class StyleValidation(BaseModel):
        """Style validation model"""
        is_compliant: bool = True
        violations: List[Dict[str, str]] = Field(default_factory=list)
        forbidden_phrases: List[str] = Field(default_factory=list)
        suggestions: List[str] = Field(default_factory=list)
        compliance_score: float = 100.0
    
    class QualityAssessment(BaseModel):
        """Quality assessment model"""
        is_approved: bool = True
        quality_score: float = 100.0
        fact_check_results: List[Dict[str, str]] = Field(default_factory=list)
        code_verification: Optional[Dict[str, str]] = None
        ethics_checklist: Dict[str, bool] = Field(default_factory=dict)
        improvement_suggestions: List[str] = Field(default_factory=list)
        requires_human_review: bool = False
        controversy_score: float = 0.0

    class ContentAnalysisResult(BaseModel):
        """Content analysis result model"""
        content_type: str = ""
        viral_score: float = 0.0
        complexity_level: str = "intermediate"
        recommended_flow_path: str = "standard_content_flow"
        kb_insights: List[str] = Field(default_factory=list)
        processing_time: float = 0.0
        target_platform: str = ""
        analysis_confidence: float = 0.8
        key_themes: List[str] = Field(default_factory=list)
        audience_indicators: Dict[str, Any] = Field(default_factory=dict)
        content_structure: Dict[str, Any] = Field(default_factory=dict)
        kb_available: bool = True
        search_strategy_used: str = "HYBRID"
        kb_query_count: int = 0
    
    # PHASE 4.5.3: Enhanced models for Platform Optimizer integration
    class MultiPlatformRequest(BaseModel):
        """Request model for multi-platform content generation"""
        topic: Dict[str, Any] = Field(..., description="Topic information")
        platforms: Dict[str, Dict[str, Any]] = Field(..., description="Platform configurations")
        request_id: Optional[str] = Field(default=None, description="Request tracking ID")
        priority: int = Field(default=5, ge=1, le=10, description="Processing priority")
    
    class MultiPlatformResponse(BaseModel):
        """Response model for multi-platform content generation"""
        request_id: str = Field(..., description="Request tracking ID")
        platform_content: Dict[str, Any] = Field(..., description="Generated content per platform")
        generation_time: float = Field(..., description="Total generation time")
        success_count: int = Field(..., description="Number of successful generations")
        error_count: int = Field(..., description="Number of failed generations")
        metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    
    class LinkedInPromptRequest(BaseModel):
        """Request model for LinkedIn carousel prompt generation"""
        topic: Dict[str, Any] = Field(..., description="Topic information")
        slides_count: int = Field(default=5, ge=3, le=10, description="Number of slides")
        template: str = Field(default="business", description="Presentation template")
        enhanced_mode: bool = Field(default=True, description="Use enhanced AI features")
    
    class LinkedInPromptResponse(BaseModel):
        """Response model for LinkedIn carousel prompt generation"""
        prompt: str = Field(..., description="Generated presentation prompt")
        slides_count: int = Field(..., description="Target slides count")
        template_used: str = Field(..., description="Template used")
        ready_for_presenton: bool = Field(default=True, description="Ready for Presenton service")
        generation_time: float = Field(..., description="Generation time")
        metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    
    class ContentGenerationMetrics(BaseModel):
        """Metrics for content generation tracking"""
        total_requests: int = Field(default=0, description="Total requests processed")
        successful_generations: int = Field(default=0, description="Successful generations")
        failed_generations: int = Field(default=0, description="Failed generations")
        average_generation_time: float = Field(default=0.0, description="Average generation time")
        platform_usage: Dict[str, int] = Field(default={}, description="Usage per platform")
        quality_scores: List[float] = Field(default=[], description="Quality score history")

__all__ = [
    "FlowStage", 
    "FlowControlState", 
    "StageExecution",
    "WritingFlowState",
    "HumanFeedbackDecision",
    "ResearchResult",
    "AudienceAlignment", 
    "DraftContent",
    "StyleValidation",
    "QualityAssessment",
    "ContentAnalysisResult",
    "MultiPlatformRequest",
    "MultiPlatformResponse",
    "LinkedInPromptRequest",
    "LinkedInPromptResponse",
    "ContentGenerationMetrics"
]
