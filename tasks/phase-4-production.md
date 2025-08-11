# PHASE 4: Orchestration & Production

## 📋 Bloki Zadań Atomowych

### Blok 13: Orchestration Domain
**Czas**: 3h | **Agent**: project-coder | **Dependencies**: Phase 3 complete

**Task 4.0**: Orchestration domain implementation

#### Execution Steps:
1. **Create orchestration domain structure** (lokalnie!)
   ```bash
   cd /Users/hretheum/dev/bezrobocie/vector-wave/kolegium
   mkdir -p src/domains/orchestration/{domain/{entities,value_objects,repositories,services},application/{use_cases,handlers,dto},infrastructure/{repositories,services,agents}}
   ```

2. **Define workflow entities**
   ```python
   # src/domains/orchestration/domain/entities/workflow.py
   from dataclasses import dataclass
   from datetime import datetime
   from typing import List, Dict, Optional, Any
   from uuid import UUID, uuid4
   from enum import Enum
   
   class WorkflowStatus(Enum):
       PENDING = "pending"
       RUNNING = "running"
       COMPLETED = "completed"
       FAILED = "failed"
       CANCELLED = "cancelled"
   
   class TaskStatus(Enum):
       WAITING = "waiting"
       ASSIGNED = "assigned"
       IN_PROGRESS = "in_progress"
       COMPLETED = "completed"
       FAILED = "failed"
       SKIPPED = "skipped"
   
   @dataclass
   class WorkflowTask:
       id: UUID
       agent_id: Optional[UUID]
       agent_type: str
       name: str
       description: str
       input_data: Dict[str, Any]
       output_data: Optional[Dict[str, Any]] = None
       status: TaskStatus = TaskStatus.WAITING
       dependencies: List[UUID] = None
       started_at: Optional[datetime] = None
       completed_at: Optional[datetime] = None
       error_message: Optional[str] = None
       
       def __post_init__(self):
           if self.dependencies is None:
               self.dependencies = []
               
       def can_start(self, completed_tasks: List[UUID]) -> bool:
           """Check if all dependencies are completed"""
           return all(dep_id in completed_tasks for dep_id in self.dependencies)
   
   @dataclass
   class Workflow:
       id: UUID
       name: str
       description: str
       tasks: List[WorkflowTask]
       status: WorkflowStatus
       created_at: datetime
       started_at: Optional[datetime] = None
       completed_at: Optional[datetime] = None
       created_by: str = "system"
       metadata: Dict[str, Any] = None
       
       def __post_init__(self):
           if self.metadata is None:
               self.metadata = {}
               
       @classmethod
       def create(cls, name: str, description: str, 
                  tasks: List[WorkflowTask], created_by: str) -> 'Workflow':
           return cls(
               id=uuid4(),
               name=name,
               description=description,
               tasks=tasks,
               status=WorkflowStatus.PENDING,
               created_at=datetime.utcnow(),
               created_by=created_by
           )
           
       def get_next_tasks(self) -> List[WorkflowTask]:
           """Get tasks that can be started"""
           completed_task_ids = [
               task.id for task in self.tasks 
               if task.status == TaskStatus.COMPLETED
           ]
           
           return [
               task for task in self.tasks
               if task.status == TaskStatus.WAITING
               and task.can_start(completed_task_ids)
           ]
   ```

3. **Create task coordination entities**
   ```python
   # src/domains/orchestration/domain/entities/task_coordination.py
   from dataclasses import dataclass
   from datetime import datetime
   from typing import List, Dict, Optional, Any
   from uuid import UUID, uuid4
   
   @dataclass
   class AgentAssignment:
       id: UUID
       task_id: UUID
       agent_id: UUID
       agent_type: str
       assigned_at: datetime
       priority: int = 0
       context: Dict[str, Any] = None
       
       def __post_init__(self):
           if self.context is None:
               self.context = {}
   
   @dataclass
   class ConsensusRequest:
       id: UUID
       workflow_id: UUID
       topic: str
       agents_involved: List[UUID]
       responses: Dict[UUID, Dict[str, Any]]
       consensus_type: str  # majority, unanimous, weighted
       deadline: datetime
       created_at: datetime
       result: Optional[Dict[str, Any]] = None
       
       @classmethod
       def create(cls, workflow_id: UUID, topic: str,
                  agents: List[UUID], consensus_type: str,
                  deadline: datetime) -> 'ConsensusRequest':
           return cls(
               id=uuid4(),
               workflow_id=workflow_id,
               topic=topic,
               agents_involved=agents,
               responses={},
               consensus_type=consensus_type,
               deadline=deadline,
               created_at=datetime.utcnow()
           )
           
       def add_response(self, agent_id: UUID, response: Dict[str, Any]):
           """Add agent response"""
           self.responses[agent_id] = response
           
       def has_all_responses(self) -> bool:
           """Check if all agents responded"""
           return set(self.agents_involved) == set(self.responses.keys())
           
       def calculate_consensus(self) -> Dict[str, Any]:
           """Calculate consensus based on type"""
           if not self.has_all_responses():
               return {"consensus": False, "reason": "Missing responses"}
               
           if self.consensus_type == "unanimous":
               # All must agree
               decisions = [r.get("decision") for r in self.responses.values()]
               if len(set(decisions)) == 1:
                   return {
                       "consensus": True,
                       "decision": decisions[0],
                       "confidence": 1.0
                   }
               return {"consensus": False, "reason": "No unanimous agreement"}
               
           elif self.consensus_type == "majority":
               # Simple majority
               from collections import Counter
               decisions = [r.get("decision") for r in self.responses.values()]
               counter = Counter(decisions)
               most_common = counter.most_common(1)[0]
               
               return {
                   "consensus": True,
                   "decision": most_common[0],
                   "confidence": most_common[1] / len(decisions)
               }
               
           elif self.consensus_type == "weighted":
               # Weighted by agent expertise/confidence
               weighted_scores = {}
               for agent_id, response in self.responses.items():
                   decision = response.get("decision")
                   weight = response.get("confidence", 0.5)
                   
                   if decision not in weighted_scores:
                       weighted_scores[decision] = 0
                   weighted_scores[decision] += weight
                   
               best_decision = max(weighted_scores.items(), key=lambda x: x[1])
               total_weight = sum(weighted_scores.values())
               
               return {
                   "consensus": True,
                   "decision": best_decision[0],
                   "confidence": best_decision[1] / total_weight
               }
   ```

4. **Create orchestration service**
   ```python
   # src/domains/orchestration/domain/services/orchestration_service.py
   from typing import List, Dict, Optional, Any
   from uuid import UUID
   from datetime import datetime, timedelta
   
   from ..entities.workflow import Workflow, WorkflowTask, WorkflowStatus, TaskStatus
   from ..entities.task_coordination import AgentAssignment, ConsensusRequest
   
   class OrchestrationService:
       def __init__(self):
           self.active_workflows: Dict[UUID, Workflow] = {}
           self.agent_assignments: Dict[UUID, List[AgentAssignment]] = {}
           self.consensus_requests: Dict[UUID, ConsensusRequest] = {}
           
       def create_workflow(self, name: str, description: str,
                          task_definitions: List[Dict[str, Any]],
                          created_by: str) -> Workflow:
           """Create new workflow from task definitions"""
           tasks = []
           
           for task_def in task_definitions:
               task = WorkflowTask(
                   id=UUID(task_def.get("id", str(uuid4()))),
                   agent_type=task_def["agent_type"],
                   agent_id=None,
                   name=task_def["name"],
                   description=task_def["description"],
                   input_data=task_def.get("input_data", {}),
                   dependencies=[UUID(dep) for dep in task_def.get("dependencies", [])]
               )
               tasks.append(task)
               
           workflow = Workflow.create(name, description, tasks, created_by)
           self.active_workflows[workflow.id] = workflow
           
           return workflow
           
       def start_workflow(self, workflow_id: UUID) -> List[WorkflowTask]:
           """Start workflow execution"""
           workflow = self.active_workflows.get(workflow_id)
           if not workflow:
               raise ValueError(f"Workflow {workflow_id} not found")
               
           workflow.status = WorkflowStatus.RUNNING
           workflow.started_at = datetime.utcnow()
           
           # Get initial tasks
           next_tasks = workflow.get_next_tasks()
           
           return next_tasks
           
       def assign_task_to_agent(self, task_id: UUID, agent_id: UUID,
                               agent_type: str, priority: int = 0) -> AgentAssignment:
           """Assign task to specific agent"""
           assignment = AgentAssignment(
               id=uuid4(),
               task_id=task_id,
               agent_id=agent_id,
               agent_type=agent_type,
               assigned_at=datetime.utcnow(),
               priority=priority
           )
           
           if agent_id not in self.agent_assignments:
               self.agent_assignments[agent_id] = []
           self.agent_assignments[agent_id].append(assignment)
           
           # Update task status
           for workflow in self.active_workflows.values():
               for task in workflow.tasks:
                   if task.id == task_id:
                       task.status = TaskStatus.ASSIGNED
                       task.agent_id = agent_id
                       break
                       
           return assignment
           
       def complete_task(self, workflow_id: UUID, task_id: UUID,
                        output_data: Dict[str, Any]) -> List[WorkflowTask]:
           """Mark task as completed and get next tasks"""
           workflow = self.active_workflows.get(workflow_id)
           if not workflow:
               raise ValueError(f"Workflow {workflow_id} not found")
               
           # Update task
           for task in workflow.tasks:
               if task.id == task_id:
                   task.status = TaskStatus.COMPLETED
                   task.output_data = output_data
                   task.completed_at = datetime.utcnow()
                   break
                   
           # Check if workflow completed
           all_completed = all(
               task.status in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]
               for task in workflow.tasks
           )
           
           if all_completed:
               workflow.status = WorkflowStatus.COMPLETED
               workflow.completed_at = datetime.utcnow()
               return []
               
           # Get next tasks
           return workflow.get_next_tasks()
           
       def create_consensus_request(self, workflow_id: UUID, topic: str,
                                  agent_ids: List[UUID],
                                  consensus_type: str = "majority",
                                  timeout_minutes: int = 5) -> ConsensusRequest:
           """Create consensus request for multiple agents"""
           deadline = datetime.utcnow() + timedelta(minutes=timeout_minutes)
           
           request = ConsensusRequest.create(
               workflow_id=workflow_id,
               topic=topic,
               agents=agent_ids,
               consensus_type=consensus_type,
               deadline=deadline
           )
           
           self.consensus_requests[request.id] = request
           return request
           
       def submit_consensus_response(self, request_id: UUID,
                                   agent_id: UUID,
                                   response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
           """Submit agent response to consensus request"""
           request = self.consensus_requests.get(request_id)
           if not request:
               raise ValueError(f"Consensus request {request_id} not found")
               
           request.add_response(agent_id, response)
           
           # Check if we have consensus
           if request.has_all_responses():
               result = request.calculate_consensus()
               request.result = result
               return result
               
           return None
   ```

5. **Create repository interfaces**
   ```python
   # src/domains/orchestration/domain/repositories/orchestration_repository.py
   from abc import ABC, abstractmethod
   from typing import List, Optional
   from uuid import UUID
   
   from ..entities.workflow import Workflow
   from ..entities.task_coordination import ConsensusRequest
   
   class IWorkflowRepository(ABC):
       @abstractmethod
       async def save(self, workflow: Workflow) -> None:
           pass
           
       @abstractmethod
       async def find_by_id(self, workflow_id: UUID) -> Optional[Workflow]:
           pass
           
       @abstractmethod
       async def find_active(self) -> List[Workflow]:
           pass
           
       @abstractmethod
       async def update_status(self, workflow_id: UUID, status: str) -> None:
           pass
   
   class IConsensusRepository(ABC):
       @abstractmethod
       async def save(self, consensus: ConsensusRequest) -> None:
           pass
           
       @abstractmethod
       async def find_by_id(self, consensus_id: UUID) -> Optional[ConsensusRequest]:
           pass
           
       @abstractmethod
       async def find_pending(self) -> List[ConsensusRequest]:
           pass
   ```

**Success Criteria**:
- [ ] Orchestration domain entities created
- [ ] Workflow and task coordination logic
- [ ] Consensus building mechanisms
- [ ] Service layer with orchestration logic
- [ ] Repository interfaces defined

---

### Blok 14: Decision Coordinator Agent
**Czas**: 4h | **Agent**: project-coder | **Dependencies**: Blok 13

**Task 4.1**: Decision Coordinator agent implementation

#### Execution Steps:
1. **Create Decision Coordinator Agent**
   ```python
   # src/domains/orchestration/infrastructure/agents/decision_coordinator.py
   from typing import Dict, Any, List, Optional
   from uuid import UUID
   from datetime import datetime
   import json
   
   from crewai import Agent, Task, Tool
   from langchain.tools import Tool as LangchainTool
   
   from ....shared.domain.events.agui_events import AGUIEvent, AGUIEventType
   from ....shared.infrastructure.agui.event_emitter import AGUIEventEmitter
   from ...domain.services.orchestration_service import OrchestrationService
   from ...domain.entities.workflow import WorkflowTask
   
   class DecisionCoordinatorAgent(Agent):
       def __init__(self,
                    event_emitter: AGUIEventEmitter,
                    orchestration_service: OrchestrationService):
           
           self.event_emitter = event_emitter
           self.orchestration_service = orchestration_service
           self.active_crews = {}
           
           # Define coordinator tools
           tools = [
               Tool(
                   name="create_workflow",
                   func=self._create_workflow,
                   description="Create and orchestrate multi-agent workflow"
               ),
               Tool(
                   name="assign_tasks",
                   func=self._assign_tasks,
                   description="Assign tasks to appropriate agents"
               ),
               Tool(
                   name="request_consensus",
                   func=self._request_consensus,
                   description="Request consensus from multiple agents"
               ),
               Tool(
                   name="generate_report",
                   func=self._generate_report,
                   description="Generate dynamic report based on workflow results"
               ),
           ]
           
           super().__init__(
               role="Decision Coordinator",
               goal="Orchestrate multi-agent workflows and coordinate decisions",
               backstory="""You are a master coordinator who excels at orchestrating 
               complex multi-agent workflows. You understand dependencies, can request 
               consensus when needed, and generate comprehensive reports.""",
               tools=tools,
               verbose=True
           )
           
       async def _create_workflow(self, workflow_definition: Dict[str, Any]) -> str:
           """Create and start a workflow"""
           
           # Emit workflow creation event
           await self.event_emitter.emit(AGUIEvent(
               type=AGUIEventType.WORKFLOW_CREATED,
               agent_id=self.role,
               data={
                   "workflow_name": workflow_definition.get("name"),
                   "task_count": len(workflow_definition.get("tasks", [])),
                   "status": "creating"
               }
           ))
           
           # Create workflow
           workflow = self.orchestration_service.create_workflow(
               name=workflow_definition["name"],
               description=workflow_definition["description"],
               task_definitions=workflow_definition["tasks"],
               created_by=self.role
           )
           
           # Start workflow
           initial_tasks = self.orchestration_service.start_workflow(workflow.id)
           
           # Emit workflow started event
           await self.event_emitter.emit(AGUIEvent(
               type=AGUIEventType.WORKFLOW_STARTED,
               agent_id=self.role,
               data={
                   "workflow_id": str(workflow.id),
                   "initial_tasks": [task.name for task in initial_tasks]
               }
           ))
           
           return f"Workflow '{workflow.name}' created with ID: {workflow.id}"
           
       async def _assign_tasks(self, workflow_id: str, 
                             tasks: List[WorkflowTask]) -> Dict[str, Any]:
           """Assign tasks to appropriate agents based on their capabilities"""
           
           assignments = []
           
           for task in tasks:
               # Determine best agent for task
               agent_id = await self._find_best_agent(task.agent_type, task.input_data)
               
               if agent_id:
                   # Assign task
                   assignment = self.orchestration_service.assign_task_to_agent(
                       task.id, agent_id, task.agent_type
                   )
                   
                   assignments.append({
                       "task": task.name,
                       "agent_id": str(agent_id),
                       "status": "assigned"
                   })
                   
                   # Emit task assignment event
                   await self.event_emitter.emit(AGUIEvent(
                       type=AGUIEventType.TASK_ASSIGNED,
                       agent_id=self.role,
                       data={
                           "task_id": str(task.id),
                           "task_name": task.name,
                           "assigned_to": str(agent_id),
                           "agent_type": task.agent_type
                       }
                   ))
               else:
                   assignments.append({
                       "task": task.name,
                       "status": "no_agent_available"
                   })
                   
           return {"assignments": assignments}
           
       async def _find_best_agent(self, agent_type: str, 
                                 requirements: Dict[str, Any]) -> Optional[UUID]:
           """Find best available agent for task"""
           # This would integrate with agent registry
           # For now, return mock agent ID
           
           # Emit agent search event
           await self.event_emitter.emit(AGUIEvent(
               type=AGUIEventType.AGENT_SEARCH,
               agent_id=self.role,
               data={
                   "searching_for": agent_type,
                   "requirements": requirements
               }
           ))
           
           # Mock implementation - would query agent registry
           return UUID("12345678-1234-5678-1234-567812345678")
           
       async def _request_consensus(self, topic: str, 
                                  agent_ids: List[str],
                                  consensus_type: str = "majority") -> Dict[str, Any]:
           """Request consensus from multiple agents"""
           
           # Create consensus request
           request = self.orchestration_service.create_consensus_request(
               workflow_id=UUID("00000000-0000-0000-0000-000000000000"),  # Mock
               topic=topic,
               agent_ids=[UUID(aid) for aid in agent_ids],
               consensus_type=consensus_type
           )
           
           # Emit consensus request event
           await self.event_emitter.emit(AGUIEvent(
               type=AGUIEventType.CONSENSUS_REQUEST,
               agent_id=self.role,
               data={
                   "request_id": str(request.id),
                   "topic": topic,
                   "agents_involved": agent_ids,
                   "consensus_type": consensus_type,
                   "deadline": request.deadline.isoformat()
               }
           ))
           
           return {
               "request_id": str(request.id),
               "status": "pending",
               "deadline": request.deadline.isoformat()
           }
           
       async def _generate_report(self, workflow_id: str) -> Dict[str, Any]:
           """Generate dynamic report based on workflow results"""
           
           workflow = self.orchestration_service.active_workflows.get(UUID(workflow_id))
           if not workflow:
               return {"error": "Workflow not found"}
               
           # Collect results
           report_data = {
               "workflow_name": workflow.name,
               "status": workflow.status.value,
               "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
               "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
               "tasks": []
           }
           
           for task in workflow.tasks:
               task_info = {
                   "name": task.name,
                   "status": task.status.value,
                   "agent_type": task.agent_type,
                   "duration": None
               }
               
               if task.started_at and task.completed_at:
                   duration = (task.completed_at - task.started_at).total_seconds()
                   task_info["duration"] = f"{duration:.2f}s"
                   
               if task.output_data:
                   task_info["key_results"] = task.output_data.get("summary", {})
                   
               report_data["tasks"].append(task_info)
               
           # Generate UI component for report
           ui_component = self._generate_report_ui(report_data)
           
           # Emit UI component event
           await self.event_emitter.emit(AGUIEvent(
               type=AGUIEventType.UI_COMPONENT,
               agent_id=self.role,
               data={
                   "component_type": "workflow_report",
                   "component_data": ui_component,
                   "workflow_id": workflow_id
               }
           ))
           
           return report_data
           
       def _generate_report_ui(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
           """Generate UI component definition for report"""
           return {
               "type": "report",
               "layout": "vertical",
               "components": [
                   {
                       "type": "header",
                       "content": f"Workflow Report: {report_data['workflow_name']}"
                   },
                   {
                       "type": "status_badge",
                       "status": report_data["status"],
                       "color": "green" if report_data["status"] == "completed" else "yellow"
                   },
                   {
                       "type": "timeline",
                       "events": [
                           {
                               "title": task["name"],
                               "status": task["status"],
                               "duration": task.get("duration", "N/A"),
                               "agent": task["agent_type"]
                           }
                           for task in report_data["tasks"]
                       ]
                   },
                   {
                       "type": "summary",
                       "metrics": {
                           "Total Tasks": len(report_data["tasks"]),
                           "Completed": sum(1 for t in report_data["tasks"] if t["status"] == "completed"),
                           "Failed": sum(1 for t in report_data["tasks"] if t["status"] == "failed")
                       }
                   }
               ]
           }
   ```

2. **Create multi-agent coordination**
   ```python
   # src/domains/orchestration/infrastructure/agents/multi_agent_crew.py
   from typing import List, Dict, Any, Optional
   from uuid import UUID
   
   from crewai import Crew, Process
   from crewai.agent import Agent
   from crewai.task import Task
   
   from ....shared.domain.events.agui_events import AGUIEvent, AGUIEventType
   from ....shared.infrastructure.agui.event_emitter import AGUIEventEmitter
   
   class MultiAgentCrew:
       def __init__(self, 
                    coordinator: DecisionCoordinatorAgent,
                    event_emitter: AGUIEventEmitter):
           self.coordinator = coordinator
           self.event_emitter = event_emitter
           self.available_agents: Dict[str, Agent] = {}
           
       def register_agent(self, agent_type: str, agent: Agent):
           """Register an agent for orchestration"""
           self.available_agents[agent_type] = agent
           
       async def execute_workflow(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
           """Execute a complete workflow using CrewAI"""
           
           # Create tasks from workflow definition
           crew_tasks = []
           agent_assignments = {}
           
           for task_def in workflow_definition["tasks"]:
               agent_type = task_def["agent_type"]
               agent = self.available_agents.get(agent_type)
               
               if not agent:
                   raise ValueError(f"No agent available for type: {agent_type}")
                   
               # Create CrewAI task
               task = Task(
                   description=task_def["description"],
                   agent=agent,
                   expected_output=task_def.get("expected_output", "Completed task output")
               )
               
               crew_tasks.append(task)
               agent_assignments[task] = agent
               
           # Create crew with coordinator as manager
           crew = Crew(
               agents=list(self.available_agents.values()) + [self.coordinator],
               tasks=crew_tasks,
               process=Process.hierarchical,  # Coordinator manages execution
               manager_agent=self.coordinator,
               verbose=True
           )
           
           # Emit workflow execution start
           await self.event_emitter.emit(AGUIEvent(
               type=AGUIEventType.CREW_EXECUTION_START,
               agent_id="multi_agent_crew",
               data={
                   "workflow_name": workflow_definition["name"],
                   "agent_count": len(self.available_agents),
                   "task_count": len(crew_tasks)
               }
           ))
           
           # Execute crew
           try:
               result = crew.kickoff()
               
               # Emit completion
               await self.event_emitter.emit(AGUIEvent(
                   type=AGUIEventType.CREW_EXECUTION_COMPLETE,
                   agent_id="multi_agent_crew",
                   data={
                       "workflow_name": workflow_definition["name"],
                       "status": "completed",
                       "result_summary": str(result)[:500]  # First 500 chars
                   }
               ))
               
               return {
                   "status": "completed",
                   "result": result,
                   "tasks_completed": len(crew_tasks)
               }
               
           except Exception as e:
               # Emit failure
               await self.event_emitter.emit(AGUIEvent(
                   type=AGUIEventType.CREW_EXECUTION_COMPLETE,
                   agent_id="multi_agent_crew",
                   data={
                       "workflow_name": workflow_definition["name"],
                       "status": "failed",
                       "error": str(e)
                   }
               ))
               
               raise
   ```

3. **Create workflow templates**
   ```python
   # src/domains/orchestration/infrastructure/templates/workflow_templates.py
   from typing import Dict, Any, List
   from uuid import uuid4
   
   class WorkflowTemplates:
       """Pre-defined workflow templates"""
       
       @staticmethod
       def content_creation_workflow() -> Dict[str, Any]:
           """Complete content creation workflow"""
           return {
               "name": "Content Creation Pipeline",
               "description": "End-to-end content creation from research to publication",
               "tasks": [
                   {
                       "id": str(uuid4()),
                       "name": "Topic Research",
                       "agent_type": "content_scout",
                       "description": "Research trending topics in the given domain",
                       "input_data": {"domain": "AI technology"},
                       "dependencies": []
                   },
                   {
                       "id": str(uuid4()),
                       "name": "Trend Analysis",
                       "agent_type": "trend_analyst",
                       "description": "Analyze viral potential of discovered topics",
                       "input_data": {},
                       "dependencies": [0]  # Depends on topic research
                   },
                   {
                       "id": str(uuid4()),
                       "name": "Editorial Review",
                       "agent_type": "editorial_strategist",
                       "description": "Review topics for editorial guidelines",
                       "input_data": {},
                       "dependencies": [1]  # Depends on trend analysis
                   },
                   {
                       "id": str(uuid4()),
                       "name": "Quality Check",
                       "agent_type": "quality_assessor",
                       "description": "Verify content quality and accuracy",
                       "input_data": {},
                       "dependencies": [2]  # Depends on editorial review
                   }
               ]
           }
           
       @staticmethod
       def consensus_decision_workflow() -> Dict[str, Any]:
           """Workflow requiring consensus from multiple agents"""
           return {
               "name": "Consensus Decision Pipeline",
               "description": "Multi-agent consensus for critical decisions",
               "tasks": [
                   {
                       "id": str(uuid4()),
                       "name": "Gather Perspectives",
                       "agent_type": "decision_coordinator",
                       "description": "Collect input from all relevant agents",
                       "input_data": {"topic": "Content publication decision"},
                       "dependencies": []
                   },
                   {
                       "id": str(uuid4()),
                       "name": "Editorial Opinion",
                       "agent_type": "editorial_strategist",
                       "description": "Provide editorial perspective",
                       "input_data": {},
                       "dependencies": [0]
                   },
                   {
                       "id": str(uuid4()),
                       "name": "Quality Opinion",
                       "agent_type": "quality_assessor",
                       "description": "Provide quality perspective",
                       "input_data": {},
                       "dependencies": [0]
                   },
                   {
                       "id": str(uuid4()),
                       "name": "Trend Opinion",
                       "agent_type": "trend_analyst",
                       "description": "Provide trending perspective",
                       "input_data": {},
                       "dependencies": [0]
                   },
                   {
                       "id": str(uuid4()),
                       "name": "Build Consensus",
                       "agent_type": "decision_coordinator",
                       "description": "Build consensus from all perspectives",
                       "input_data": {"consensus_type": "weighted"},
                       "dependencies": [1, 2, 3]
                   }
               ]
           }
   ```

4. **Integration with API**
   ```python
   # src/interfaces/api/controllers/orchestration_controller.py
   from fastapi import APIRouter, HTTPException, Depends
   from pydantic import BaseModel
   from typing import Dict, Any, List, Optional
   from uuid import UUID
   
   from dependency_injector.wiring import inject, Provide
   
   from src.domains.orchestration.infrastructure.agents.decision_coordinator import (
       DecisionCoordinatorAgent
   )
   from src.domains.orchestration.infrastructure.agents.multi_agent_crew import (
       MultiAgentCrew
   )
   from src.domains.orchestration.infrastructure.templates.workflow_templates import (
       WorkflowTemplates
   )
   from src.shared.infrastructure.container import Container
   
   router = APIRouter(prefix="/api/orchestration", tags=["orchestration"])
   
   class WorkflowRequest(BaseModel):
       template_name: Optional[str] = None
       custom_workflow: Optional[Dict[str, Any]] = None
       
   class ConsensusRequest(BaseModel):
       topic: str
       agent_types: List[str]
       consensus_type: str = "majority"
       timeout_minutes: int = 5
   
   router.post("/workflows/execute")
   @inject
   async def execute_workflow(
       request: WorkflowRequest,
       coordinator: DecisionCoordinatorAgent = Provide[Container.decision_coordinator],
       crew: MultiAgentCrew = Provide[Container.multi_agent_crew]
   ):
       """Execute a workflow using multi-agent orchestration"""
       
       try:
           # Get workflow definition
           if request.template_name:
               # Use template
               if request.template_name == "content_creation":
                   workflow_def = WorkflowTemplates.content_creation_workflow()
               elif request.template_name == "consensus_decision":
                   workflow_def = WorkflowTemplates.consensus_decision_workflow()
               else:
                   raise HTTPException(
                       status_code=400,
                       detail=f"Unknown template: {request.template_name}"
                   )
           elif request.custom_workflow:
               workflow_def = request.custom_workflow
           else:
               raise HTTPException(
                   status_code=400,
                   detail="Either template_name or custom_workflow required"
               )
               
           # Execute workflow
           result = await crew.execute_workflow(workflow_def)
           
           return {
               "success": True,
               "workflow_name": workflow_def["name"],
               "result": result
           }
           
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))
           
   router.post("/consensus/request")
   @inject
   async def request_consensus(
       request: ConsensusRequest,
       coordinator: DecisionCoordinatorAgent = Provide[Container.decision_coordinator]
   ):
       """Request consensus from multiple agents"""
       
       try:
           # Find agent IDs for the requested types
           agent_ids = []  # Would be resolved from agent registry
           
           result = await coordinator._request_consensus(
               topic=request.topic,
               agent_ids=agent_ids,
               consensus_type=request.consensus_type
           )
           
           return {
               "success": True,
               "consensus_request": result
           }
           
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))
           
   router.get("/workflows/templates")
   async def list_workflow_templates():
       """List available workflow templates"""
       
       return {
           "templates": [
               {
                   "name": "content_creation",
                   "description": "End-to-end content creation pipeline",
                   "agent_types": ["content_scout", "trend_analyst", 
                                  "editorial_strategist", "quality_assessor"]
               },
               {
                   "name": "consensus_decision",
                   "description": "Multi-agent consensus decision making",
                   "agent_types": ["decision_coordinator", "editorial_strategist",
                                  "quality_assessor", "trend_analyst"]
               }
           ]
       }
           
   router.get("/workflows/{workflow_id}/status")
   @inject
   async def get_workflow_status(
       workflow_id: UUID,
       coordinator: DecisionCoordinatorAgent = Provide[Container.decision_coordinator]
   ):
       """Get workflow execution status"""
       
       workflow = coordinator.orchestration_service.active_workflows.get(workflow_id)
       
       if not workflow:
           raise HTTPException(status_code=404, detail="Workflow not found")
           
       return {
           "workflow_id": str(workflow.id),
           "name": workflow.name,
           "status": workflow.status.value,
           "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
           "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
           "tasks": [
               {
                   "name": task.name,
                   "status": task.status.value,
                   "agent_type": task.agent_type
               }
               for task in workflow.tasks
           ]
       }
   ```

**Success Criteria**:
- [ ] Decision Coordinator agent with orchestration capabilities
- [ ] Multi-agent CrewAI integration
- [ ] Workflow execution with dependencies
- [ ] Consensus building implementation
- [ ] Dynamic report generation
- [ ] API endpoints for orchestration

---

### Blok 15: Generative UI Components
**Czas**: 4h | **Agent**: project-coder | **Dependencies**: Blok 14

**Task 4.2**: Generative UI components

#### Execution Steps:
1. **Create Generative UI system**
   ```typescript
   // frontend/src/components/generative/GenerativeUIRenderer.tsx
   import React, { useMemo } from 'react';
   import { useAGUIConnection } from '../../hooks/useAGUIConnection';
   import { DynamicChart } from './DynamicChart';
   import { InteractiveReport } from './InteractiveReport';
   import { DecisionTree } from './DecisionTree';
   import { WorkflowTimeline } from './WorkflowTimeline';
   
   interface UIComponent {
     type: string;
     layout?: string;
     components?: UIComponent[];
     [key: string]: any;
   }
   
   interface GenerativeUIRendererProps {
     component: UIComponent;
     onInteraction?: (action: string, data: any) => void;
   }
   
   export const GenerativeUIRenderer: React.FC<GenerativeUIRendererProps> = ({
     component,
     onInteraction
   }) => {
     const renderComponent = useMemo(() => {
       switch (component.type) {
         case 'report':
           return <InteractiveReport data={component} onInteraction={onInteraction} />;
           
         case 'chart':
           return <DynamicChart config={component} />;
           
         case 'decision_tree':
           return <DecisionTree data={component} onDecision={onInteraction} />;
           
         case 'workflow_timeline':
           return <WorkflowTimeline events={component.events} />;
           
         case 'header':
           return (
             <h2 className="text-2xl font-bold mb-4">
               {component.content}
             </h2>
           );
           
         case 'status_badge':
           return (
             <span className={`
               inline-flex items-center px-3 py-1 rounded-full text-sm font-medium
               ${component.color === 'green' ? 'bg-green-100 text-green-800' : ''}
               ${component.color === 'yellow' ? 'bg-yellow-100 text-yellow-800' : ''}
               ${component.color === 'red' ? 'bg-red-100 text-red-800' : ''}
             `}>
               {component.status}
             </span>
           );
           
         case 'timeline':
           return <WorkflowTimeline events={component.events} />;
           
         case 'summary':
           return (
             <div className="grid grid-cols-3 gap-4 mt-6">
               {Object.entries(component.metrics || {}).map(([key, value]) => (
                 <div key={key} className="bg-gray-50 p-4 rounded-lg">
                   <p className="text-sm text-gray-600">{key}</p>
                   <p className="text-2xl font-bold">{String(value)}</p>
                 </div>
               ))}
             </div>
           );
           
         case 'container':
           return (
             <div className={`
               ${component.layout === 'horizontal' ? 'flex space-x-4' : 'space-y-4'}
             `}>
               {component.components?.map((child, idx) => (
                 <GenerativeUIRenderer
                   key={idx}
                   component={child}
                   onInteraction={onInteraction}
                 />
               ))}
             </div>
           );
           
         default:
           return <div>Unknown component type: {component.type}</div>;
       }
     }, [component, onInteraction]);
     
     return <div className="generative-ui-component">{renderComponent}</div>;
   };
   ```

2. **Create Dynamic Chart component**
   ```typescript
   // frontend/src/components/generative/DynamicChart.tsx
   import React, { useEffect, useRef } from 'react';
   import {
     Chart as ChartJS,
     CategoryScale,
     LinearScale,
     PointElement,
     LineElement,
     BarElement,
     ArcElement,
     Title,
     Tooltip,
     Legend,
     ChartData,
     ChartOptions
   } from 'chart.js';
   import { Chart } from 'react-chartjs-2';
   
   ChartJS.register(
     CategoryScale,
     LinearScale,
     PointElement,
     LineElement,
     BarElement,
     ArcElement,
     Title,
     Tooltip,
     Legend
   );
   
   interface DynamicChartProps {
     config: {
       chartType: 'line' | 'bar' | 'pie' | 'doughnut';
       data: ChartData;
       options?: ChartOptions;
       title?: string;
       description?: string;
     };
   }
   
   export const DynamicChart: React.FC<DynamicChartProps> = ({ config }) => {
     const chartRef = useRef<ChartJS>(null);
     
     useEffect(() => {
       // Auto-update chart if data changes
       if (chartRef.current) {
         chartRef.current.update();
       }
     }, [config.data]);
     
     const defaultOptions: ChartOptions = {
       responsive: true,
       maintainAspectRatio: false,
       plugins: {
         legend: {
           position: 'top' as const,
         },
         title: {
           display: !!config.title,
           text: config.title,
         },
       },
     };
     
     const mergedOptions = { ...defaultOptions, ...config.options };
     
     return (
       <div className="bg-white p-6 rounded-lg shadow-md">
         {config.description && (
           <p className="text-sm text-gray-600 mb-4">{config.description}</p>
         )}
         <div className="h-64">
           <Chart
             ref={chartRef}
             type={config.chartType}
             data={config.data}
             options={mergedOptions}
           />
         </div>
       </div>
     );
   };
   ```

3. **Create Interactive Report component**
   ```typescript
   // frontend/src/components/generative/InteractiveReport.tsx
   import React, { useState } from 'react';
   import { ChevronDown, ChevronRight, Download, Share2 } from 'lucide-react';
   import { GenerativeUIRenderer } from './GenerativeUIRenderer';
   
   interface InteractiveReportProps {
     data: {
       layout: string;
       components: any[];
       metadata?: {
         title?: string;
         generated_at?: string;
         agent?: string;
       };
     };
     onInteraction?: (action: string, data: any) => void;
   }
   
   export const InteractiveReport: React.FC<InteractiveReportProps> = ({
     data,
     onInteraction
   }) => {
     const [expandedSections, setExpandedSections] = useState<Set<number>>(
       new Set([0, 1, 2]) // First 3 sections expanded by default
     );
     
     const toggleSection = (index: number) => {
       const newExpanded = new Set(expandedSections);
       if (newExpanded.has(index)) {
         newExpanded.delete(index);
       } else {
         newExpanded.add(index);
       }
       setExpandedSections(newExpanded);
     };
     
     const handleExport = () => {
       onInteraction?.('export', { format: 'pdf', report: data });
     };
     
     const handleShare = () => {
       onInteraction?.('share', { report: data });
     };
     
     return (
       <div className="bg-white rounded-lg shadow-lg p-6">
         {/* Report Header */}
         <div className="flex items-center justify-between mb-6">
           <div>
             <h1 className="text-2xl font-bold">
               {data.metadata?.title || 'AI-Generated Report'}
             </h1>
             {data.metadata?.generated_at && (
               <p className="text-sm text-gray-500">
                 Generated at: {new Date(data.metadata.generated_at).toLocaleString()}
               </p>
             )}
             {data.metadata?.agent && (
               <p className="text-sm text-gray-500">
                 By: {data.metadata.agent}
               </p>
             )}
           </div>
           <div className="flex space-x-2">
             <button
               onClick={handleExport}
               className="flex items-center px-3 py-1 border rounded hover:bg-gray-50"
             >
               <Download className="h-4 w-4 mr-1" />
               Export
             </button>
             <button
               onClick={handleShare}
               className="flex items-center px-3 py-1 border rounded hover:bg-gray-50"
             >
               <Share2 className="h-4 w-4 mr-1" />
               Share
             </button>
           </div>
         </div>
         
         {/* Report Content */}
         <div className={data.layout === 'horizontal' ? 'flex space-x-6' : 'space-y-6'}>
           {data.components.map((component, idx) => (
             <div key={idx} className="flex-1">
               {component.type === 'section' ? (
                 <div className="border rounded-lg p-4">
                   <button
                     onClick={() => toggleSection(idx)}
                     className="w-full flex items-center justify-between text-left"
                   >
                     <h3 className="text-lg font-semibold">{component.title}</h3>
                     {expandedSections.has(idx) ? (
                       <ChevronDown className="h-5 w-5" />
                     ) : (
                       <ChevronRight className="h-5 w-5" />
                     )}
                   </button>
                   {expandedSections.has(idx) && (
                     <div className="mt-4">
                       <GenerativeUIRenderer
                         component={component}
                         onInteraction={onInteraction}
                       />
                     </div>
                   )}
                 </div>
               ) : (
                 <GenerativeUIRenderer
                   component={component}
                   onInteraction={onInteraction}
                 />
               )}
             </div>
           ))}
         </div>
       </div>
     );
   };
   ```

4. **Create Decision Tree component**
   ```typescript
   // frontend/src/components/generative/DecisionTree.tsx
   import React, { useState } from 'react';
   import { AlertCircle, CheckCircle, XCircle } from 'lucide-react';
   
   interface DecisionNode {
     id: string;
     question: string;
     options: {
       label: string;
       value: string;
       nextNode?: string;
       result?: string;
     }[];
   }
   
   interface DecisionTreeProps {
     data: {
       nodes: DecisionNode[];
       startNode: string;
       title?: string;
     };
     onDecision?: (action: string, data: any) => void;
   }
   
   export const DecisionTree: React.FC<DecisionTreeProps> = ({ data, onDecision }) => {
     const [currentNodeId, setCurrentNodeId] = useState(data.startNode);
     const [decisions, setDecisions] = useState<Array<{node: string, choice: string}>>([]);
     const [finalResult, setFinalResult] = useState<string | null>(null);
     
     const currentNode = data.nodes.find(n => n.id === currentNodeId);
     
     const handleChoice = (option: any) => {
       const newDecisions = [...decisions, { node: currentNodeId, choice: option.label }];
       setDecisions(newDecisions);
       
       if (option.result) {
         setFinalResult(option.result);
         onDecision?.('complete', {
           decisions: newDecisions,
           result: option.result
         });
       } else if (option.nextNode) {
         setCurrentNodeId(option.nextNode);
       }
     };
     
     const reset = () => {
       setCurrentNodeId(data.startNode);
       setDecisions([]);
       setFinalResult(null);
     };
     
     return (
       <div className="bg-white rounded-lg shadow-md p-6">
         {data.title && (
           <h3 className="text-xl font-bold mb-4">{data.title}</h3>
         )}
         
         {/* Decision Path */}
         {decisions.length > 0 && (
           <div className="mb-4 p-3 bg-gray-50 rounded">
             <p className="text-sm font-medium mb-2">Decision Path:</p>
             <div className="space-y-1">
               {decisions.map((d, idx) => (
                 <div key={idx} className="text-sm text-gray-600">
                   → {d.choice}
                 </div>
               ))}
             </div>
           </div>
         )}
         
         {/* Current Question or Result */}
         {finalResult ? (
           <div className="text-center py-8">
             <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
             <h4 className="text-lg font-semibold mb-2">Decision Complete</h4>
             <p className="text-gray-700 mb-6">{finalResult}</p>
             <button
               onClick={reset}
               className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
             >
               Start Over
             </button>
           </div>
         ) : currentNode ? (
           <div>
             <div className="flex items-start mb-6">
               <AlertCircle className="h-6 w-6 text-blue-500 mr-3 mt-1" />
               <p className="text-lg">{currentNode.question}</p>
             </div>
             <div className="space-y-3">
               {currentNode.options.map((option, idx) => (
                 <button
                   key={idx}
                   onClick={() => handleChoice(option)}
                   className="w-full text-left p-4 border rounded-lg hover:bg-gray-50 
                            transition-colors flex items-center justify-between group"
                 >
                   <span>{option.label}</span>
                   <span className="text-gray-400 group-hover:text-gray-600">→</span>
                 </button>
               ))}
             </div>
           </div>
         ) : (
           <div className="text-center py-8">
             <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
             <p>Error: Node not found</p>
           </div>
         )}
       </div>
     );
   };
   ```

5. **Create AI Summary Generator**
   ```typescript
   // frontend/src/components/generative/AISummaryGenerator.tsx
   import React, { useState, useEffect } from 'react';
   import { Sparkles, Loader } from 'lucide-react';
   import { useAGUIConnection } from '../../hooks/useAGUIConnection';
   import { AGUIEventType } from '../../types/agui';
   
   interface AISummaryGeneratorProps {
     data: any;
     context?: string;
     onSummaryGenerated?: (summary: string) => void;
   }
   
   export const AISummaryGenerator: React.FC<AISummaryGeneratorProps> = ({
     data,
     context,
     onSummaryGenerated
   }) => {
     const [summary, setSummary] = useState<string>('');
     const [isGenerating, setIsGenerating] = useState(false);
     const { subscribe, unsubscribe } = useAGUIConnection();
     
     useEffect(() => {
       const handleSummaryEvent = (event: any) => {
         if (event.type === AGUIEventType.AI_SUMMARY_GENERATED &&
             event.data.context === context) {
           setSummary(event.data.summary);
           setIsGenerating(false);
           onSummaryGenerated?.(event.data.summary);
         }
       };
       
       subscribe(AGUIEventType.AI_SUMMARY_GENERATED, handleSummaryEvent);
       
       return () => {
         unsubscribe(AGUIEventType.AI_SUMMARY_GENERATED, handleSummaryEvent);
       };
     }, [context, subscribe, unsubscribe, onSummaryGenerated]);
     
     const generateSummary = async () => {
       setIsGenerating(true);
       
       try {
         const response = await fetch('/api/ai/generate-summary', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ data, context })
         });
         
         if (!response.ok) throw new Error('Failed to generate summary');
         
         // Summary will come through WebSocket/SSE
       } catch (error) {
         console.error('Summary generation error:', error);
         setIsGenerating(false);
       }
     };
     
     return (
       <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6">
         <div className="flex items-center justify-between mb-4">
           <div className="flex items-center">
             <Sparkles className="h-6 w-6 text-purple-600 mr-2" />
             <h3 className="text-lg font-semibold">AI-Generated Summary</h3>
           </div>
           {!summary && !isGenerating && (
             <button
               onClick={generateSummary}
               className="px-4 py-2 bg-purple-600 text-white rounded-lg 
                        hover:bg-purple-700 transition-colors"
             >
               Generate Summary
             </button>
           )}
         </div>
         
         {isGenerating && (
           <div className="flex items-center justify-center py-8">
             <Loader className="h-8 w-8 animate-spin text-purple-600" />
             <span className="ml-3 text-gray-600">Generating summary...</span>
           </div>
         )}
         
         {summary && (
           <div className="prose max-w-none">
             <div className="bg-white rounded-lg p-4 shadow-inner">
               {summary.split('\n').map((paragraph, idx) => (
                 <p key={idx} className="mb-3 last:mb-0">
                   {paragraph}
                 </p>
               ))}
             </div>
             <div className="mt-4 flex justify-end">
               <button
                 onClick={generateSummary}
                 className="text-sm text-purple-600 hover:text-purple-700"
               >
                 Regenerate
               </button>
             </div>
           </div>
         )}
       </div>
     );
   };
   ```

**Success Criteria**:
- [ ] Generative UI renderer system
- [ ] Dynamic chart generation
- [ ] Interactive report components
- [ ] Decision tree visualizations
- [ ] AI-generated summaries
- [ ] Component interaction handling

---

### Blok 16: Production Security & Performance
**Czas**: 6h | **Agent**: deployment-specialist | **Dependencies**: Blok 15

**Task 4.3 + 4.4**: Production security hardening + Load testing

#### Execution Steps:
1. **Setup HTTPS with Let's Encrypt**
   ```bash
   #!/bin/bash
   # scripts/security-hardening.sh
   
   echo "🔐 Starting security hardening..."
   
   # Install certbot
   sudo apt-get update
   sudo apt-get install -y certbot python3-certbot-nginx
   
   # Get SSL certificate
   sudo certbot --nginx -d kolegium.yourdomain.com \
     --non-interactive \
     --agree-tos \
     --email admin@yourdomain.com \
     --redirect
   
   # Auto-renewal
   echo "0 0,12 * * * root certbot renew --quiet" | sudo tee -a /etc/crontab > /dev/null
   ```

2. **Update Nginx configuration**
   ```nginx
   # nginx/nginx.conf
   upstream api_gateway {
       server api-gateway:8000;
   }
   
   # Rate limiting
   limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
   limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/m;
   
   server {
       listen 80;
       server_name kolegium.yourdomain.com;
       return 301 https://$server_name$request_uri;
   }
   
   server {
       listen 443 ssl http2;
       server_name kolegium.yourdomain.com;
       
       # SSL Configuration
       ssl_certificate /etc/letsencrypt/live/kolegium.yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/kolegium.yourdomain.com/privkey.pem;
       
       # Security headers
       add_header X-Frame-Options "SAMEORIGIN" always;
       add_header X-Content-Type-Options "nosniff" always;
       add_header X-XSS-Protection "1; mode=block" always;
       add_header Referrer-Policy "strict-origin-when-cross-origin" always;
       add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;
       
       # API endpoints with rate limiting
       location /api/ {
           limit_req zone=api_limit burst=20 nodelay;
           
           proxy_pass http://api_gateway;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           
           # CORS headers
           add_header Access-Control-Allow-Origin $http_origin always;
           add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
           add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
           add_header Access-Control-Allow-Credentials true always;
           
           if ($request_method = 'OPTIONS') {
               return 204;
           }
       }
       
       # Auth endpoints with stricter rate limiting
       location /api/auth/ {
           limit_req zone=auth_limit burst=5 nodelay;
           
           proxy_pass http://api_gateway;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       # WebSocket for AG-UI
       location /ws/ {
           proxy_pass http://api_gateway;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       # Static files
       location / {
           root /usr/share/nginx/html;
           try_files $uri $uri/ /index.html;
           
           # Cache static assets
           location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
               expires 1y;
               add_header Cache-Control "public, immutable";
           }
       }
   }
   ```

3. **Enhanced API security**
   ```python
   # src/shared/infrastructure/security/api_security.py
   from fastapi import FastAPI, Request, HTTPException
   from fastapi.middleware.cors import CORSMiddleware
   from fastapi.middleware.trustedhost import TrustedHostMiddleware
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   from slowapi.errors import RateLimitExceeded
   import time
   from typing import Callable
   
   # Create limiter
   limiter = Limiter(key_func=get_remote_address)
   
   def setup_security(app: FastAPI):
       """Setup security middleware and configurations"""
       
       # Trusted hosts
       app.add_middleware(
           TrustedHostMiddleware,
           allowed_hosts=["kolegium.yourdomain.com", "localhost"]
       )
       
       # CORS with specific origins
       app.add_middleware(
           CORSMiddleware,
           allow_origins=["https://kolegium.yourdomain.com"],
           allow_credentials=True,
           allow_methods=["GET", "POST", "PUT", "DELETE"],
           allow_headers=["*"],
       )
       
       # Rate limiting
       app.state.limiter = limiter
       app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
       
       # Request ID middleware
       @app.middleware("http")
       async def add_request_id(request: Request, call_next):
           request_id = str(uuid4())
           request.state.request_id = request_id
           
           response = await call_next(request)
           response.headers["X-Request-ID"] = request_id
           
           return response
       
       # Security headers middleware
       @app.middleware("http")
       async def add_security_headers(request: Request, call_next):
           response = await call_next(request)
           
           response.headers["X-Content-Type-Options"] = "nosniff"
           response.headers["X-Frame-Options"] = "DENY"
           response.headers["X-XSS-Protection"] = "1; mode=block"
           response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
           
           return response
       
       # Request timing middleware
       @app.middleware("http")
       async def add_process_time_header(request: Request, call_next):
           start_time = time.time()
           response = await call_next(request)
           process_time = time.time() - start_time
           response.headers["X-Process-Time"] = str(process_time)
           return response
   ```

4. **Input validation and sanitization**
   ```python
   # src/shared/infrastructure/security/input_validation.py
   import re
   import html
   from typing import Any, Dict, List
   from pydantic import BaseModel, validator
   import bleach
   
   class InputSanitizer:
       """Sanitize user inputs to prevent XSS and injection attacks"""
       
       # Allowed HTML tags for rich text
       ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'a']
       ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}
       
       @staticmethod
       def sanitize_html(text: str) -> str:
           """Sanitize HTML content"""
           return bleach.clean(
               text,
               tags=InputSanitizer.ALLOWED_TAGS,
               attributes=InputSanitizer.ALLOWED_ATTRIBUTES,
               strip=True
           )
           
       @staticmethod
       def sanitize_text(text: str) -> str:
           """Sanitize plain text (escape HTML)"""
           return html.escape(text)
           
       @staticmethod
       def validate_sql_identifier(identifier: str) -> bool:
           """Validate SQL identifiers to prevent injection"""
           pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
           return bool(re.match(pattern, identifier))
           
       @staticmethod
       def sanitize_filename(filename: str) -> str:
           """Sanitize filename to prevent path traversal"""
           # Remove any path components
           filename = filename.replace('..', '').replace('/', '').replace('\\', '')
           # Keep only safe characters
           filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
           return filename[:255]  # Limit length
   
   class SecureBaseModel(BaseModel):
       """Base model with built-in sanitization"""
       
       class Config:
           # Automatically validate on assignment
           validate_assignment = True
           
       @validator('*', pre=True)
       def sanitize_strings(cls, v):
           if isinstance(v, str):
               return InputSanitizer.sanitize_text(v)
           return v
   
   # Example secure models
   class SecureAgentConfig(SecureBaseModel):
       role: str
       goal: str
       backstory: str
       
       @validator('role', 'goal')
       def validate_length(cls, v):
           if len(v) > 200:
               raise ValueError('Text too long')
           return v
           
       @validator('backstory')
       def validate_backstory(cls, v):
           if len(v) > 1000:
               raise ValueError('Backstory too long')
           # Allow some HTML in backstory
           return InputSanitizer.sanitize_html(v)
   ```

5. **Create load testing suite**
   ```python
   # tests/load/test_api_performance.py
   import asyncio
   import aiohttp
   import time
   from typing import List, Dict, Any
   from dataclasses import dataclass
   from statistics import mean, median, stdev
   import json
   
   @dataclass
   class LoadTestResult:
       endpoint: str
       total_requests: int
       successful_requests: int
       failed_requests: int
       response_times: List[float]
       errors: List[str]
       
       @property
       def success_rate(self) -> float:
           return self.successful_requests / self.total_requests * 100
           
       @property
       def avg_response_time(self) -> float:
           return mean(self.response_times) if self.response_times else 0
           
       @property
       def median_response_time(self) -> float:
           return median(self.response_times) if self.response_times else 0
           
       @property
       def p95_response_time(self) -> float:
           if not self.response_times:
               return 0
           sorted_times = sorted(self.response_times)
           index = int(len(sorted_times) * 0.95)
           return sorted_times[index]
   
   class LoadTester:
       def __init__(self, base_url: str, auth_token: str = None):
           self.base_url = base_url
           self.auth_token = auth_token
           self.headers = {}
           if auth_token:
               self.headers['Authorization'] = f'Bearer {auth_token}'
               
       async def test_endpoint(self, 
                             endpoint: str,
                             method: str = 'GET',
                             data: Dict[str, Any] = None,
                             concurrent_users: int = 10,
                             requests_per_user: int = 10) -> LoadTestResult:
           """Test a single endpoint with concurrent users"""
           
           result = LoadTestResult(
               endpoint=endpoint,
               total_requests=concurrent_users * requests_per_user,
               successful_requests=0,
               failed_requests=0,
               response_times=[],
               errors=[]
           )
           
           async def make_request(session: aiohttp.ClientSession):
               url = f"{self.base_url}{endpoint}"
               start_time = time.time()
               
               try:
                   async with session.request(
                       method, url, 
                       headers=self.headers,
                       json=data,
                       timeout=aiohttp.ClientTimeout(total=30)
                   ) as response:
                       await response.text()
                       response_time = time.time() - start_time
                       
                       if response.status < 400:
                           result.successful_requests += 1
                           result.response_times.append(response_time)
                       else:
                           result.failed_requests += 1
                           result.errors.append(f"HTTP {response.status}")
                           
               except Exception as e:
                   result.failed_requests += 1
                   result.errors.append(str(e))
                   
           async def user_session():
               async with aiohttp.ClientSession() as session:
                   tasks = [make_request(session) for _ in range(requests_per_user)]
                   await asyncio.gather(*tasks)
                   
           # Run concurrent user sessions
           user_tasks = [user_session() for _ in range(concurrent_users)]
           await asyncio.gather(*user_tasks)
           
           return result
           
       async def run_test_suite(self) -> Dict[str, LoadTestResult]:
           """Run complete load test suite"""
           
           test_scenarios = [
               # Basic endpoints
               {
                   "endpoint": "/api/health",
                   "method": "GET",
                   "concurrent_users": 100,
                   "requests_per_user": 10
               },
               # Agent creation (heavy operation)
               {
                   "endpoint": "/api/agents/create-from-description",
                   "method": "POST",
                   "data": {
                       "description": "Create an agent to monitor news"
                   },
                   "concurrent_users": 20,
                   "requests_per_user": 5
               },
               # WebSocket simulation
               {
                   "endpoint": "/api/agents",
                   "method": "GET",
                   "concurrent_users": 50,
                   "requests_per_user": 20
               },
               # Workflow execution
               {
                   "endpoint": "/api/orchestration/workflows/execute",
                   "method": "POST",
                   "data": {
                       "template_name": "content_creation"
                   },
                   "concurrent_users": 10,
                   "requests_per_user": 3
               }
           ]
           
           results = {}
           
           for scenario in test_scenarios:
               print(f"Testing {scenario['endpoint']}...")
               result = await self.test_endpoint(**scenario)
               results[scenario['endpoint']] = result
               
               # Print immediate results
               print(f"  Success rate: {result.success_rate:.2f}%")
               print(f"  Avg response time: {result.avg_response_time:.3f}s")
               print(f"  P95 response time: {result.p95_response_time:.3f}s")
               
           return results
           
       def generate_report(self, results: Dict[str, LoadTestResult]) -> str:
           """Generate performance report"""
           
           report = ["# Load Test Report\n"]
           report.append(f"Timestamp: {datetime.utcnow().isoformat()}\n")
           report.append(f"Base URL: {self.base_url}\n")
           report.append("\n## Results Summary\n")
           
           for endpoint, result in results.items():
               report.append(f"\n### {endpoint}")
               report.append(f"- Total Requests: {result.total_requests}")
               report.append(f"- Success Rate: {result.success_rate:.2f}%")
               report.append(f"- Average Response Time: {result.avg_response_time:.3f}s")
               report.append(f"- Median Response Time: {result.median_response_time:.3f}s")
               report.append(f"- P95 Response Time: {result.p95_response_time:.3f}s")
               
               if result.errors:
                   error_counts = {}
                   for error in result.errors:
                       error_counts[error] = error_counts.get(error, 0) + 1
                   report.append("\nErrors:")
                   for error, count in error_counts.items():
                       report.append(f"  - {error}: {count} occurrences")
                       
           # Performance assessment
           report.append("\n## Performance Assessment\n")
           
           all_response_times = []
           for result in results.values():
               all_response_times.extend(result.response_times)
               
           if all_response_times:
               overall_p95 = sorted(all_response_times)[int(len(all_response_times) * 0.95)]
               
               if overall_p95 < 0.2:
                   report.append("✅ EXCELLENT: P95 response time < 200ms")
               elif overall_p95 < 0.5:
                   report.append("✅ GOOD: P95 response time < 500ms")
               elif overall_p95 < 1.0:
                   report.append("⚠️ ACCEPTABLE: P95 response time < 1s")
               else:
                   report.append("❌ POOR: P95 response time > 1s")
                   
           return "\n".join(report)
   
   # Run load tests
   async def main():
       tester = LoadTester("https://kolegium.yourdomain.com")
       results = await tester.run_test_suite()
       report = tester.generate_report(results)
       
       with open("load_test_report.md", "w") as f:
           f.write(report)
           
       print("\nLoad test complete. Report saved to load_test_report.md")
   
   if __name__ == "__main__":
       asyncio.run(main())
   ```

6. **Database query optimization**
   ```python
   # src/shared/infrastructure/database/query_optimizer.py
   from sqlalchemy import create_engine, event, text
   from sqlalchemy.engine import Engine
   from sqlalchemy.orm import Session
   import time
   import logging
   from typing import Dict, List
   
   logger = logging.getLogger(__name__)
   
   class QueryOptimizer:
       def __init__(self):
           self.slow_queries: List[Dict[str, Any]] = []
           self.query_stats: Dict[str, Dict[str, Any]] = {}
           
       def setup_query_monitoring(self, engine: Engine):
           """Setup query monitoring and optimization"""
           
           @event.listens_for(Engine, "before_cursor_execute")
           def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
               conn.info.setdefault('query_start_time', []).append(time.time())
               
           @event.listens_for(Engine, "after_cursor_execute")
           def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
               total = time.time() - conn.info['query_start_time'].pop(-1)
               
               # Log slow queries
               if total > 0.1:  # 100ms threshold
                   self.slow_queries.append({
                       'query': statement,
                       'duration': total,
                       'timestamp': datetime.utcnow()
                   })
                   logger.warning(f"Slow query detected ({total:.3f}s): {statement[:100]}...")
                   
               # Track query statistics
               query_hash = hash(statement)
               if query_hash not in self.query_stats:
                   self.query_stats[query_hash] = {
                       'query': statement,
                       'count': 0,
                       'total_time': 0,
                       'avg_time': 0
                   }
                   
               stats = self.query_stats[query_hash]
               stats['count'] += 1
               stats['total_time'] += total
               stats['avg_time'] = stats['total_time'] / stats['count']
               
       def create_indexes(self, session: Session):
           """Create optimized indexes based on query patterns"""
           
           indexes = [
               # Event store indexes
               "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC)",
               "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_aggregate ON events(aggregate_id, version)",
               "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_type ON events(event_type)",
               
               # Agent indexes
               "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_status ON agent_instances(status)",
               "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agents_created ON agent_instances(created_at DESC)",
               
               # Workflow indexes  
               "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workflows_status ON workflows(status)",
               "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_workflow ON workflow_tasks(workflow_id, status)",
               
               # Content indexes
               "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_topics_discovered ON topics(discovered_at DESC)",
               "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_topics_score ON topics(controversy_score DESC)",
           ]
           
           for index_sql in indexes:
               try:
                   session.execute(text(index_sql))
                   session.commit()
                   logger.info(f"Created index: {index_sql}")
               except Exception as e:
                   logger.error(f"Failed to create index: {e}")
                   session.rollback()
                   
       def optimize_common_queries(self):
           """Return optimized versions of common queries"""
           
           return {
               # Use materialized views for complex aggregations
               "agent_performance": """
                   CREATE MATERIALIZED VIEW IF NOT EXISTS agent_performance_stats AS
                   SELECT 
                       agent_id,
                       COUNT(*) as total_tasks,
                       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                       AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_task_duration
                   FROM workflow_tasks
                   WHERE started_at IS NOT NULL
                   GROUP BY agent_id;
                   
                   CREATE UNIQUE INDEX ON agent_performance_stats(agent_id);
               """,
               
               # Partial indexes for common filters
               "active_agents_index": """
                   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_active_agents 
                   ON agent_instances(created_at DESC) 
                   WHERE status = 'active';
               """,
               
               # Covering indexes for read-heavy queries
               "topic_listing_index": """
                   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_topic_listing
                   ON topics(discovered_at DESC) 
                   INCLUDE (title, source, controversy_score);
               """
           }
   ```

**Success Criteria**:
- [ ] HTTPS enabled with auto-renewal
- [ ] Enhanced rate limiting configured
- [ ] Security headers implemented
- [ ] Input validation and sanitization
- [ ] Load tests passing (100 concurrent users)
- [ ] Database query optimization (<100ms avg)
- [ ] All security scans passing

---

### Blok 17: Monitoring, Documentation & Go-Live
**Czas**: 5h | **Agent**: deployment-specialist + documentation-keeper | **Dependencies**: Blok 16

**Task 4.5 + 4.6 + 4.7**: Advanced monitoring + Backup + Documentation

#### Execution Steps:
1. **Setup Prometheus metrics**
   ```yaml
   # monitoring/prometheus.yml
   global:
     scrape_interval: 15s
     evaluation_interval: 15s
   
   scrape_configs:
     - job_name: 'api-gateway'
       static_configs:
         - targets: ['api-gateway:8000']
       metrics_path: '/metrics'
       
     - job_name: 'node-exporter'
       static_configs:
         - targets: ['node-exporter:9100']
         
     - job_name: 'postgres-exporter'
       static_configs:
         - targets: ['postgres-exporter:9187']
         
     - job_name: 'redis-exporter'
       static_configs:
         - targets: ['redis-exporter:9121']
         
   alerting:
     alertmanagers:
       - static_configs:
           - targets: ['alertmanager:9093']
   
   rule_files:
     - '/etc/prometheus/alerts/*.yml'
   ```

2. **Create alert rules**
   ```yaml
   # monitoring/alerts/system_alerts.yml
   groups:
     - name: system_alerts
       interval: 30s
       rules:
         - alert: HighCPUUsage
           expr: rate(process_cpu_seconds_total[5m]) * 100 > 80
           for: 5m
           labels:
             severity: warning
           annotations:
             summary: "High CPU usage detected"
             description: "CPU usage is above 80% (current value: {{ $value }}%)"
             
         - alert: HighMemoryUsage
           expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
           for: 5m
           labels:
             severity: warning
           annotations:
             summary: "High memory usage detected"
             description: "Memory usage is above 85% (current value: {{ $value }}%)"
             
         - alert: APIHighResponseTime
           expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 0.5
           for: 5m
           labels:
             severity: critical
           annotations:
             summary: "API response time is high"
             description: "95th percentile response time is above 500ms"
             
         - alert: AgentError
           expr: rate(agent_errors_total[5m]) > 0.1
           for: 5m
           labels:
             severity: critical
           annotations:
             summary: "Agent errors detected"
             description: "Agent error rate is above threshold"
   ```

3. **Setup Grafana dashboards**
   ```json
   // monitoring/grafana/dashboards/kolegium_overview.json
   {
     "dashboard": {
       "title": "AI Kolegium Overview",
       "panels": [
         {
           "title": "API Response Time",
           "targets": [{
             "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))"
           }],
           "type": "graph"
         },
         {
           "title": "Active Agents",
           "targets": [{
             "expr": "kolegium_active_agents_total"
           }],
           "type": "stat"
         },
         {
           "title": "Decisions Per Hour",
           "targets": [{
             "expr": "rate(kolegium_editorial_decisions_total[1h]) * 3600"
           }],
           "type": "gauge"
         },
         {
           "title": "Human Intervention Rate",
           "targets": [{
             "expr": "rate(kolegium_human_interventions_total[1h]) / rate(kolegium_editorial_decisions_total[1h]) * 100"
           }],
           "type": "graph"
         }
       ]
     }
   }
   ```

4. **Setup automated backups**
   ```bash
   #!/bin/bash
   # scripts/backup.sh
   
   # Configuration
   BACKUP_DIR="/backup/kolegium"
   RETENTION_DAYS=7
   S3_BUCKET="kolegium-backups"
   DATE=$(date +%Y%m%d_%H%M%S)
   
   # Create backup directory
   mkdir -p $BACKUP_DIR
   
   echo "🔄 Starting backup process..."
   
   # 1. Database backup
   echo "📊 Backing up PostgreSQL..."
   docker exec postgres pg_dump -U kolegium kolegium | gzip > $BACKUP_DIR/db_$DATE.sql.gz
   
   # 2. Event store backup (critical data)
   echo "📝 Backing up event store..."
   docker exec postgres pg_dump -U kolegium -t events -t event_snapshots kolegium | gzip > $BACKUP_DIR/events_$DATE.sql.gz
   
   # 3. Redis backup
   echo "💾 Backing up Redis..."
   docker exec redis redis-cli BGSAVE
   sleep 5
   docker cp redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb
   
   # 4. Configuration files
   echo "⚙️ Backing up configurations..."
   tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
     docker-compose.yml \
     docker-compose.prod.yml \
     nginx/nginx.conf \
     .env.production
   
   # 5. Upload to S3
   echo "☁️ Uploading to S3..."
   aws s3 sync $BACKUP_DIR s3://$S3_BUCKET/$(date +%Y/%m/%d)/ \
     --exclude "*" \
     --include "*_$DATE.*"
   
   # 6. Cleanup old backups
   echo "🧹 Cleaning up old backups..."
   find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete
   
   # 7. Verify backup
   echo "✅ Verifying backup..."
   BACKUP_SIZE=$(du -sh $BACKUP_DIR/*_$DATE.* | awk '{sum+=$1} END {print sum}')
   
   # Send notification
   curl -X POST https://api.kolegium.com/monitoring/backup-complete \
     -H "Content-Type: application/json" \
     -d "{\"timestamp\": \"$DATE\", \"size\": \"$BACKUP_SIZE\", \"status\": \"success\"}"
   
   echo "✅ Backup completed successfully!"
   ```

5. **Create disaster recovery documentation**
   ```markdown
   # docs/disaster-recovery.md
   
   # Disaster Recovery Plan - AI Kolegium
   
   ## 🚨 Emergency Contacts
   - Primary: DevOps Lead - +XX XXX XXX XXX
   - Secondary: CTO - +XX XXX XXX XXX
   - Digital Ocean Support: Ticket via dashboard
   
   ## 📊 Recovery Objectives
   - **RTO (Recovery Time Objective)**: 2 hours
   - **RPO (Recovery Point Objective)**: 1 hour
   
   ## 🔄 Backup Schedule
   - **Full backup**: Daily at 02:00 UTC
   - **Incremental**: Every 6 hours
   - **Event store**: Real-time replication
   - **Retention**: 7 days local, 30 days S3
   
   ## 📋 Recovery Procedures
   
   ### 1. Database Failure
   ```bash
   # Stop services
   docker-compose -f docker-compose.prod.yml stop api-gateway
   
   # Restore latest backup
   gunzip < /backup/kolegium/db_LATEST.sql.gz | docker exec -i postgres psql -U kolegium kolegium
   
   # Replay events from event store
   docker exec api-gateway python scripts/replay_events.py --from "2 hours ago"
   
   # Start services
   docker-compose -f docker-compose.prod.yml start api-gateway
   ```
   
   ### 2. Complete System Failure
   ```bash
   # 1. Provision new droplet from snapshot
   doctl compute droplet create kolegium-recovery \
     --image kolegium-snapshot-latest \
     --size s-4vcpu-8gb \
     --region fra1
   
   # 2. Update DNS
   doctl compute domain records update kolegium.com \
     --record-id XXXXX \
     --record-data NEW_IP
   
   # 3. Restore from S3
   aws s3 sync s3://kolegium-backups/latest/ /backup/kolegium/
   
   # 4. Run recovery script
   ./scripts/full_recovery.sh
   ```
   
   ### 3. Agent System Failure
   ```bash
   # Kill all agents
   docker exec api-gateway python scripts/emergency_agent_shutdown.py
   
   # Clear agent state
   docker exec redis redis-cli FLUSHDB
   
   # Restart core agents only
   docker exec api-gateway python scripts/start_core_agents.py
   ```
   
   ## 🔍 Verification Steps
   1. Check health endpoint: `curl https://kolegium.com/api/health`
   2. Verify WebSocket: `wscat -c wss://kolegium.com/ws/agui`
   3. Test agent creation: `curl -X POST https://kolegium.com/api/agents/test`
   4. Check metrics: `https://grafana.kolegium.com`
   
   ## 📈 Post-Recovery
   1. Generate incident report
   2. Update runbooks if needed
   3. Schedule post-mortem meeting
   4. Test backups again
   ```

6. **Create comprehensive API documentation**
   ```python
   # src/interfaces/api/documentation.py
   from fastapi import FastAPI
   from fastapi.openapi.utils import get_openapi
   
   def custom_openapi(app: FastAPI):
       if app.openapi_schema:
           return app.openapi_schema
           
       openapi_schema = get_openapi(
           title="AI Kolegium Redakcyjne API",
           version="1.0.0",
           description="""
           ## Overview
           
           AI Kolegium Redakcyjne is an intelligent editorial system that orchestrates 
           multiple AI agents for content discovery, analysis, and decision-making.
           
           ## Authentication
           
           All API endpoints (except health checks) require JWT authentication:
           
           ```
           Authorization: Bearer <your-jwt-token>
           ```
           
           ## Rate Limiting
           
           - Standard endpoints: 100 requests/minute
           - Auth endpoints: 5 requests/minute
           - Agent creation: 10 requests/hour
           
           ## WebSocket Connection
           
           For real-time updates, connect to:
           ```
           wss://kolegium.com/ws/agui
           ```
           
           ## Common Workflows
           
           ### 1. Create Dynamic Agent
           ```bash
           POST /api/agents/create-from-description
           {
             "description": "Create an agent that monitors tech news"
           }
           ```
           
           ### 2. Execute Workflow
           ```bash
           POST /api/orchestration/workflows/execute
           {
             "template_name": "content_creation"
           }
           ```
           
           ### 3. Request Human Input
           ```bash
           GET /api/human-input/pending-decisions
           ```
           """,
           routes=app.routes,
       )
       
       # Add webhook documentation
       openapi_schema["webhooks"] = {
           "agentEvent": {
               "post": {
                   "requestBody": {
                       "content": {
                           "application/json": {
                               "schema": {
                                   "$ref": "#/components/schemas/AGUIEvent"
                               }
                           }
                       }
                   },
                   "responses": {
                       "200": {"description": "Webhook processed"}
                   }
               }
           }
       }
       
       app.openapi_schema = openapi_schema
       return app.openapi_schema
   ```

7. **Create production checklist**
   ```markdown
   # docs/production-checklist.md
   
   # Production Readiness Checklist
   
   ## ✅ Infrastructure
   - [x] Digital Ocean droplet provisioned (4vCPU, 8GB RAM)
   - [x] Docker & Docker Compose installed
   - [x] SSL certificates (Let's Encrypt)
   - [x] Firewall configured
   - [x] Automated backups
   - [x] Monitoring (Prometheus + Grafana)
   
   ## ✅ Security
   - [x] HTTPS enforced
   - [x] Rate limiting configured
   - [x] Input validation
   - [x] SQL injection protection
   - [x] XSS protection
   - [x] CORS properly configured
   - [x] Security headers
   - [x] Secrets in environment variables
   
   ## ✅ Performance
   - [x] Load tests passed (100 concurrent users)
   - [x] Database indexes optimized
   - [x] Caching implemented (Redis)
   - [x] CDN for static assets
   - [x] Response time < 200ms (p95)
   
   ## ✅ Reliability
   - [x] Health checks on all services
   - [x] Auto-restart on failure
   - [x] Circuit breakers implemented
   - [x] Graceful shutdown
   - [x] Error tracking (Sentry)
   
   ## ✅ Documentation
   - [x] API documentation (OpenAPI)
   - [x] User guides
   - [x] Deployment runbooks
   - [x] Disaster recovery plan
   - [x] Architecture diagrams
   
   ## ✅ Operational
   - [x] Log aggregation
   - [x] Alerts configured
   - [x] On-call rotation
   - [x] Incident response process
   - [x] Post-mortem template
   
   ## 🚀 Launch Steps
   1. Final security scan
   2. Backup current state
   3. Deploy to production
   4. Smoke tests
   5. Monitor for 24h
   6. Announce go-live
   ```

**Success Criteria**:
- [ ] Prometheus metrics collecting
- [ ] Grafana dashboards configured
- [ ] Alerts firing correctly
- [ ] Automated backups running
- [ ] Disaster recovery tested
- [ ] API documentation complete
- [ ] All checklists green
- [ ] Production deployment successful

**Final Deploy**: System is production-ready! 🎉