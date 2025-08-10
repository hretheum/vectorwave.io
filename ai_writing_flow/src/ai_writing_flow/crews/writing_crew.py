"""
Writing Crew - Main crew orchestrating all writing agents

Adds lightweight crew state management for sequential execution:
- Execution state tracking (status, current stage, timestamps)
- Intermediate results persistence per stage
- Failure recording and resume capability from last successful stage
"""

from .research_crew import ResearchCrew
from .audience_crew import AudienceCrew
from .writer_crew import WriterCrew
from .style_crew import StyleCrew
from .quality_crew import QualityCrew
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
import os
import json
from datetime import datetime
import uuid


class WritingCrew:
    """Main crew that orchestrates all writing agents"""
    
    def __init__(self, state_dir: str = ".crew_state"):
        self._research_crew = None
        self._audience_crew = None
        self._writer_crew = None
        self._style_crew = None
        self._quality_crew = None
        # Directory for state persistence
        self._state_dir = state_dir
        os.makedirs(self._state_dir, exist_ok=True)
    
    def research_agent(self):
        """Get or create research crew"""
        if not self._research_crew:
            self._research_crew = ResearchCrew()
        return self._research_crew
    
    def audience_mapper(self):
        """Get or create audience crew"""
        if not self._audience_crew:
            self._audience_crew = AudienceCrew()
        return self._audience_crew
    
    def content_writer(self):
        """Get or create writer crew"""
        if not self._writer_crew:
            self._writer_crew = WriterCrew()
        return self._writer_crew
    
    def style_validator(self):
        """Get or create style crew"""
        if not self._style_crew:
            self._style_crew = StyleCrew()
        return self._style_crew
    
    def quality_controller(self):
        """Get or create quality crew"""
        if not self._quality_crew:
            self._quality_crew = QualityCrew()
        return self._quality_crew

    # ========================
    # Crew State Management
    # ========================

    class Stage(str, Enum):
        RESEARCH = "research"
        AUDIENCE = "audience"
        WRITE = "write"
        STYLE = "style"
        QUALITY = "quality"

    class ExecutionStatus(str, Enum):
        PENDING = "pending"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"

    class CrewExecutionState(BaseModel):
        flow_id: str = Field(default_factory=lambda: f"flow_{uuid.uuid4().hex[:8]}")
        status: "WritingCrew.ExecutionStatus" = Field(default=ExecutionStatus.PENDING)
        current_stage: Optional["WritingCrew.Stage"] = None
        stages_completed: List["WritingCrew.Stage"] = Field(default_factory=list)
        started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
        updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
        inputs: Dict[str, Any] = Field(default_factory=dict)
        results: Dict[str, Any] = Field(default_factory=dict)
        error_message: Optional[str] = None

        def to_json(self) -> str:
            return self.model_dump_json(indent=2)

    def _state_path(self, flow_id: str) -> str:
        return os.path.join(self._state_dir, f"{flow_id}.json")

    def _save_state(self, state: "WritingCrew.CrewExecutionState") -> None:
        state.updated_at = datetime.utcnow().isoformat()
        with open(self._state_path(state.flow_id), "w", encoding="utf-8") as f:
            f.write(state.to_json())

    def load_state(self, flow_id: str) -> Optional["WritingCrew.CrewExecutionState"]:
        path = self._state_path(flow_id)
        if not os.path.exists(path):
            return None
        try:
            data = json.load(open(path, "r", encoding="utf-8"))
            return WritingCrew.CrewExecutionState(**data)
        except Exception:
            return None

    def start_sequential_pipeline(
        self,
        *,
        topic: str,
        platform: str,
        audience_insights: str,
        research_sources_path: str,
        research_context: str,
        writer_depth_level: int = 2,
        styleguide_context: Dict[str, Any] = None,
        quality_sources: Optional[List[Dict[str, str]]] = None,
    ) -> "WritingCrew.CrewExecutionState":
        """Run the end-to-end sequential pipeline with state tracking and persistence.

        Returns the final execution state. If a stage fails, state.status = FAILED and error_message set.
        """
        styleguide_context = styleguide_context or {"platform": platform, "content_type": "article"}
        quality_sources = quality_sources or []

        state = WritingCrew.CrewExecutionState(
            status=WritingCrew.ExecutionStatus.RUNNING,
            inputs={
                "topic": topic,
                "platform": platform,
                "audience_insights": audience_insights,
                "research_sources_path": research_sources_path,
                "writer_depth_level": writer_depth_level,
            },
        )
        self._save_state(state)

        try:
            # 1) Research
            state.current_stage = WritingCrew.Stage.RESEARCH
            self._save_state(state)
            research_result = self.research_agent().execute(
                topic=topic,
                sources_path=research_sources_path,
                context=research_context,
                content_ownership="EXTERNAL",
            )
            state.results[state.current_stage.value] = research_result.model_dump() if hasattr(research_result, "model_dump") else str(research_result)
            state.stages_completed.append(state.current_stage)
            self._save_state(state)

            # 2) Audience
            state.current_stage = WritingCrew.Stage.AUDIENCE
            self._save_state(state)
            audience_alignment = self.audience_mapper().execute(
                topic=topic,
                platform=platform,
                research_summary=state.results[WritingCrew.Stage.RESEARCH.value].get("summary", ""),
                editorial_recommendations="",
            )
            state.results[state.current_stage.value] = audience_alignment.model_dump() if hasattr(audience_alignment, "model_dump") else str(audience_alignment)
            state.stages_completed.append(state.current_stage)
            self._save_state(state)

            # 3) Write
            state.current_stage = WritingCrew.Stage.WRITE
            self._save_state(state)
            draft_content = self.content_writer().execute(
                topic=topic,
                platform=platform,
                audience_insights=audience_insights,
                research_summary=state.results[WritingCrew.Stage.RESEARCH.value].get("summary", ""),
                depth_level=writer_depth_level,
                styleguide_context=styleguide_context,
            )
            state.results[state.current_stage.value] = draft_content.model_dump() if hasattr(draft_content, "model_dump") else str(draft_content)
            state.stages_completed.append(state.current_stage)
            self._save_state(state)

            # 4) Style
            state.current_stage = WritingCrew.Stage.STYLE
            self._save_state(state)
            style_validation = self.style_validator().execute(
                draft=state.results[WritingCrew.Stage.WRITE.value].get("draft", ""),
                styleguide_context=styleguide_context,
            )
            state.results[state.current_stage.value] = style_validation.model_dump() if hasattr(style_validation, "model_dump") else str(style_validation)
            state.stages_completed.append(state.current_stage)
            self._save_state(state)

            # 5) Quality
            state.current_stage = WritingCrew.Stage.QUALITY
            self._save_state(state)
            quality_assessment = self.quality_controller().execute(
                draft=state.results[WritingCrew.Stage.WRITE.value].get("draft", ""),
                sources=quality_sources,
                styleguide_context=styleguide_context,
            )
            state.results[state.current_stage.value] = quality_assessment.model_dump() if hasattr(quality_assessment, "model_dump") else str(quality_assessment)
            state.stages_completed.append(state.current_stage)
            self._save_state(state)

            # Done
            state.current_stage = None
            state.status = WritingCrew.ExecutionStatus.COMPLETED
            self._save_state(state)
            return state

        except Exception as e:
            state.status = WritingCrew.ExecutionStatus.FAILED
            state.error_message = str(e)
            self._save_state(state)
            return state

    def resume_from_last_stage(self, flow_id: str) -> Optional["WritingCrew.CrewExecutionState"]:
        """Attempt to resume a failed or interrupted execution from the next stage."""
        state = self.load_state(flow_id)
        if not state:
            return None
        if state.status == WritingCrew.ExecutionStatus.COMPLETED:
            return state

        # Determine next stage
        stage_order = [
            WritingCrew.Stage.RESEARCH,
            WritingCrew.Stage.AUDIENCE,
            WritingCrew.Stage.WRITE,
            WritingCrew.Stage.STYLE,
            WritingCrew.Stage.QUALITY,
        ]
        completed = set(state.stages_completed)
        remaining = [s for s in stage_order if s not in completed]
        if not remaining:
            state.status = WritingCrew.ExecutionStatus.COMPLETED
            self._save_state(state)
            return state

        # Re-run from first remaining stage using stored inputs/results
        return self.start_sequential_pipeline(
            topic=state.inputs.get("topic", ""),
            platform=state.inputs.get("platform", "general"),
            audience_insights=state.inputs.get("audience_insights", ""),
            research_sources_path=state.inputs.get("research_sources_path", ""),
            research_context="",
            writer_depth_level=state.inputs.get("writer_depth_level", 2),
            styleguide_context={"platform": state.inputs.get("platform", "general"), "content_type": "article"},
            quality_sources=[],
        )