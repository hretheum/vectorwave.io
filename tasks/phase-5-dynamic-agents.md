# PHASE 5: Dynamic Agent System

## 📋 Bloki Zadań Atomowych

### Blok 18: Agent Factory & Registry
**Czas**: 4h | **Agent**: project-coder | **Dependencies**: Phase 4 complete

**Task 5.0**: Agent Factory & Registry implementation

#### Execution Steps:
1. **Create Agent Factory base classes**
   ```python
   # src/shared/infrastructure/agents/agent_factory.py
   from typing import Dict, Any, List, Optional, Type
   from uuid import UUID, uuid4
   from datetime import datetime
   from dataclasses import dataclass
   import json
   
   from crewai import Agent, Tool
   from pydantic import BaseModel
   
   from ...domain.events.agui_events import AGUIEvent, AGUIEventType
   from ..agui.event_emitter import AGUIEventEmitter
   
   @dataclass
   class AgentTemplate:
       """Template for creating agents"""
       id: UUID
       name: str
       role: str
       goal: str
       backstory: str
       required_tools: List[str]
       optional_tools: List[str]
       default_config: Dict[str, Any]
       created_at: datetime
       created_by: str
       is_public: bool = False
       version: str = "1.0.0"
       
   class DynamicAgentConfig(BaseModel):
       """Configuration for dynamic agent creation"""
       role: str
       goal: str
       backstory: Optional[str] = None
       tools: List[str]
       constraints: Dict[str, Any] = {}
       metadata: Dict[str, Any] = {}
       
   class AgentFactory:
       def __init__(self, 
                    event_emitter: AGUIEventEmitter,
                    tool_registry: 'ToolRegistry'):
           self.event_emitter = event_emitter
           self.tool_registry = tool_registry
           self.agent_templates: Dict[UUID, AgentTemplate] = {}
           self.running_agents: Dict[UUID, Agent] = {}
           
       async def create_agent(self, config: DynamicAgentConfig) -> UUID:
           """Create a new agent dynamically"""
           agent_id = uuid4()
           
           # Emit agent spawn request event
           await self.event_emitter.emit(AGUIEvent(
               type=AGUIEventType.AGENT_SPAWN_REQUEST,
               data={
                   "agent_id": str(agent_id),
                   "config": config.dict(),
                   "status": "creating"
               }
           ))
           
           try:
               # Resolve tools
               tools = await self._resolve_tools(config.tools)
               
               # Generate backstory if not provided
               backstory = config.backstory or self._generate_backstory(
                   config.role, config.goal
               )
               
               # Create CrewAI agent
               agent = Agent(
                   role=config.role,
                   goal=config.goal,
                   backstory=backstory,
                   tools=tools,
                   verbose=True,
                   max_iter=config.constraints.get('max_iterations', 10),
                   memory=config.constraints.get('enable_memory', True)
               )
               
               # Store agent
               self.running_agents[agent_id] = agent
               
               # Emit agent created event
               await self.event_emitter.emit(AGUIEvent(
                   type=AGUIEventType.AGENT_CREATED,
                   data={
                       "agent_id": str(agent_id),
                       "role": config.role,
                       "status": "active",
                       "created_at": datetime.utcnow().isoformat()
                   }
               ))
               
               return agent_id
               
           except Exception as e:
               # Emit failure event
               await self.event_emitter.emit(AGUIEvent(
                   type=AGUIEventType.AGENT_SPAWN_REQUEST,
                   data={
                       "agent_id": str(agent_id),
                       "status": "failed",
                       "error": str(e)
                   }
               ))
               raise
               
       async def _resolve_tools(self, tool_names: List[str]) -> List[Tool]:
           """Resolve tool names to actual Tool instances"""
           tools = []
           for tool_name in tool_names:
               tool = await self.tool_registry.get_tool(tool_name)
               if tool:
                   tools.append(tool)
               else:
                   print(f"Warning: Tool '{tool_name}' not found in registry")
           return tools
           
       def _generate_backstory(self, role: str, goal: str) -> str:
           """Generate a backstory based on role and goal"""
           return f"You are a {role} specialized in achieving the following goal: {goal}. " \
                  f"You have extensive experience and always strive for excellence in your domain."
   ```

2. **Create Agent Registry**
   ```python
   # src/shared/infrastructure/agents/agent_registry.py
   from typing import Dict, List, Optional
   from uuid import UUID
   from datetime import datetime
   import asyncpg
   import json
   
   from .agent_factory import AgentTemplate, DynamicAgentConfig
   
   class AgentRegistry:
       def __init__(self, db_connection: asyncpg.Connection):
           self.db = db_connection
           self._cache: Dict[UUID, AgentTemplate] = {}
           
       async def initialize(self):
           """Create registry tables if not exist"""
           await self.db.execute("""
               CREATE TABLE IF NOT EXISTS agent_templates (
                   id UUID PRIMARY KEY,
                   name VARCHAR(255) NOT NULL,
                   role VARCHAR(255) NOT NULL,
                   goal TEXT NOT NULL,
                   backstory TEXT NOT NULL,
                   required_tools JSONB DEFAULT '[]',
                   optional_tools JSONB DEFAULT '[]',
                   default_config JSONB DEFAULT '{}',
                   created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                   created_by VARCHAR(255) NOT NULL,
                   is_public BOOLEAN DEFAULT FALSE,
                   version VARCHAR(50) DEFAULT '1.0.0',
                   UNIQUE(name, version)
               );
               
               CREATE TABLE IF NOT EXISTS agent_instances (
                   id UUID PRIMARY KEY,
                   template_id UUID REFERENCES agent_templates(id),
                   config JSONB NOT NULL,
                   status VARCHAR(50) NOT NULL,
                   created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                   started_at TIMESTAMP WITH TIME ZONE,
                   stopped_at TIMESTAMP WITH TIME ZONE,
                   metrics JSONB DEFAULT '{}'
               );
               
               CREATE INDEX idx_agent_instances_status ON agent_instances(status);
               CREATE INDEX idx_agent_templates_public ON agent_templates(is_public);
           """)
           
       async def register_template(self, template: AgentTemplate) -> UUID:
           """Register a new agent template"""
           await self.db.execute("""
               INSERT INTO agent_templates 
               (id, name, role, goal, backstory, required_tools, optional_tools,
                default_config, created_by, is_public, version)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
               ON CONFLICT (name, version) DO UPDATE
               SET role = EXCLUDED.role,
                   goal = EXCLUDED.goal,
                   backstory = EXCLUDED.backstory,
                   required_tools = EXCLUDED.required_tools,
                   optional_tools = EXCLUDED.optional_tools,
                   default_config = EXCLUDED.default_config
           """, 
               template.id, template.name, template.role, template.goal,
               template.backstory, json.dumps(template.required_tools),
               json.dumps(template.optional_tools), json.dumps(template.default_config),
               template.created_by, template.is_public, template.version
           )
           
           self._cache[template.id] = template
           return template.id
           
       async def get_template(self, template_id: UUID) -> Optional[AgentTemplate]:
           """Get agent template by ID"""
           if template_id in self._cache:
               return self._cache[template_id]
               
           row = await self.db.fetchrow("""
               SELECT * FROM agent_templates WHERE id = $1
           """, template_id)
           
           if row:
               template = AgentTemplate(
                   id=row['id'],
                   name=row['name'],
                   role=row['role'],
                   goal=row['goal'],
                   backstory=row['backstory'],
                   required_tools=json.loads(row['required_tools']),
                   optional_tools=json.loads(row['optional_tools']),
                   default_config=json.loads(row['default_config']),
                   created_at=row['created_at'],
                   created_by=row['created_by'],
                   is_public=row['is_public'],
                   version=row['version']
               )
               self._cache[template_id] = template
               return template
               
           return None
           
       async def find_public_templates(self, 
                                     query: Optional[str] = None) -> List[AgentTemplate]:
           """Find public agent templates"""
           if query:
               rows = await self.db.fetch("""
                   SELECT * FROM agent_templates 
                   WHERE is_public = TRUE 
                   AND (name ILIKE $1 OR role ILIKE $1 OR goal ILIKE $1)
                   ORDER BY created_at DESC
               """, f"%{query}%")
           else:
               rows = await self.db.fetch("""
                   SELECT * FROM agent_templates 
                   WHERE is_public = TRUE 
                   ORDER BY created_at DESC
               """)
               
           return [
               AgentTemplate(
                   id=row['id'],
                   name=row['name'],
                   role=row['role'],
                   goal=row['goal'],
                   backstory=row['backstory'],
                   required_tools=json.loads(row['required_tools']),
                   optional_tools=json.loads(row['optional_tools']),
                   default_config=json.loads(row['default_config']),
                   created_at=row['created_at'],
                   created_by=row['created_by'],
                   is_public=row['is_public'],
                   version=row['version']
               )
               for row in rows
           ]
   ```

3. **Create Tool Registry**
   ```python
   # src/shared/infrastructure/agents/tool_registry.py
   from typing import Dict, List, Optional, Callable, Any
   from dataclasses import dataclass
   import inspect
   
   from crewai import Tool
   from langchain.tools import Tool as LangchainTool
   
   @dataclass
   class ToolDefinition:
       name: str
       description: str
       func: Callable
       args_schema: Optional[Any] = None
       requires_auth: bool = False
       category: str = "general"
       
   class ToolRegistry:
       def __init__(self):
           self.tools: Dict[str, ToolDefinition] = {}
           self._initialize_builtin_tools()
           
       def _initialize_builtin_tools(self):
           """Register built-in tools"""
           # Web search tool
           self.register_tool(ToolDefinition(
               name="web_search",
               description="Search the web for information",
               func=self._web_search_func,
               category="research"
           ))
           
           # Data analysis tool
           self.register_tool(ToolDefinition(
               name="data_analyzer",
               description="Analyze data and generate insights",
               func=self._data_analyzer_func,
               category="analytics"
           ))
           
           # Content summarizer
           self.register_tool(ToolDefinition(
               name="summarizer",
               description="Summarize long texts",
               func=self._summarizer_func,
               category="content"
           ))
           
       def register_tool(self, tool_def: ToolDefinition):
           """Register a new tool"""
           self.tools[tool_def.name] = tool_def
           
       async def get_tool(self, tool_name: str) -> Optional[Tool]:
           """Get a CrewAI tool by name"""
           if tool_name not in self.tools:
               return None
               
           tool_def = self.tools[tool_name]
           
           # Convert to CrewAI Tool
           return Tool(
               name=tool_def.name,
               description=tool_def.description,
               func=tool_def.func
           )
           
       def get_available_tools(self, category: Optional[str] = None) -> List[str]:
           """Get list of available tool names"""
           if category:
               return [
                   name for name, tool in self.tools.items()
                   if tool.category == category
               ]
           return list(self.tools.keys())
           
       # Example tool implementations
       async def _web_search_func(self, query: str) -> str:
           """Mock web search implementation"""
           # In production, this would call actual search API
           return f"Search results for: {query}"
           
       async def _data_analyzer_func(self, data: str) -> str:
           """Mock data analyzer implementation"""
           return f"Analysis of data: {data}"
           
       async def _summarizer_func(self, text: str, max_length: int = 100) -> str:
           """Mock summarizer implementation"""
           return text[:max_length] + "..."
   ```

4. **Runtime tool resolution system**
   ```python
   # src/shared/infrastructure/agents/tool_resolver.py
   from typing import List, Dict, Any, Optional
   from dataclasses import dataclass
   
   @dataclass
   class ToolRequirement:
       name: str
       required: bool = True
       config: Dict[str, Any] = None
       
   class ToolResolver:
       def __init__(self, tool_registry: ToolRegistry):
           self.tool_registry = tool_registry
           
       async def resolve_tools_from_description(self, 
                                              description: str) -> List[str]:
           """Use LLM to extract required tools from natural language"""
           # This would use an LLM to analyze the description
           # and determine which tools are needed
           
           # Mock implementation
           tool_keywords = {
               "search": ["web_search"],
               "analyze": ["data_analyzer"],
               "summarize": ["summarizer"],
               "monitor": ["web_search", "data_analyzer"],
               "research": ["web_search", "summarizer"],
           }
           
           suggested_tools = []
           description_lower = description.lower()
           
           for keyword, tools in tool_keywords.items():
               if keyword in description_lower:
                   suggested_tools.extend(tools)
                   
           return list(set(suggested_tools))  # Remove duplicates
           
       def validate_tool_access(self, 
                              tool_names: List[str],
                              user_permissions: Dict[str, bool]) -> List[str]:
           """Validate which tools user has access to"""
           allowed_tools = []
           
           for tool_name in tool_names:
               tool = self.tool_registry.tools.get(tool_name)
               if tool:
                   if not tool.requires_auth or user_permissions.get(tool_name, False):
                       allowed_tools.append(tool_name)
                       
           return allowed_tools
   ```

**Success Criteria**:
- [ ] DynamicAgentFactory class implemented
- [ ] Agent Registry with database persistence
- [ ] Agent Template system working
- [ ] Tool Registry with runtime resolution
- [ ] Unit tests for factory and registry

---

### Blok 19: Natural Language Agent Parser
**Czas**: 4h | **Agent**: project-coder | **Dependencies**: Blok 18

**Task 5.1**: Natural Language Agent Parser

#### Execution Steps:
1. **Create NL to Agent Config Parser**
   ```python
   # src/shared/infrastructure/agents/nl_parser.py
   from typing import Dict, Any, List, Optional, Tuple
   import re
   from dataclasses import dataclass
   
   from langchain.llms import OpenAI
   from langchain.prompts import PromptTemplate
   from langchain.output_parsers import PydanticOutputParser
   from pydantic import BaseModel, Field
   
   from .agent_factory import DynamicAgentConfig
   from .tool_resolver import ToolResolver
   
   class ParsedAgentIntent(BaseModel):
       """Parsed agent configuration from natural language"""
       role: str = Field(description="The role/title of the agent")
       goal: str = Field(description="The main goal or objective")
       capabilities: List[str] = Field(description="List of required capabilities")
       constraints: Dict[str, Any] = Field(description="Any limitations or constraints")
       domain: str = Field(description="Domain of expertise")
       
   class NaturalLanguageAgentParser:
       def __init__(self, 
                    llm: OpenAI,
                    tool_resolver: ToolResolver):
           self.llm = llm
           self.tool_resolver = tool_resolver
           self.parser = PydanticOutputParser(pydantic_object=ParsedAgentIntent)
           
           self.prompt_template = PromptTemplate(
               input_variables=["user_request"],
               template="""
               Extract agent configuration from the following user request:
               
               User Request: {user_request}
               
               {format_instructions}
               
               Focus on:
               1. What role should the agent have?
               2. What is the main goal?
               3. What capabilities/tools are needed?
               4. Are there any constraints mentioned?
               5. What domain/area of expertise?
               """,
               partial_variables={
                   "format_instructions": self.parser.get_format_instructions()
               }
           )
           
       async def parse_agent_request(self, 
                                   user_request: str) -> DynamicAgentConfig:
           """Parse natural language request into agent configuration"""
           
           # Use LLM to extract intent
           prompt = self.prompt_template.format(user_request=user_request)
           llm_response = await self.llm.apredict(prompt)
           
           try:
               parsed_intent = self.parser.parse(llm_response)
           except Exception as e:
               # Fallback to regex parsing
               parsed_intent = self._fallback_parse(user_request)
               
           # Resolve tools from capabilities
           tools = await self.tool_resolver.resolve_tools_from_description(
               " ".join(parsed_intent.capabilities)
           )
           
           # Generate backstory
           backstory = self._generate_backstory(
               parsed_intent.role, 
               parsed_intent.goal,
               parsed_intent.domain
           )
           
           # Create config
           config = DynamicAgentConfig(
               role=parsed_intent.role,
               goal=parsed_intent.goal,
               backstory=backstory,
               tools=tools,
               constraints=parsed_intent.constraints,
               metadata={
                   "domain": parsed_intent.domain,
                   "original_request": user_request,
                   "parsed_capabilities": parsed_intent.capabilities
               }
           )
           
           return config
           
       def _fallback_parse(self, user_request: str) -> ParsedAgentIntent:
           """Fallback regex-based parsing"""
           # Extract patterns
           role_match = re.search(r"(agent|assistant|bot) (?:that|to|for) (\w+)", 
                                 user_request, re.I)
           goal_match = re.search(r"(monitor|analyze|track|search|find|create) (.+)", 
                                 user_request, re.I)
           
           role = "Custom Agent"
           if role_match:
               role = f"{role_match.group(2).title()} Agent"
               
           goal = "Assist with tasks"
           if goal_match:
               goal = f"{goal_match.group(1).title()} {goal_match.group(2)}"
               
           # Extract capabilities from keywords
           capabilities = []
           capability_keywords = {
               "search": "web search",
               "analyze": "data analysis",
               "monitor": "monitoring",
               "report": "reporting",
               "summarize": "summarization"
           }
           
           for keyword, capability in capability_keywords.items():
               if keyword in user_request.lower():
                   capabilities.append(capability)
                   
           return ParsedAgentIntent(
               role=role,
               goal=goal,
               capabilities=capabilities or ["general assistance"],
               constraints={},
               domain="general"
           )
           
       def _generate_backstory(self, role: str, goal: str, domain: str) -> str:
           """Generate appropriate backstory"""
           templates = {
               "research": f"You are a {role} with deep expertise in {domain}. "
                          f"Your mission is to {goal} using cutting-edge research methods.",
               "monitoring": f"You are a vigilant {role} specialized in {domain}. "
                            f"You continuously {goal} and alert on important changes.",
               "analysis": f"You are an analytical {role} focusing on {domain}. "
                           f"You excel at {goal} providing data-driven insights.",
               "general": f"You are a skilled {role} working in {domain}. "
                         f"Your primary objective is to {goal} efficiently and accurately."
           }
           
           # Select template based on keywords
           for key, template in templates.items():
               if key in goal.lower() or key in domain.lower():
                   return template
                   
           return templates["general"]
   ```

2. **Create capability validator**
   ```python
   # src/shared/infrastructure/agents/capability_validator.py
   from typing import List, Dict, Any, Tuple
   from dataclasses import dataclass
   
   @dataclass
   class ValidationResult:
       is_valid: bool
       errors: List[str]
       warnings: List[str]
       suggestions: List[str]
       
   class CapabilityValidator:
       def __init__(self, tool_registry: 'ToolRegistry'):
           self.tool_registry = tool_registry
           self.capability_rules = self._load_capability_rules()
           
       def _load_capability_rules(self) -> Dict[str, Dict[str, Any]]:
           """Load rules for capability validation"""
           return {
               "web_search": {
                   "requires": [],
                   "conflicts_with": [],
                   "rate_limit": 100,  # per hour
                   "requires_auth": False
               },
               "data_analyzer": {
                   "requires": ["web_search"],  # Often needs data from search
                   "conflicts_with": [],
                   "rate_limit": 50,
                   "requires_auth": False
               },
               "file_access": {
                   "requires": [],
                   "conflicts_with": ["sandboxed"],
                   "rate_limit": None,
                   "requires_auth": True
               },
               "api_caller": {
                   "requires": [],
                   "conflicts_with": [],
                   "rate_limit": 1000,
                   "requires_auth": True
               }
           }
           
       def validate_capabilities(self, 
                               requested_tools: List[str],
                               user_permissions: Dict[str, bool]) -> ValidationResult:
           """Validate requested capabilities"""
           errors = []
           warnings = []
           suggestions = []
           
           # Check if tools exist
           for tool in requested_tools:
               if tool not in self.tool_registry.tools:
                   errors.append(f"Tool '{tool}' not found in registry")
                   # Suggest similar tools
                   similar = self._find_similar_tools(tool)
                   if similar:
                       suggestions.append(f"Did you mean: {', '.join(similar)}?")
                       
           # Check permissions
           for tool in requested_tools:
               if tool in self.capability_rules:
                   rule = self.capability_rules[tool]
                   if rule.get("requires_auth") and not user_permissions.get(tool, False):
                       errors.append(f"Tool '{tool}' requires authentication")
                       
           # Check dependencies
           for tool in requested_tools:
               if tool in self.capability_rules:
                   rule = self.capability_rules[tool]
                   for required in rule.get("requires", []):
                       if required not in requested_tools:
                           warnings.append(
                               f"Tool '{tool}' works better with '{required}'"
                           )
                           suggestions.append(f"Consider adding '{required}' tool")
                           
           # Check conflicts
           for tool in requested_tools:
               if tool in self.capability_rules:
                   rule = self.capability_rules[tool]
                   for conflict in rule.get("conflicts_with", []):
                       if conflict in requested_tools:
                           errors.append(
                               f"Tool '{tool}' conflicts with '{conflict}'"
                           )
                           
           return ValidationResult(
               is_valid=len(errors) == 0,
               errors=errors,
               warnings=warnings,
               suggestions=suggestions
           )
           
       def _find_similar_tools(self, tool_name: str) -> List[str]:
           """Find similar tool names using fuzzy matching"""
           from difflib import get_close_matches
           all_tools = list(self.tool_registry.tools.keys())
           return get_close_matches(tool_name, all_tools, n=3, cutoff=0.6)
   ```

3. **Create security constraints checker**
   ```python
   # src/shared/infrastructure/agents/security_constraints.py
   from typing import Dict, Any, List, Optional
   from dataclasses import dataclass
   from enum import Enum
   
   class SecurityLevel(Enum):
       SANDBOX = "sandbox"      # Highly restricted
       STANDARD = "standard"    # Normal restrictions  
       ELEVATED = "elevated"    # Some elevated permissions
       ADMIN = "admin"         # Full permissions
       
   @dataclass
   class SecurityConstraints:
       max_memory_mb: int = 512
       max_cpu_percent: int = 25
       max_execution_time_seconds: int = 300
       allowed_tools: List[str] = None
       blocked_tools: List[str] = None
       network_access: bool = True
       file_system_access: bool = False
       max_tokens_per_request: int = 4000
       rate_limit_per_hour: int = 100
       
   class SecurityConstraintChecker:
       def __init__(self):
           self.security_levels = self._define_security_levels()
           
       def _define_security_levels(self) -> Dict[SecurityLevel, SecurityConstraints]:
           """Define constraints for each security level"""
           return {
               SecurityLevel.SANDBOX: SecurityConstraints(
                   max_memory_mb=256,
                   max_cpu_percent=10,
                   max_execution_time_seconds=60,
                   allowed_tools=["web_search", "summarizer"],
                   network_access=True,
                   file_system_access=False,
                   rate_limit_per_hour=50
               ),
               SecurityLevel.STANDARD: SecurityConstraints(
                   max_memory_mb=512,
                   max_cpu_percent=25,
                   max_execution_time_seconds=300,
                   blocked_tools=["file_delete", "system_command"],
                   network_access=True,
                   file_system_access=False,
                   rate_limit_per_hour=100
               ),
               SecurityLevel.ELEVATED: SecurityConstraints(
                   max_memory_mb=1024,
                   max_cpu_percent=50,
                   max_execution_time_seconds=600,
                   blocked_tools=["system_command"],
                   network_access=True,
                   file_system_access=True,
                   rate_limit_per_hour=500
               ),
               SecurityLevel.ADMIN: SecurityConstraints(
                   max_memory_mb=2048,
                   max_cpu_percent=100,
                   max_execution_time_seconds=3600,
                   network_access=True,
                   file_system_access=True,
                   rate_limit_per_hour=10000
               )
           }
           
       def get_constraints_for_user(self, 
                                  user_role: str,
                                  custom_limits: Optional[Dict[str, Any]] = None
                                  ) -> SecurityConstraints:
           """Get security constraints based on user role"""
           # Map user roles to security levels
           role_mapping = {
               "guest": SecurityLevel.SANDBOX,
               "user": SecurityLevel.STANDARD,
               "power_user": SecurityLevel.ELEVATED,
               "admin": SecurityLevel.ADMIN
           }
           
           security_level = role_mapping.get(user_role, SecurityLevel.SANDBOX)
           constraints = self.security_levels[security_level]
           
           # Apply custom limits if provided
           if custom_limits:
               # Create a copy and update with custom limits
               import copy
               constraints = copy.deepcopy(constraints)
               for key, value in custom_limits.items():
                   if hasattr(constraints, key):
                       setattr(constraints, key, value)
                       
           return constraints
           
       def validate_agent_config(self,
                               config: DynamicAgentConfig,
                               constraints: SecurityConstraints) -> ValidationResult:
           """Validate agent configuration against security constraints"""
           errors = []
           warnings = []
           
           # Check tools
           if constraints.allowed_tools:
               for tool in config.tools:
                   if tool not in constraints.allowed_tools:
                       errors.append(f"Tool '{tool}' not allowed for security level")
                       
           if constraints.blocked_tools:
               for tool in config.tools:
                   if tool in constraints.blocked_tools:
                       errors.append(f"Tool '{tool}' is blocked for security reasons")
                       
           # Check resource constraints in config
           if config.constraints.get("max_memory_mb", 0) > constraints.max_memory_mb:
               errors.append(
                   f"Requested memory {config.constraints['max_memory_mb']}MB "
                   f"exceeds limit {constraints.max_memory_mb}MB"
               )
               
           # Add more validation as needed
           
           return ValidationResult(
               is_valid=len(errors) == 0,
               errors=errors,
               warnings=warnings,
               suggestions=[]
           )
   ```

4. **Integration endpoint**
   ```python
   # src/interfaces/api/controllers/agent_creation_controller.py
   from fastapi import APIRouter, HTTPException, Depends
   from pydantic import BaseModel
   from typing import Dict, Any, Optional
   
   from dependency_injector.wiring import inject, Provide
   
   from src.shared.infrastructure.agents.nl_parser import NaturalLanguageAgentParser
   from src.shared.infrastructure.agents.agent_factory import AgentFactory
   from src.shared.infrastructure.agents.capability_validator import CapabilityValidator
   from src.shared.infrastructure.agents.security_constraints import (
       SecurityConstraintChecker
   )
   from src.shared.infrastructure.container import Container
   
   router = APIRouter(prefix="/api/agents", tags=["agents"])
   
   class CreateAgentRequest(BaseModel):
       description: str
       constraints: Optional[Dict[str, Any]] = {}
       
   class ValidateAgentRequest(BaseModel):
       description: str
       
   router.post("/create-from-description")
   @inject
   async def create_agent_from_description(
       request: CreateAgentRequest,
       nl_parser: NaturalLanguageAgentParser = Provide[Container.nl_parser],
       agent_factory: AgentFactory = Provide[Container.agent_factory],
       capability_validator: CapabilityValidator = Provide[Container.capability_validator],
       security_checker: SecurityConstraintChecker = Provide[Container.security_checker],
       current_user: dict = Depends(get_current_user)  # Auth dependency
   ):
       """Create an agent from natural language description"""
       
       try:
           # Parse natural language to config
           agent_config = await nl_parser.parse_agent_request(request.description)
           
           # Get user permissions and constraints
           user_permissions = current_user.get("permissions", {})
           user_role = current_user.get("role", "user")
           
           # Validate capabilities
           capability_result = capability_validator.validate_capabilities(
               agent_config.tools,
               user_permissions
           )
           
           if not capability_result.is_valid:
               raise HTTPException(
                   status_code=400,
                   detail={
                       "errors": capability_result.errors,
                       "suggestions": capability_result.suggestions
                   }
               )
               
           # Check security constraints
           constraints = security_checker.get_constraints_for_user(
               user_role,
               request.constraints
           )
           
           security_result = security_checker.validate_agent_config(
               agent_config,
               constraints
           )
           
           if not security_result.is_valid:
               raise HTTPException(
                   status_code=403,
                   detail={
                       "errors": security_result.errors,
                       "message": "Security constraints violated"
                   }
               )
               
           # Create agent
           agent_id = await agent_factory.create_agent(agent_config)
           
           return {
               "success": True,
               "agent_id": str(agent_id),
               "config": agent_config.dict(),
               "warnings": capability_result.warnings
           }
           
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))
           
   router.post("/validate-description")
   @inject
   async def validate_agent_description(
       request: ValidateAgentRequest,
       nl_parser: NaturalLanguageAgentParser = Provide[Container.nl_parser],
       capability_validator: CapabilityValidator = Provide[Container.capability_validator]
   ):
       """Validate agent description without creating"""
       
       try:
           # Parse description
           agent_config = await nl_parser.parse_agent_request(request.description)
           
           # Validate capabilities
           capability_result = capability_validator.validate_capabilities(
               agent_config.tools,
               {}  # No permissions check for validation
           )
           
           return {
               "valid": capability_result.is_valid,
               "parsed_config": agent_config.dict(),
               "validation": {
                   "errors": capability_result.errors,
                   "warnings": capability_result.warnings,
                   "suggestions": capability_result.suggestions
               }
           }
           
       except Exception as e:
           return {
               "valid": False,
               "error": str(e)
           }
   ```

**Success Criteria**:
- [ ] NL to agent config parser working with LLM
- [ ] Fallback parsing for common patterns
- [ ] Capability validation with suggestions
- [ ] Security constraints enforcement
- [ ] API endpoints for validation and creation
- [ ] Integration tests for various descriptions

---

### Blok 20: Dynamic Agent UI & Management
**Czas**: 3h | **Agent**: project-coder | **Dependencies**: Blok 19

**Task 5.2**: Chat-based Agent Creation UI

#### Execution Steps:
1. **Create Agent Creator component**
   ```typescript
   // frontend/src/components/agents/AgentCreator.tsx
   import React, { useState } from 'react';
   import { Send, Loader, AlertCircle, CheckCircle } from 'lucide-react';
   import { useAGUIConnection } from '../../hooks/useAGUIConnection';
   import { Button } from '../ui/Button';
   import { Textarea } from '../ui/Textarea';
   import { AgentPreview } from './AgentPreview';
   import { CapabilitySelector } from './CapabilitySelector';
   
   interface AgentConfig {
     role: string;
     goal: string;
     backstory: string;
     tools: string[];
     constraints: Record<string, any>;
   }
   
   interface ValidationResult {
     valid: boolean;
     parsed_config?: AgentConfig;
     validation?: {
       errors: string[];
       warnings: string[];
       suggestions: string[];
     };
   }
   
   export const AgentCreator: React.FC = () => {
     const [description, setDescription] = useState('');
     const [isValidating, setIsValidating] = useState(false);
     const [isCreating, setIsCreating] = useState(false);
     const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
     const [createdAgentId, setCreatedAgentId] = useState<string | null>(null);
     const [showAdvanced, setShowAdvanced] = useState(false);
     
     const { subscribe, unsubscribe } = useAGUIConnection();
     
     const handleValidate = async () => {
       setIsValidating(true);
       setValidationResult(null);
       
       try {
         const response = await fetch('/api/agents/validate-description', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ description }),
         });
         
         const result = await response.json();
         setValidationResult(result);
       } catch (error) {
         console.error('Validation error:', error);
       } finally {
         setIsValidating(false);
       }
     };
     
     const handleCreate = async () => {
       if (!validationResult?.valid) return;
       
       setIsCreating(true);
       
       try {
         const response = await fetch('/api/agents/create-from-description', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ 
             description,
             constraints: validationResult.parsed_config?.constraints || {}
           }),
         });
         
         const result = await response.json();
         
         if (result.success) {
           setCreatedAgentId(result.agent_id);
           // Clear form
           setDescription('');
           setValidationResult(null);
         } else {
           throw new Error(result.detail || 'Failed to create agent');
         }
       } catch (error) {
         console.error('Creation error:', error);
         alert(`Failed to create agent: ${error.message}`);
       } finally {
         setIsCreating(false);
       }
     };
     
     const exampleDescriptions = [
       "Create an agent that monitors GitHub repositories for security vulnerabilities",
       "I need an assistant to analyze competitor pricing and generate weekly reports",
       "Build me a research agent that tracks AI news and summarizes key developments",
       "Create an agent to monitor social media mentions and alert on negative sentiment"
     ];
     
     return (
       <div className="max-w-4xl mx-auto p-6">
         <div className="mb-8">
           <h2 className="text-3xl font-bold mb-2">Create Custom Agent</h2>
           <p className="text-gray-600">
             Describe what you want your agent to do in natural language
           </p>
         </div>
         
         {/* Example descriptions */}
         <div className="mb-6">
           <p className="text-sm font-medium mb-2">Examples:</p>
           <div className="flex flex-wrap gap-2">
             {exampleDescriptions.map((example, idx) => (
               <button
                 key={idx}
                 onClick={() => setDescription(example)}
                 className="text-xs px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full"
               >
                 {example.substring(0, 50)}...
               </button>
             ))}
           </div>
         </div>
         
         {/* Description input */}
         <div className="mb-6">
           <label className="block text-sm font-medium mb-2">
             Agent Description
           </label>
           <Textarea
             value={description}
             onChange={(e) => setDescription(e.target.value)}
             placeholder="Describe your agent's purpose and capabilities..."
             rows={4}
             className="w-full"
           />
           <div className="mt-2 flex justify-between items-center">
             <button
               onClick={() => setShowAdvanced(!showAdvanced)}
               className="text-sm text-blue-600 hover:text-blue-700"
             >
               {showAdvanced ? 'Hide' : 'Show'} advanced options
             </button>
             <Button
               onClick={handleValidate}
               disabled={!description.trim() || isValidating}
               variant="secondary"
             >
               {isValidating ? (
                 <>
                   <Loader className="animate-spin h-4 w-4 mr-2" />
                   Validating...
                 </>
               ) : (
                 'Validate'
               )}
             </Button>
           </div>
         </div>
         
         {/* Advanced options */}
         {showAdvanced && (
           <div className="mb-6 p-4 bg-gray-50 rounded-lg">
             <h3 className="font-medium mb-3">Advanced Options</h3>
             <CapabilitySelector
               selected={validationResult?.parsed_config?.tools || []}
               onChange={(tools) => {
                 // Update tools in validation result
               }}
             />
           </div>
         )}
         
         {/* Validation results */}
         {validationResult && (
           <div className="mb-6 space-y-4">
             {/* Preview */}
             {validationResult.valid && validationResult.parsed_config && (
               <AgentPreview config={validationResult.parsed_config} />
             )}
             
             {/* Errors */}
             {validationResult.validation?.errors.length > 0 && (
               <div className="p-4 bg-red-50 rounded-lg">
                 <div className="flex items-start">
                   <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 mr-2" />
                   <div>
                     <p className="font-medium text-red-900">Validation Errors</p>
                     <ul className="mt-1 text-sm text-red-700 list-disc list-inside">
                       {validationResult.validation.errors.map((error, idx) => (
                         <li key={idx}>{error}</li>
                       ))}
                     </ul>
                   </div>
                 </div>
               </div>
             )}
             
             {/* Warnings */}
             {validationResult.validation?.warnings.length > 0 && (
               <div className="p-4 bg-yellow-50 rounded-lg">
                 <div className="flex items-start">
                   <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5 mr-2" />
                   <div>
                     <p className="font-medium text-yellow-900">Warnings</p>
                     <ul className="mt-1 text-sm text-yellow-700 list-disc list-inside">
                       {validationResult.validation.warnings.map((warning, idx) => (
                         <li key={idx}>{warning}</li>
                       ))}
                     </ul>
                   </div>
                 </div>
               </div>
             )}
             
             {/* Suggestions */}
             {validationResult.validation?.suggestions.length > 0 && (
               <div className="p-4 bg-blue-50 rounded-lg">
                 <div className="flex items-start">
                   <Info className="h-5 w-5 text-blue-500 mt-0.5 mr-2" />
                   <div>
                     <p className="font-medium text-blue-900">Suggestions</p>
                     <ul className="mt-1 text-sm text-blue-700 list-disc list-inside">
                       {validationResult.validation.suggestions.map((suggestion, idx) => (
                         <li key={idx}>{suggestion}</li>
                       ))}
                     </ul>
                   </div>
                 </div>
               </div>
             )}
           </div>
         )}
         
         {/* Create button */}
         {validationResult?.valid && (
           <div className="flex justify-end">
             <Button
               onClick={handleCreate}
               disabled={isCreating}
               size="lg"
             >
               {isCreating ? (
                 <>
                   <Loader className="animate-spin h-5 w-5 mr-2" />
                   Creating Agent...
                 </>
               ) : (
                 <>
                   <Send className="h-5 w-5 mr-2" />
                   Create Agent
                 </>
               )}
             </Button>
           </div>
         )}
         
         {/* Success message */}
         {createdAgentId && (
           <div className="mt-6 p-4 bg-green-50 rounded-lg">
             <div className="flex items-center">
               <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
               <div>
                 <p className="font-medium text-green-900">
                   Agent Created Successfully!
                 </p>
                 <p className="text-sm text-green-700">
                   Agent ID: {createdAgentId}
                 </p>
               </div>
             </div>
           </div>
         )}
       </div>
     );
   };
   ```

2. **Create Agent Preview component**
   ```typescript
   // frontend/src/components/agents/AgentPreview.tsx
   import React from 'react';
   import { Bot, Target, Tool, Shield } from 'lucide-react';
   import { Badge } from '../ui/Badge';
   
   interface AgentPreviewProps {
     config: {
       role: string;
       goal: string;
       backstory: string;
       tools: string[];
       constraints?: Record<string, any>;
     };
   }
   
   export const AgentPreview: React.FC<AgentPreviewProps> = ({ config }) => {
     return (
       <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
         <div className="flex items-start mb-4">
           <Bot className="h-8 w-8 text-blue-500 mr-3 mt-1" />
           <div className="flex-1">
             <h3 className="text-xl font-semibold">{config.role}</h3>
             <p className="text-gray-600 mt-1">{config.goal}</p>
           </div>
         </div>
         
         {/* Backstory */}
         <div className="mb-4">
           <div className="flex items-center mb-2">
             <Target className="h-4 w-4 text-gray-400 mr-2" />
             <span className="text-sm font-medium">Backstory</span>
           </div>
           <p className="text-sm text-gray-600 italic">"{config.backstory}"</p>
         </div>
         
         {/* Tools */}
         <div className="mb-4">
           <div className="flex items-center mb-2">
             <Tool className="h-4 w-4 text-gray-400 mr-2" />
             <span className="text-sm font-medium">Capabilities</span>
           </div>
           <div className="flex flex-wrap gap-2">
             {config.tools.map((tool, idx) => (
               <Badge key={idx} variant="secondary" size="sm">
                 {tool.replace(/_/g, ' ')}
               </Badge>
             ))}
           </div>
         </div>
         
         {/* Constraints */}
         {config.constraints && Object.keys(config.constraints).length > 0 && (
           <div>
             <div className="flex items-center mb-2">
               <Shield className="h-4 w-4 text-gray-400 mr-2" />
               <span className="text-sm font-medium">Constraints</span>
             </div>
             <div className="text-sm text-gray-600">
               {Object.entries(config.constraints).map(([key, value]) => (
                 <div key={key} className="flex justify-between py-1">
                   <span className="capitalize">{key.replace(/_/g, ' ')}:</span>
                   <span className="font-mono">{String(value)}</span>
                 </div>
               ))}
             </div>
           </div>
         )}
       </div>
     );
   };
   ```

3. **Create Capability Selector component**
   ```typescript
   // frontend/src/components/agents/CapabilitySelector.tsx
   import React, { useState, useEffect } from 'react';
   import { Check, X, Info } from 'lucide-react';
   
   interface Tool {
     name: string;
     description: string;
     category: string;
     requires_auth: boolean;
   }
   
   interface CapabilitySelectorProps {
     selected: string[];
     onChange: (selected: string[]) => void;
   }
   
   export const CapabilitySelector: React.FC<CapabilitySelectorProps> = ({
     selected,
     onChange,
   }) => {
     const [availableTools, setAvailableTools] = useState<Tool[]>([]);
     const [loading, setLoading] = useState(true);
     
     useEffect(() => {
       fetchAvailableTools();
     }, []);
     
     const fetchAvailableTools = async () => {
       try {
         const response = await fetch('/api/agents/tools');
         const tools = await response.json();
         setAvailableTools(tools);
       } catch (error) {
         console.error('Failed to fetch tools:', error);
       } finally {
         setLoading(false);
       }
     };
     
     const toggleTool = (toolName: string) => {
       if (selected.includes(toolName)) {
         onChange(selected.filter(t => t !== toolName));
       } else {
         onChange([...selected, toolName]);
       }
     };
     
     const groupedTools = availableTools.reduce((acc, tool) => {
       if (!acc[tool.category]) {
         acc[tool.category] = [];
       }
       acc[tool.category].push(tool);
       return acc;
     }, {} as Record<string, Tool[]>);
     
     if (loading) {
       return <div>Loading capabilities...</div>;
     }
     
     return (
       <div className="space-y-4">
         {Object.entries(groupedTools).map(([category, tools]) => (
           <div key={category}>
             <h4 className="text-sm font-medium capitalize mb-2">
               {category.replace(/_/g, ' ')}
             </h4>
             <div className="grid grid-cols-2 gap-2">
               {tools.map(tool => (
                 <button
                   key={tool.name}
                   onClick={() => toggleTool(tool.name)}
                   className={`
                     flex items-center justify-between p-3 rounded-lg border
                     transition-colors text-left
                     ${selected.includes(tool.name)
                       ? 'bg-blue-50 border-blue-300'
                       : 'bg-white border-gray-200 hover:bg-gray-50'
                     }
                   `}
                 >
                   <div className="flex-1">
                     <div className="flex items-center">
                       <span className="text-sm font-medium">
                         {tool.name.replace(/_/g, ' ')}
                       </span>
                       {tool.requires_auth && (
                         <Info className="h-3 w-3 text-yellow-500 ml-1" />
                       )}
                     </div>
                     <p className="text-xs text-gray-500 mt-1">
                       {tool.description}
                     </p>
                   </div>
                   <div className="ml-2">
                     {selected.includes(tool.name) ? (
                       <Check className="h-4 w-4 text-blue-600" />
                     ) : (
                       <div className="h-4 w-4 border border-gray-300 rounded" />
                     )}
                   </div>
                 </button>
               ))}
             </div>
           </div>
         ))}
       </div>
     );
   };
   ```

4. **Create slash command handler**
   ```typescript
   // frontend/src/hooks/useSlashCommands.ts
   import { useState, useCallback } from 'react';
   
   interface SlashCommand {
     command: string;
     description: string;
     handler: (args: string) => void;
   }
   
   export const useSlashCommands = () => {
     const [commands] = useState<SlashCommand[]>([
       {
         command: '/spawn-agent',
         description: 'Create a new agent from description',
         handler: (args: string) => {
           // Open agent creator with pre-filled description
           window.dispatchEvent(new CustomEvent('open-agent-creator', {
             detail: { description: args }
           }));
         }
       },
       {
         command: '/list-agents',
         description: 'List all active agents',
         handler: () => {
           window.dispatchEvent(new CustomEvent('open-agent-manager'));
         }
       },
       {
         command: '/stop-agent',
         description: 'Stop an agent by ID',
         handler: (agentId: string) => {
           if (!agentId) {
             alert('Please provide agent ID: /stop-agent <id>');
             return;
           }
           // Call API to stop agent
           fetch(`/api/agents/${agentId}/stop`, { method: 'POST' })
             .then(() => alert(`Agent ${agentId} stopped`))
             .catch(err => alert(`Failed to stop agent: ${err.message}`));
         }
       }
     ]);
     
     const executeCommand = useCallback((input: string) => {
       const parts = input.split(' ');
       const commandName = parts[0];
       const args = parts.slice(1).join(' ');
       
       const command = commands.find(c => c.command === commandName);
       if (command) {
         command.handler(args);
         return true;
       }
       
       return false;
     }, [commands]);
     
     return {
       commands,
       executeCommand
     };
   };
   ```

**Success Criteria**:
- [ ] Agent Creator UI with natural language input
- [ ] Real-time validation and preview
- [ ] Capability selector with categories
- [ ] Slash command support (/spawn-agent)
- [ ] Responsive design
- [ ] Integration tests for UI flow

---

### Blok 21: Agent Lifecycle & Security
**Czas**: 7h | **Agent**: project-coder + deployment-specialist | **Dependencies**: Blok 20

**Task 5.3 + 5.4**: Agent Lifecycle Management + Security

#### Execution Steps:
1. **Create Lifecycle Manager**
   ```python
   # src/shared/infrastructure/agents/lifecycle_manager.py
   from typing import Dict, List, Optional, Any
   from uuid import UUID
   from datetime import datetime, timedelta
   from enum import Enum
   import asyncio
   import psutil
   import resource
   
   from crewai import Agent, Crew
   
   from ...domain.events.agui_events import AGUIEvent, AGUIEventType
   from ..agui.event_emitter import AGUIEventEmitter
   from .agent_factory import AgentFactory
   
   class AgentStatus(Enum):
       CREATING = "creating"
       ACTIVE = "active"
       PAUSED = "paused"
       STOPPING = "stopping"
       STOPPED = "stopped"
       ERROR = "error"
       
   class AgentMetrics:
       def __init__(self):
           self.cpu_usage: float = 0.0
           self.memory_usage_mb: float = 0.0
           self.tasks_completed: int = 0
           self.tasks_failed: int = 0
           self.total_execution_time: float = 0.0
           self.last_activity: datetime = datetime.utcnow()
           
   class ManagedAgent:
       def __init__(self, 
                    agent_id: UUID,
                    agent: Agent,
                    config: Dict[str, Any],
                    constraints: 'SecurityConstraints'):
           self.agent_id = agent_id
           self.agent = agent
           self.config = config
           self.constraints = constraints
           self.status = AgentStatus.ACTIVE
           self.metrics = AgentMetrics()
           self.created_at = datetime.utcnow()
           self.process = None
           
   class AgentLifecycleManager:
       def __init__(self,
                    event_emitter: AGUIEventEmitter,
                    agent_factory: AgentFactory):
           self.event_emitter = event_emitter
           self.agent_factory = agent_factory
           self.managed_agents: Dict[UUID, ManagedAgent] = {}
           self.monitoring_task = None
           
       async def start_monitoring(self):
           """Start background monitoring of all agents"""
           if not self.monitoring_task:
               self.monitoring_task = asyncio.create_task(self._monitor_agents())
               
       async def stop_monitoring(self):
           """Stop background monitoring"""
           if self.monitoring_task:
               self.monitoring_task.cancel()
               await asyncio.gather(self.monitoring_task, return_exceptions=True)
               
       async def _monitor_agents(self):
           """Monitor agent health and resource usage"""
           while True:
               try:
                   for agent_id, managed_agent in self.managed_agents.items():
                       if managed_agent.status == AgentStatus.ACTIVE:
                           # Update metrics
                           await self._update_agent_metrics(managed_agent)
                           
                           # Check constraints
                           await self._check_constraints(managed_agent)
                           
                           # Emit metrics event
                           await self.event_emitter.emit(AGUIEvent(
                               type=AGUIEventType.AGENT_METRICS_UPDATE,
                               data={
                                   "agent_id": str(agent_id),
                                   "metrics": {
                                       "cpu_usage": managed_agent.metrics.cpu_usage,
                                       "memory_mb": managed_agent.metrics.memory_usage_mb,
                                       "tasks_completed": managed_agent.metrics.tasks_completed,
                                       "uptime_seconds": (
                                           datetime.utcnow() - managed_agent.created_at
                                       ).total_seconds()
                                   }
                               }
                           ))
                           
                   await asyncio.sleep(5)  # Monitor every 5 seconds
                   
               except Exception as e:
                   print(f"Monitoring error: {e}")
                   await asyncio.sleep(10)
                   
       async def _update_agent_metrics(self, managed_agent: ManagedAgent):
           """Update resource usage metrics for an agent"""
           if managed_agent.process:
               try:
                   # Get process stats
                   process = psutil.Process(managed_agent.process.pid)
                   managed_agent.metrics.cpu_usage = process.cpu_percent()
                   managed_agent.metrics.memory_usage_mb = (
                       process.memory_info().rss / 1024 / 1024
                   )
               except psutil.NoSuchProcess:
                   managed_agent.status = AgentStatus.ERROR
                   
       async def _check_constraints(self, managed_agent: ManagedAgent):
           """Check if agent is violating constraints"""
           constraints = managed_agent.constraints
           metrics = managed_agent.metrics
           
           violations = []
           
           # Check memory
           if metrics.memory_usage_mb > constraints.max_memory_mb:
               violations.append(f"Memory usage {metrics.memory_usage_mb}MB exceeds limit")
               
           # Check CPU
           if metrics.cpu_usage > constraints.max_cpu_percent:
               violations.append(f"CPU usage {metrics.cpu_usage}% exceeds limit")
               
           # Check execution time
           uptime = (datetime.utcnow() - managed_agent.created_at).total_seconds()
           if uptime > constraints.max_execution_time_seconds:
               violations.append("Execution time exceeded")
               
           if violations:
               # Pause agent
               await self.pause_agent(managed_agent.agent_id)
               
               # Emit violation event
               await self.event_emitter.emit(AGUIEvent(
                   type=AGUIEventType.AGENT_CONSTRAINT_VIOLATION,
                   data={
                       "agent_id": str(managed_agent.agent_id),
                       "violations": violations,
                       "action": "paused"
                   }
               ))
               
       async def start_agent(self, 
                           agent_id: UUID,
                           agent: Agent,
                           config: Dict[str, Any],
                           constraints: 'SecurityConstraints'):
           """Start managing an agent"""
           managed_agent = ManagedAgent(agent_id, agent, config, constraints)
           self.managed_agents[agent_id] = managed_agent
           
           # Start agent in separate process with resource limits
           if constraints.max_memory_mb or constraints.max_cpu_percent:
               # Run in subprocess with resource limits
               managed_agent.process = await self._start_sandboxed_agent(
                   managed_agent
               )
               
           await self.event_emitter.emit(AGUIEvent(
               type=AGUIEventType.AGENT_STARTED,
               data={
                   "agent_id": str(agent_id),
                   "status": "active"
               }
           ))
           
       async def _start_sandboxed_agent(self, managed_agent: ManagedAgent):
           """Start agent in sandboxed subprocess"""
           # This would start a subprocess with resource limits
           # Using resource.setrlimit() for memory and CPU limits
           # Implementation depends on OS and containerization strategy
           pass
           
       async def pause_agent(self, agent_id: UUID):
           """Pause agent execution"""
           if agent_id in self.managed_agents:
               managed_agent = self.managed_agents[agent_id]
               managed_agent.status = AgentStatus.PAUSED
               
               # In real implementation, would pause the actual process
               
               await self.event_emitter.emit(AGUIEvent(
                   type=AGUIEventType.AGENT_STATUS_CHANGE,
                   data={
                       "agent_id": str(agent_id),
                       "status": "paused"
                   }
               ))
               
       async def resume_agent(self, agent_id: UUID):
           """Resume paused agent"""
           if agent_id in self.managed_agents:
               managed_agent = self.managed_agents[agent_id]
               if managed_agent.status == AgentStatus.PAUSED:
                   managed_agent.status = AgentStatus.ACTIVE
                   
                   await self.event_emitter.emit(AGUIEvent(
                       type=AGUIEventType.AGENT_STATUS_CHANGE,
                       data={
                           "agent_id": str(agent_id),
                           "status": "active"
                       }
                   ))
                   
       async def stop_agent(self, agent_id: UUID):
           """Stop and remove agent"""
           if agent_id in self.managed_agents:
               managed_agent = self.managed_agents[agent_id]
               managed_agent.status = AgentStatus.STOPPING
               
               # Stop process if running
               if managed_agent.process:
                   managed_agent.process.terminate()
                   await asyncio.sleep(2)
                   if managed_agent.process.poll() is None:
                       managed_agent.process.kill()
                       
               # Remove from managed agents
               del self.managed_agents[agent_id]
               
               await self.event_emitter.emit(AGUIEvent(
                   type=AGUIEventType.AGENT_DESTROYED,
                   data={
                       "agent_id": str(agent_id),
                       "final_metrics": {
                           "tasks_completed": managed_agent.metrics.tasks_completed,
                           "total_runtime": (
                               datetime.utcnow() - managed_agent.created_at
                           ).total_seconds()
                       }
                   }
               ))
               
       async def get_agent_status(self, agent_id: UUID) -> Optional[Dict[str, Any]]:
           """Get current agent status and metrics"""
           if agent_id not in self.managed_agents:
               return None
               
           managed_agent = self.managed_agents[agent_id]
           
           return {
               "agent_id": str(agent_id),
               "status": managed_agent.status.value,
               "created_at": managed_agent.created_at.isoformat(),
               "uptime_seconds": (
                   datetime.utcnow() - managed_agent.created_at
               ).total_seconds(),
               "metrics": {
                   "cpu_usage": managed_agent.metrics.cpu_usage,
                   "memory_mb": managed_agent.metrics.memory_usage_mb,
                   "tasks_completed": managed_agent.metrics.tasks_completed,
                   "tasks_failed": managed_agent.metrics.tasks_failed,
               },
               "config": managed_agent.config
           }
           
       async def list_agents(self, 
                           status_filter: Optional[AgentStatus] = None
                           ) -> List[Dict[str, Any]]:
           """List all managed agents"""
           agents = []
           
           for agent_id, managed_agent in self.managed_agents.items():
               if status_filter and managed_agent.status != status_filter:
                   continue
                   
               agents.append(await self.get_agent_status(agent_id))
               
           return [a for a in agents if a is not None]
   ```

2. **Create Agent Sandbox**
   ```python
   # src/shared/infrastructure/security/agent_sandbox.py
   import os
   import subprocess
   import resource
   import tempfile
   from typing import Dict, Any, Optional
   from pathlib import Path
   import docker
   
   class AgentSandbox:
       def __init__(self, use_docker: bool = True):
           self.use_docker = use_docker
           if use_docker:
               self.docker_client = docker.from_env()
               
       def create_sandbox_config(self, 
                               agent_id: str,
                               constraints: 'SecurityConstraints') -> Dict[str, Any]:
           """Create sandbox configuration"""
           if self.use_docker:
               return self._create_docker_config(agent_id, constraints)
           else:
               return self._create_process_config(agent_id, constraints)
               
       def _create_docker_config(self, 
                               agent_id: str,
                               constraints: 'SecurityConstraints') -> Dict[str, Any]:
           """Create Docker container configuration"""
           return {
               "image": "kolegium/agent-runtime:latest",
               "name": f"agent_{agent_id}",
               "detach": True,
               "mem_limit": f"{constraints.max_memory_mb}m",
               "nano_cpus": int(constraints.max_cpu_percent * 10**7),  # 1 CPU = 10^9 nano CPUs
               "network_mode": "bridge" if constraints.network_access else "none",
               "read_only": not constraints.file_system_access,
               "security_opt": ["no-new-privileges"],
               "ulimits": [
                   docker.types.Ulimit(name='nofile', soft=1024, hard=2048),
                   docker.types.Ulimit(name='nproc', soft=512, hard=1024),
               ],
               "environment": {
                   "AGENT_ID": agent_id,
                   "MAX_EXECUTION_TIME": str(constraints.max_execution_time_seconds),
               },
               "volumes": {
                   "/tmp/agent-workspace": {"bind": "/workspace", "mode": "rw"}
               } if constraints.file_system_access else {},
           }
           
       def _create_process_config(self,
                                agent_id: str,
                                constraints: 'SecurityConstraints') -> Dict[str, Any]:
           """Create subprocess configuration with resource limits"""
           
           def set_limits():
               # Set memory limit
               if constraints.max_memory_mb:
                   memory_bytes = constraints.max_memory_mb * 1024 * 1024
                   resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
                   
               # Set CPU time limit
               if constraints.max_execution_time_seconds:
                   resource.setrlimit(
                       resource.RLIMIT_CPU,
                       (constraints.max_execution_time_seconds, 
                        constraints.max_execution_time_seconds)
                   )
                   
               # Set file descriptor limit
               resource.setrlimit(resource.RLIMIT_NOFILE, (100, 100))
               
               # Drop privileges if running as root
               if os.getuid() == 0:
                   os.setuid(65534)  # nobody user
                   
           return {
               "preexec_fn": set_limits,
               "cwd": tempfile.mkdtemp(prefix=f"agent_{agent_id}_"),
               "env": {
                   **os.environ,
                   "AGENT_ID": agent_id,
                   "PYTHONPATH": "/app/src",
               }
           }
           
       async def run_agent_sandboxed(self,
                                   agent_id: str,
                                   agent_code: str,
                                   constraints: 'SecurityConstraints'):
           """Run agent in sandbox"""
           if self.use_docker:
               return await self._run_docker_agent(agent_id, agent_code, constraints)
           else:
               return await self._run_subprocess_agent(agent_id, agent_code, constraints)
               
       async def _run_docker_agent(self,
                                 agent_id: str,
                                 agent_code: str,
                                 constraints: 'SecurityConstraints'):
           """Run agent in Docker container"""
           config = self._create_docker_config(agent_id, constraints)
           
           # Create container
           container = self.docker_client.containers.create(**config)
           
           # Copy agent code to container
           with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
               f.write(agent_code)
               f.flush()
               
               # Copy file to container
               with open(f.name, 'rb') as code_file:
                   container.put_archive(
                       '/app',
                       self._create_tar_archive('agent.py', code_file.read())
                   )
                   
           # Start container
           container.start()
           
           return container
           
       async def _run_subprocess_agent(self,
                                     agent_id: str,
                                     agent_code: str,
                                     constraints: 'SecurityConstraints'):
           """Run agent in subprocess with limits"""
           config = self._create_process_config(agent_id, constraints)
           
           # Write agent code to temp file
           agent_dir = Path(config["cwd"])
           agent_file = agent_dir / "agent.py"
           agent_file.write_text(agent_code)
           
           # Start subprocess
           process = subprocess.Popen(
               ["python", str(agent_file)],
               **config,
               stdout=subprocess.PIPE,
               stderr=subprocess.PIPE
           )
           
           return process
           
       def _create_tar_archive(self, filename: str, content: bytes):
           """Create tar archive for Docker copy"""
           import tarfile
           import io
           
           tar_stream = io.BytesIO()
           tar = tarfile.open(fileobj=tar_stream, mode='w')
           
           tarinfo = tarfile.TarInfo(name=filename)
           tarinfo.size = len(content)
           tar.addfile(tarinfo, io.BytesIO(content))
           tar.close()
           
           tar_stream.seek(0)
           return tar_stream
   ```

3. **Create Auto-scaling Manager**
   ```python
   # src/shared/infrastructure/agents/autoscaling_manager.py
   from typing import Dict, List, Optional
   from uuid import UUID
   from datetime import datetime, timedelta
   from dataclasses import dataclass
   import statistics
   
   @dataclass
   class ScalingPolicy:
       min_agents: int = 1
       max_agents: int = 10
       scale_up_threshold: float = 80.0  # CPU or task queue %
       scale_down_threshold: float = 20.0
       cooldown_seconds: int = 300
       
   @dataclass
   class LoadMetrics:
       timestamp: datetime
       cpu_usage_avg: float
       memory_usage_avg: float
       pending_tasks: int
       active_agents: int
       
   class AutoScalingManager:
       def __init__(self, 
                    lifecycle_manager: 'AgentLifecycleManager',
                    agent_factory: 'AgentFactory'):
           self.lifecycle_manager = lifecycle_manager
           self.agent_factory = agent_factory
           self.scaling_policies: Dict[str, ScalingPolicy] = {}
           self.metrics_history: List[LoadMetrics] = []
           self.last_scale_action: Optional[datetime] = None
           
       def set_scaling_policy(self, agent_type: str, policy: ScalingPolicy):
           """Set scaling policy for agent type"""
           self.scaling_policies[agent_type] = policy
           
       async def evaluate_scaling(self) -> List[Dict[str, Any]]:
           """Evaluate if scaling is needed"""
           actions = []
           
           # Get current metrics
           current_metrics = await self._collect_metrics()
           self.metrics_history.append(current_metrics)
           
           # Keep only last hour of metrics
           cutoff = datetime.utcnow() - timedelta(hours=1)
           self.metrics_history = [
               m for m in self.metrics_history if m.timestamp > cutoff
           ]
           
           # Check cooldown
           if self.last_scale_action:
               cooldown_end = self.last_scale_action + timedelta(seconds=300)
               if datetime.utcnow() < cooldown_end:
                   return []  # Still in cooldown
                   
           # Evaluate each agent type
           for agent_type, policy in self.scaling_policies.items():
               action = await self._evaluate_agent_type(
                   agent_type, policy, current_metrics
               )
               if action:
                   actions.append(action)
                   
           return actions
           
       async def _collect_metrics(self) -> LoadMetrics:
           """Collect current system metrics"""
           agents = await self.lifecycle_manager.list_agents()
           
           if not agents:
               return LoadMetrics(
                   timestamp=datetime.utcnow(),
                   cpu_usage_avg=0.0,
                   memory_usage_avg=0.0,
                   pending_tasks=0,
                   active_agents=0
               )
               
           cpu_usages = [a["metrics"]["cpu_usage"] for a in agents]
           memory_usages = [a["metrics"]["memory_mb"] for a in agents]
           
           return LoadMetrics(
               timestamp=datetime.utcnow(),
               cpu_usage_avg=statistics.mean(cpu_usages) if cpu_usages else 0,
               memory_usage_avg=statistics.mean(memory_usages) if memory_usages else 0,
               pending_tasks=0,  # Would come from task queue
               active_agents=len(agents)
           )
           
       async def _evaluate_agent_type(self,
                                     agent_type: str,
                                     policy: ScalingPolicy,
                                     metrics: LoadMetrics) -> Optional[Dict[str, Any]]:
           """Evaluate scaling for specific agent type"""
           
           # Get agents of this type
           agents = await self.lifecycle_manager.list_agents()
           type_agents = [
               a for a in agents 
               if a["config"].get("role") == agent_type
           ]
           
           current_count = len(type_agents)
           
           # Calculate average load over last 5 minutes
           recent_metrics = [
               m for m in self.metrics_history
               if m.timestamp > datetime.utcnow() - timedelta(minutes=5)
           ]
           
           if not recent_metrics:
               return None
               
           avg_cpu = statistics.mean([m.cpu_usage_avg for m in recent_metrics])
           
           # Scale up decision
           if avg_cpu > policy.scale_up_threshold and current_count < policy.max_agents:
               return {
                   "action": "scale_up",
                   "agent_type": agent_type,
                   "current_count": current_count,
                   "target_count": min(current_count + 1, policy.max_agents),
                   "reason": f"CPU usage {avg_cpu:.1f}% exceeds threshold"
               }
               
           # Scale down decision
           if avg_cpu < policy.scale_down_threshold and current_count > policy.min_agents:
               return {
                   "action": "scale_down",
                   "agent_type": agent_type,
                   "current_count": current_count,
                   "target_count": max(current_count - 1, policy.min_agents),
                   "reason": f"CPU usage {avg_cpu:.1f}% below threshold"
               }
               
           return None
           
       async def execute_scaling_action(self, action: Dict[str, Any]):
           """Execute scaling decision"""
           if action["action"] == "scale_up":
               # Create new agent instance
               config = DynamicAgentConfig(
                   role=action["agent_type"],
                   goal=f"Auto-scaled {action['agent_type']} instance",
                   tools=["web_search"],  # Would be configured per type
               )
               
               await self.agent_factory.create_agent(config)
               
           elif action["action"] == "scale_down":
               # Find least busy agent of type
               agents = await self.lifecycle_manager.list_agents()
               type_agents = [
                   a for a in agents
                   if a["config"].get("role") == action["agent_type"]
               ]
               
               if type_agents:
                   # Sort by tasks completed (stop least productive)
                   type_agents.sort(key=lambda a: a["metrics"]["tasks_completed"])
                   await self.lifecycle_manager.stop_agent(UUID(type_agents[0]["agent_id"]))
                   
           self.last_scale_action = datetime.utcnow()
   ```

4. **API endpoints for management**
   ```python
   # src/interfaces/api/controllers/agent_management_controller.py
   from fastapi import APIRouter, HTTPException, Depends
   from typing import List, Optional
   from uuid import UUID
   
   from dependency_injector.wiring import inject, Provide
   
   from src.shared.infrastructure.agents.lifecycle_manager import (
       AgentLifecycleManager, AgentStatus
   )
   from src.shared.infrastructure.agents.autoscaling_manager import (
       AutoScalingManager, ScalingPolicy
   )
   from src.shared.infrastructure.container import Container
   
   router = APIRouter(prefix="/api/agents", tags=["agent-management"])
   
   router.get("/")
   @inject
   async def list_agents(
       status: Optional[str] = None,
       lifecycle_manager: AgentLifecycleManager = Provide[Container.lifecycle_manager]
   ):
       """List all agents with optional status filter"""
       status_filter = AgentStatus(status) if status else None
       agents = await lifecycle_manager.list_agents(status_filter)
       
       return {
           "count": len(agents),
           "agents": agents
       }
       
   router.get("/{agent_id}")
   @inject
   async def get_agent_status(
       agent_id: UUID,
       lifecycle_manager: AgentLifecycleManager = Provide[Container.lifecycle_manager]
   ):
       """Get specific agent status"""
       status = await lifecycle_manager.get_agent_status(agent_id)
       
       if not status:
           raise HTTPException(status_code=404, detail="Agent not found")
           
       return status
       
   router.post("/{agent_id}/pause")
   @inject
   async def pause_agent(
       agent_id: UUID,
       lifecycle_manager: AgentLifecycleManager = Provide[Container.lifecycle_manager]
   ):
       """Pause agent execution"""
       await lifecycle_manager.pause_agent(agent_id)
       return {"status": "paused", "agent_id": str(agent_id)}
       
   router.post("/{agent_id}/resume")
   @inject
   async def resume_agent(
       agent_id: UUID,
       lifecycle_manager: AgentLifecycleManager = Provide[Container.lifecycle_manager]
   ):
       """Resume paused agent"""
       await lifecycle_manager.resume_agent(agent_id)
       return {"status": "resumed", "agent_id": str(agent_id)}
       
   router.delete("/{agent_id}")
   @inject
   async def stop_agent(
       agent_id: UUID,
       lifecycle_manager: AgentLifecycleManager = Provide[Container.lifecycle_manager]
   ):
       """Stop and remove agent"""
       await lifecycle_manager.stop_agent(agent_id)
       return {"status": "stopped", "agent_id": str(agent_id)}
       
   router.get("/metrics/summary")
   @inject
   async def get_metrics_summary(
       lifecycle_manager: AgentLifecycleManager = Provide[Container.lifecycle_manager]
   ):
       """Get aggregated metrics for all agents"""
       agents = await lifecycle_manager.list_agents()
       
       if not agents:
           return {
               "total_agents": 0,
               "active_agents": 0,
               "total_tasks_completed": 0,
               "average_cpu_usage": 0,
               "average_memory_mb": 0
           }
           
       active_agents = [a for a in agents if a["status"] == "active"]
       
       return {
           "total_agents": len(agents),
           "active_agents": len(active_agents),
           "total_tasks_completed": sum(a["metrics"]["tasks_completed"] for a in agents),
           "average_cpu_usage": sum(a["metrics"]["cpu_usage"] for a in active_agents) / len(active_agents) if active_agents else 0,
           "average_memory_mb": sum(a["metrics"]["memory_mb"] for a in active_agents) / len(active_agents) if active_agents else 0,
           "by_status": {
               status: len([a for a in agents if a["status"] == status])
               for status in ["active", "paused", "stopped", "error"]
           }
       }
       
   router.post("/scaling/policy")
   @inject
   async def set_scaling_policy(
       agent_type: str,
       policy: ScalingPolicy,
       autoscaling_manager: AutoScalingManager = Provide[Container.autoscaling_manager]
   ):
       """Set auto-scaling policy for agent type"""
       autoscaling_manager.set_scaling_policy(agent_type, policy)
       return {"status": "policy_set", "agent_type": agent_type}
       
   router.post("/scaling/evaluate")
   @inject
   async def evaluate_scaling(
       autoscaling_manager: AutoScalingManager = Provide[Container.autoscaling_manager]
   ):
       """Manually trigger scaling evaluation"""
       actions = await autoscaling_manager.evaluate_scaling()
       
       return {
           "recommended_actions": actions,
           "count": len(actions)
       }
   ```

**Success Criteria**:
- [ ] Agent lifecycle management (start/stop/pause/resume)
- [ ] Resource monitoring with metrics collection
- [ ] Security constraints enforcement
- [ ] Sandboxed execution (Docker or process-based)
- [ ] Auto-scaling based on load
- [ ] Management API endpoints
- [ ] Integration tests for lifecycle operations

**Deploy Test**: Po ukończeniu tego bloku, deploy kompletny system dynamicznych agentów