"""StageManager - Manages flow stage execution and completion tracking.

This module provides centralized stage management for CrewAI Flow,
including completion tracking, result storage, and reset functionality.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import logging

from ..models.flow_stage import FlowStage
from ..models.flow_control_state import FlowControlState, StageExecution


logger = logging.getLogger(__name__)


@dataclass
class StageConfig:
    """Configuration for a specific stage."""
    
    stage: FlowStage
    required: bool = True
    timeout_seconds: int = 300  # 5 minutes default
    max_retries: int = 3
    skip_conditions: Optional[List[Callable[[FlowControlState], bool]]] = None
    
    def should_skip(self, state: FlowControlState) -> bool:
        """Check if stage should be skipped based on conditions.
        
        Args:
            state: Current flow state
            
        Returns:
            True if stage should be skipped
        """
        if not self.skip_conditions:
            return False
        
        return any(condition(state) for condition in self.skip_conditions)


class StageManager:
    """Manages flow stage execution and completion tracking.
    
    The StageManager provides centralized control over stage execution,
    including completion tracking, result storage, and reset functionality.
    It works with FlowControlState to maintain consistent flow state.
    """
    
    def __init__(self, flow_state: FlowControlState):
        """Initialize StageManager with flow state.
        
        Args:
            flow_state: FlowControlState instance to manage
        """
        self.flow_state = flow_state
        self.stage_configs: Dict[FlowStage, StageConfig] = {}
        self._current_execution: Optional[StageExecution] = None
        
        # Initialize default stage configurations
        self._initialize_default_configs()
    
    def _initialize_default_configs(self) -> None:
        """Initialize default configurations for all stages."""
        linear_flow = FlowStage.get_linear_flow()
        
        for stage in linear_flow:
            # Default configuration for all stages
            config = StageConfig(
                stage=stage,
                required=True,
                timeout_seconds=300,
                max_retries=3
            )
            
            # Stage-specific configurations
            if stage == FlowStage.RESEARCH:
                config.skip_conditions = [self._has_existing_research]
            elif stage == FlowStage.HUMAN_REVIEW:
                config.skip_conditions = [self._auto_approve_enabled]
            
            self.stage_configs[stage] = config
    
    def _has_existing_research(self, state: FlowControlState) -> bool:
        """Check if research already exists and is valid.
        
        Args:
            state: Flow state to check
            
        Returns:
            True if research can be skipped
        """
        research_result = state.stage_results.get('research')
        return research_result is not None and len(str(research_result)) > 100
    
    def _auto_approve_enabled(self, state: FlowControlState) -> bool:
        """Check if auto-approval is enabled for human review.
        
        Args:
            state: Flow state to check
            
        Returns:
            True if human review can be skipped
        """
        return state.global_context.get('auto_approve', False)
    
    def configure_stage(self, stage: FlowStage, config: StageConfig) -> None:
        """Configure a specific stage.
        
        Args:
            stage: Stage to configure
            config: Configuration for the stage
        """
        self.stage_configs[stage] = config
        logger.info(f"Configured stage {stage} with timeout {config.timeout_seconds}s")
    
    def is_stage_completed(self, stage: FlowStage) -> bool:
        """Check if a stage has been completed successfully.
        
        Args:
            stage: Stage to check
            
        Returns:
            True if stage is completed
        """
        return stage in self.flow_state.completed_stages
    
    def should_skip_stage(self, stage: FlowStage) -> bool:
        """Check if a stage should be skipped.
        
        Args:
            stage: Stage to check
            
        Returns:
            True if stage should be skipped
        """
        if stage not in self.stage_configs:
            return False
        
        config = self.stage_configs[stage]
        
        # Skip if already completed and not required to re-run
        if self.is_stage_completed(stage):
            return True
        
        # Skip if stage-specific conditions are met
        return config.should_skip(self.flow_state)
    
    def start_stage(self, stage: FlowStage) -> StageExecution:
        """Start execution of a stage.
        
        Args:
            stage: Stage to start
            
        Returns:
            StageExecution instance for tracking
            
        Raises:
            ValueError: If stage cannot be started
        """
        if self.should_skip_stage(stage):
            logger.info(f"Skipping stage {stage} - conditions met")
            # Create a fake execution that's already completed
            execution = StageExecution(
                stage=stage,
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                success=True,
                result={'skipped': True}
            )
            return execution
        
        # Check if stage is valid for current flow position
        if not FlowStage.is_valid_transition(self.flow_state.current_stage, stage):
            # Allow starting the current stage
            if stage != self.flow_state.current_stage:
                raise ValueError(f"Cannot start stage {stage} from current stage {self.flow_state.current_stage}")
        
        # Start stage execution tracking
        self._current_execution = self.flow_state.start_stage_execution(stage)
        
        logger.info(f"Started stage {stage} execution")
        return self._current_execution
    
    def complete_stage(self, stage: FlowStage, success: bool = True, 
                      result: Optional[Dict[str, Any]] = None, 
                      error: Optional[str] = None) -> None:
        """Mark a stage as completed.
        
        Args:
            stage: Stage to complete
            success: Whether stage completed successfully
            result: Stage execution result
            error: Error message if failed
        """
        # Find the execution in history
        execution = None
        for exec_item in reversed(self.flow_state.execution_history):
            if exec_item.stage == stage and exec_item.end_time is None:
                execution = exec_item
                break
        
        if execution:
            execution.complete(success=success, result=result, error=error)
        
        if success:
            # Store result in stage results
            if result:
                self.flow_state.stage_results[stage.name.lower()] = result
            
            # Mark stage as completed
            if stage not in self.flow_state.completed_stages:
                self.flow_state.completed_stages.append(stage)
            
            logger.info(f"Completed stage {stage} successfully")
        else:
            logger.error(f"Stage {stage} failed: {error}")
        
        # Update last update time
        self.flow_state.last_update = datetime.now(timezone.utc)
    
    def get_stage_result(self, stage: FlowStage) -> Optional[Dict[str, Any]]:
        """Get the result of a completed stage.
        
        Args:
            stage: Stage to get result for
            
        Returns:
            Stage result or None if not completed
        """
        return self.flow_state.stage_results.get(stage.name.lower())
    
    def reset_stage(self, stage: FlowStage) -> None:
        """Reset a stage for re-execution.
        
        Args:
            stage: Stage to reset
        """
        self.flow_state.reset_stage(stage)
        logger.info(f"Reset stage {stage} for re-execution")
    
    def get_execution_history(self, stage: Optional[FlowStage] = None) -> List[StageExecution]:
        """Get execution history for stages.
        
        Args:
            stage: Specific stage to filter by, or None for all
            
        Returns:
            List of StageExecution objects
        """
        if stage is None:
            return self.flow_state.execution_history
        
        return [exec_item for exec_item in self.flow_state.execution_history 
                if exec_item.stage == stage]
    
    def get_stage_metrics(self, stage: FlowStage) -> Dict[str, Any]:
        """Get metrics for a specific stage.
        
        Args:
            stage: Stage to get metrics for
            
        Returns:
            Dictionary of stage metrics
        """
        executions = self.get_execution_history(stage)
        
        if not executions:
            return {'executions': 0}
        
        successful = [e for e in executions if e.success]
        failed = [e for e in executions if not e.success]
        
        total_duration = sum(
            e.duration_seconds or 0 for e in executions if e.duration_seconds
        )
        
        return {
            'executions': len(executions),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(executions) if executions else 0,
            'total_duration_seconds': total_duration,
            'average_duration_seconds': total_duration / len(executions) if executions else 0,
            'completed': self.is_stage_completed(stage)
        }
    
    def get_overall_metrics(self) -> Dict[str, Any]:
        """Get overall flow execution metrics.
        
        Returns:
            Dictionary of overall metrics
        """
        all_executions = self.flow_state.execution_history
        completed_stages = len(self.flow_state.completed_stages)
        total_stages = len(FlowStage.get_linear_flow())
        
        return {
            'total_executions': len(all_executions),
            'completed_stages': completed_stages,
            'total_stages': total_stages,
            'completion_percentage': (completed_stages / total_stages) * 100 if total_stages else 0,
            'total_retries': self.flow_state.total_retries,
            'execution_duration_seconds': self.flow_state.get_execution_duration(),
            'current_stage': self.flow_state.current_stage.name,
            'is_completed': self.flow_state.is_completed()
        }
    
    def cleanup_history(self, keep_last_n: int = 100) -> None:
        """Clean up execution history to prevent memory bloat.
        
        Args:
            keep_last_n: Number of recent executions to keep
        """
        if len(self.flow_state.execution_history) > keep_last_n:
            # Keep the most recent executions
            self.flow_state.execution_history = self.flow_state.execution_history[-keep_last_n:]
            logger.info(f"Cleaned up execution history, kept last {keep_last_n} executions")
