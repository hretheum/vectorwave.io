#!/usr/bin/env python
"""
AI Writing Flow - Content generation with styleguide compliance and human-in-the-loop
"""

import os
import logging
from typing import Optional
from datetime import datetime

from crewai.flow import Flow, listen, start, router
from pydantic import BaseModel
from dotenv import load_dotenv

from ai_writing_flow.models import WritingFlowState, HumanFeedbackDecision
from ai_writing_flow.crews.writing_crew import WritingCrew
from ai_writing_flow.tools.styleguide_loader import load_styleguide_context
from ai_writing_flow.utils.ui_bridge import UIBridge

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIWritingFlow(Flow[WritingFlowState]):
    """Main flow for AI content writing with human feedback loop"""
    
    def __init__(self):
        super().__init__()
        self.crew = WritingCrew()
        self.ui_bridge = UIBridge()
        self.styleguide_context = load_styleguide_context()
        
    @start()
    def receive_topic(self):
        """Receive topic selection from Kolegium"""
        logger.info(f"📝 Starting Writing Flow for: {self.state.topic_title}")
        logger.info(f"🎯 Platform: {self.state.platform}")
        logger.info(f"📊 Viral Score: {self.state.viral_score}")
        logger.info(f"🏷️ Content Type: {self.state.content_ownership}")
        
        self.state.current_stage = "topic_received"
        self.state.agents_executed.append("flow_initialized")
        
        # Check if we should skip research
        if self.state.content_ownership == "ORIGINAL" or self.state.skip_research:
            logger.info("⏭️ Skipping research phase for ORIGINAL content")
            return "skip_research"
        
        return "conduct_research"
    
    @router(receive_topic)
    def route_after_topic(self):
        """Route based on content ownership"""
        if self.state.content_ownership == "ORIGINAL" or self.state.skip_research:
            return "align_audience"
        return "conduct_research"
    
    @listen("conduct_research")
    def conduct_research(self):
        """Deep content research for EXTERNAL content"""
        logger.info("🔍 Conducting deep research...")
        self.state.current_stage = "research"
        self.state.agents_executed.append("research_agent")
        
        result = self.crew.research_agent().execute(
            topic=self.state.topic_title,
            sources_path=self.state.folder_path,
            context=self.styleguide_context
        )
        
        self.state.research_sources = result.sources
        self.state.research_summary = result.summary
        
        return "align_audience"
    
    @listen("align_audience", "skip_research")
    def align_audience(self):
        """Align content with target audiences"""
        logger.info("👥 Aligning with target audiences...")
        self.state.current_stage = "audience_alignment"
        self.state.agents_executed.append("audience_mapper")
        
        result = self.crew.audience_mapper().execute(
            topic=self.state.topic_title,
            platform=self.state.platform,
            research_summary=self.state.research_summary,
            editorial_recommendations=self.state.editorial_recommendations
        )
        
        self.state.audience_scores = {
            "technical_founder": result.technical_founder_score,
            "senior_engineer": result.senior_engineer_score,
            "decision_maker": result.decision_maker_score,
            "skeptical_learner": result.skeptical_learner_score
        }
        self.state.target_depth_level = result.recommended_depth
        
        return "generate_draft"
    
    @listen("generate_draft")
    def generate_draft(self):
        """Generate initial draft"""
        logger.info("✍️ Generating draft...")
        self.state.current_stage = "draft_generation"
        self.state.agents_executed.append("content_writer")
        
        result = self.crew.content_writer().execute(
            topic=self.state.topic_title,
            platform=self.state.platform,
            audience_insights=self.state.audience_insights,
            research_summary=self.state.research_summary,
            depth_level=self.state.target_depth_level,
            styleguide_context=self.styleguide_context
        )
        
        self.state.current_draft = result.draft
        self.state.draft_versions.append(result.draft)
        
        # Send draft to UI for human review
        logger.info("👤 Sending draft for human review...")
        self.ui_bridge.send_draft_for_review(
            draft=result.draft,
            metadata={
                "word_count": result.word_count,
                "structure_type": result.structure_type,
                "non_obvious_insights": result.non_obvious_insights
            }
        )
        
        return "await_human_feedback"
    
    @listen("await_human_feedback")
    def await_human_feedback(self):
        """Wait for human feedback on draft"""
        logger.info("⏳ Awaiting human feedback...")
        self.state.current_stage = "human_review"
        
        # This would normally wait for UI callback
        # For now, we'll simulate the feedback
        feedback = self.ui_bridge.get_human_feedback()
        
        if feedback:
            self.state.human_feedback = feedback.feedback_text
            self.state.human_feedback_type = feedback.feedback_type
            
            return f"process_{feedback.feedback_type}_feedback"
        
        # No feedback means approve as-is
        return "validate_style"
    
    @router(await_human_feedback)
    def route_human_feedback(self):
        """Route based on human feedback type"""
        if not self.state.human_feedback_type:
            return "validate_style"
        
        feedback_routes = {
            "minor": "validate_style",      # Minor edits -> style check
            "major": "align_audience",       # Content changes -> re-align
            "pivot": "conduct_research"      # Direction change -> research
        }
        
        # For ORIGINAL content, skip research even on pivot
        if self.state.human_feedback_type == "pivot" and self.state.content_ownership == "ORIGINAL":
            return "align_audience"
        
        return feedback_routes.get(self.state.human_feedback_type, "validate_style")
    
    @listen("validate_style")
    def validate_style(self):
        """Validate against style guide"""
        logger.info("📏 Validating style compliance...")
        self.state.current_stage = "style_validation"
        self.state.agents_executed.append("style_validator")
        
        result = self.crew.style_validator().execute(
            draft=self.state.current_draft,
            styleguide_context=self.styleguide_context
        )
        
        self.state.style_violations = result.violations
        self.state.forbidden_phrases_found = result.forbidden_phrases
        self.state.style_score = result.compliance_score
        
        if not result.is_compliant:
            logger.warning(f"❌ Style violations found: {len(result.violations)}")
            self.state.revision_count += 1
            
            if self.state.revision_count > 3:
                logger.error("🚨 Max revisions reached, escalating to human")
                self.ui_bridge.escalate_to_human("Max revision attempts")
                return "finalize_output"
            
            return "generate_draft"  # Retry with feedback
        
        return "quality_check"
    
    @listen("quality_check")
    def quality_check(self):
        """Final quality assessment"""
        logger.info("✅ Running quality check...")
        self.state.current_stage = "quality_assessment"
        self.state.agents_executed.append("quality_controller")
        
        result = self.crew.quality_controller().execute(
            draft=self.state.current_draft,
            sources=self.state.research_sources,
            styleguide_context=self.styleguide_context
        )
        
        self.state.quality_score = result.quality_score
        self.state.quality_issues = result.improvement_suggestions
        
        if not result.is_approved or result.requires_human_review:
            logger.warning("🚨 Quality check failed or requires human review")
            self.ui_bridge.request_human_review(result)
            return "await_human_feedback"
        
        return "finalize_output"
    
    @listen("finalize_output")
    def finalize_output(self):
        """Prepare final output package"""
        logger.info("📦 Finalizing output...")
        self.state.current_stage = "completed"
        
        self.state.final_draft = self.state.current_draft
        self.state.total_processing_time = (
            datetime.now() - self.state.flow_start_time
        ).total_seconds()
        
        # Prepare metadata
        self.state.publication_metadata = {
            "topic": self.state.topic_title,
            "platform": self.state.platform,
            "viral_score": self.state.viral_score,
            "quality_score": self.state.quality_score,
            "style_score": self.state.style_score,
            "audience_alignment": self.state.audience_scores,
            "revision_count": self.state.revision_count,
            "processing_time": self.state.total_processing_time,
            "agents_executed": self.state.agents_executed
        }
        
        logger.info("✨ Writing Flow completed successfully!")
        self.ui_bridge.send_completion_notice(self.state)
        
        return self.state


def kickoff():
    """Entry point for the flow"""
    # Example input from Kolegium
    initial_state = WritingFlowState(
        topic_title="The Rise of AI Agents in Software Development",
        platform="LinkedIn",
        folder_path="/content/raw/2024-ai-agents",
        content_type="STANDALONE",
        content_ownership="EXTERNAL",
        viral_score=8.5,
        editorial_recommendations="Focus on practical examples and ROI"
    )
    
    flow = AIWritingFlow()
    flow.kickoff(initial_state)


def plot():
    """Generate flow diagram"""
    flow = AIWritingFlow()
    flow.plot("ai_writing_flow_diagram.png")


if __name__ == "__main__":
    kickoff()
