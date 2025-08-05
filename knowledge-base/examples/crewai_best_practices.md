# Example: Getting CrewAI Best Practices

This example demonstrates how to retrieve and apply CrewAI best practices using the Knowledge Base integration.

## Basic Best Practices Search

```python
from ai_writing_flow.tools.enhanced_knowledge_tools import (
    search_crewai_knowledge,
    get_flow_examples
)

# Search for general best practices
best_practices = search_crewai_knowledge(
    "CrewAI best practices recommendations guidelines",
    strategy="HYBRID",
    limit=10,
    score_threshold=0.7
)

print(best_practices)
```

**Expected Output:**
```
# Knowledge Search Results
**Query:** CrewAI best practices recommendations guidelines
**Strategy used:** HYBRID
**Response time:** 198ms

## 📚 Knowledge Base Results

### 1. Agent Design Best Practices
*Relevance: 0.94*

**Key Principles:**
1. **Clear Role Definition**: Each agent should have a specific, well-defined role
2. **Appropriate Tool Selection**: Match tools to agent capabilities
3. **Backstory Depth**: Provide rich context for better decision-making
4. **Goal Specificity**: Set measurable, achievable goals

```python
# Good agent design
agent = Agent(
    role="Senior Data Analyst",
    goal="Extract actionable insights from quarterly sales data",
    backstory="""You have 10+ years of experience in retail analytics,
    specializing in sales trend analysis and market forecasting.""",
    tools=[data_analysis_tool, visualization_tool],
    verbose=True,
    allow_delegation=False
)
```

### 2. Task Orchestration Best Practices
*Relevance: 0.91*

**Effective Task Design:**
- Break complex work into atomic tasks
- Define clear dependencies
- Set realistic expectations
- Include success criteria

```python
# Well-structured task
task = Task(
    description="""
    Analyze Q3 sales data to identify:
    1. Top performing products
    2. Regional sales variations
    3. Customer segment insights
    
    Provide specific recommendations for Q4 strategy.
    """,
    agent=data_analyst,
    expected_output="Executive summary with 3-5 key recommendations",
    tools=[analysis_tool]
)
```
```

## Specific Best Practice Categories

### 1. Memory Management Best Practices

```python
# Search for memory configuration guidance
memory_practices = search_crewai_knowledge(
    "CrewAI memory management best practices short term long term",
    strategy="KB_FIRST",
    score_threshold=0.8
)

print(memory_practices)
```

**Example Response:**
```
### Memory Configuration Best Practices

**Short-term Memory:**
- Use for task-specific context
- Automatically managed per execution
- Good for conversation continuity

**Long-term Memory:**
- Enable for learning across sessions
- Configure appropriate storage backend
- Monitor storage growth

```python
# Recommended memory setup
agent = Agent(
    role="Research Assistant",
    memory=True,  # Enable both short and long-term
    max_memory_items=1000,  # Limit growth
    memory_storage="redis://localhost:6379"  # Persistent storage
)
```
```

### 2. Performance Optimization Best Practices

```python
# Get performance optimization examples
performance_practices = get_flow_examples("performance_optimization")

# Search for specific optimization techniques
optimization_tips = search_crewai_knowledge(
    "CrewAI performance optimization speed memory CPU usage",
    strategy="HYBRID",
    limit=7
)
```

### 3. Error Handling Best Practices

```python
# Get error handling patterns
error_practices = get_flow_examples("error_handling")

# Search for specific error scenarios
error_tips = search_crewai_knowledge(
    "CrewAI error handling exception management retry logic",
    strategy="KB_FIRST"
)
```

## Comprehensive Best Practices Implementation

### 1. Agent Design Template

```python
from crewai import Agent
from typing import List, Optional

class BestPracticeAgent(Agent):
    """Agent following CrewAI best practices"""
    
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: List,
        verbose: bool = True,
        allow_delegation: bool = False,
        max_iter: int = 15,
        memory: bool = True
    ):
        # Validate inputs according to best practices
        self._validate_role(role)
        self._validate_goal(goal)
        self._validate_backstory(backstory)
        
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            verbose=verbose,
            allow_delegation=allow_delegation,
            max_iter=max_iter,
            memory=memory
        )
    
    def _validate_role(self, role: str):
        """Validate role follows best practices"""
        if len(role.split()) < 2:
            raise ValueError("Role should be descriptive (e.g., 'Senior Data Analyst')")
        
        if role.lower() in ["agent", "assistant", "helper"]:
            raise ValueError("Role should be specific, not generic")
    
    def _validate_goal(self, goal: str):
        """Validate goal is specific and measurable"""
        if len(goal.split()) < 5:
            raise ValueError("Goal should be detailed and specific")
        
        action_words = ["analyze", "create", "generate", "review", "research"]
        if not any(word in goal.lower() for word in action_words):
            raise ValueError("Goal should contain clear action verbs")
    
    def _validate_backstory(self, backstory: str):
        """Validate backstory provides sufficient context"""
        if len(backstory.split()) < 10:
            raise ValueError("Backstory should be detailed (minimum 10 words)")

# Example usage
research_agent = BestPracticeAgent(
    role="Senior Research Analyst",
    goal="Conduct comprehensive market research and provide strategic insights",
    backstory="""You are a seasoned research analyst with 15 years of experience 
    in market analysis, competitive intelligence, and strategic planning. You excel 
    at finding patterns in complex data and translating findings into actionable 
    business recommendations.""",
    tools=[search_tool, analysis_tool, report_tool]
)
```

### 2. Task Design Template

```python
from crewai import Task
from typing import Optional

class BestPracticeTask(Task):
    """Task following CrewAI best practices"""
    
    def __init__(
        self,
        description: str,
        agent: Agent,
        expected_output: str,
        tools: Optional[List] = None,
        context: Optional[List] = None,
        output_file: Optional[str] = None
    ):
        # Validate inputs
        self._validate_description(description)
        self._validate_expected_output(expected_output)
        
        super().__init__(
            description=description,
            agent=agent,
            expected_output=expected_output,
            tools=tools,
            context=context,
            output_file=output_file
        )
    
    def _validate_description(self, description: str):
        """Validate task description is clear and actionable"""
        if len(description.split()) < 10:
            raise ValueError("Task description should be detailed")
        
        if not any(char in description for char in ['.', ':', '\n']):
            raise ValueError("Task description should be well-structured")
    
    def _validate_expected_output(self, expected_output: str):
        """Validate expected output is specific"""
        if len(expected_output.split()) < 5:
            raise ValueError("Expected output should be specific")

# Example usage
analysis_task = BestPracticeTask(
    description="""
    Analyze the competitive landscape for our target market:
    
    1. Identify top 5 competitors
    2. Analyze their pricing strategies
    3. Evaluate their market positioning
    4. Assess their strengths and weaknesses
    5. Provide strategic recommendations
    
    Use provided market data and conduct additional research as needed.
    """,
    agent=research_agent,
    expected_output="""
    A comprehensive competitive analysis report including:
    - Executive summary (1 page)
    - Detailed competitor profiles (2-3 pages)
    - Strategic recommendations (1 page)
    - Supporting data and charts
    """,
    tools=[research_tool, analysis_tool]
)
```

### 3. Crew Configuration Best Practices

```python
from crewai import Crew
from typing import List

class BestPracticeCrew(Crew):
    """Crew following CrewAI best practices"""
    
    def __init__(
        self,
        agents: List[Agent],
        tasks: List[Task],
        verbose: bool = True,
        memory: bool = True,
        planning: bool = False,
        max_rpm: Optional[int] = None
    ):
        # Validate crew composition
        self._validate_agents(agents)
        self._validate_tasks(tasks)
        self._validate_agent_task_alignment(agents, tasks)
        
        super().__init__(
            agents=agents,
            tasks=tasks,
            verbose=verbose,
            memory=memory,
            planning=planning,
            max_rpm=max_rpm
        )
    
    def _validate_agents(self, agents: List[Agent]):
        """Validate agent configuration"""
        if len(agents) < 1:
            raise ValueError("Crew must have at least one agent")
        
        if len(agents) > 10:
            raise ValueError("Large crews (>10 agents) may have coordination issues")
        
        # Check for role uniqueness
        roles = [agent.role for agent in agents]
        if len(roles) != len(set(roles)):
            raise ValueError("Agents should have unique roles")
    
    def _validate_tasks(self, tasks: List[Task]):
        """Validate task configuration"""
        if len(tasks) < 1:
            raise ValueError("Crew must have at least one task")
        
        if len(tasks) > len(agents) * 3:
            raise ValueError("Too many tasks per agent may cause inefficiency")
    
    def _validate_agent_task_alignment(self, agents: List[Agent], tasks: List[Task]):
        """Validate agents are appropriately assigned to tasks"""
        agent_skills = {agent.role: agent.tools for agent in agents}
        
        for task in tasks:
            if task.agent.role not in agent_skills:
                raise ValueError(f"Task assigned to undefined agent: {task.agent.role}")

# Example usage
best_practice_crew = BestPracticeCrew(
    agents=[research_agent, analyst_agent, writer_agent],
    tasks=[research_task, analysis_task, writing_task],
    verbose=True,
    memory=True,
    planning=False  # Enable only for complex workflows
)
```

## Tool Integration Best Practices

```python
# Search for tool integration guidance
tool_practices = search_crewai_knowledge(
    "CrewAI tool integration custom tools @tool decorator best practices",
    strategy="HYBRID",
    limit=5
)

# Get tool integration examples
tool_examples = get_flow_examples("tool_integration")
```

### Custom Tool Best Practices

```python
from crewai_tools import tool
from typing import Dict, Any
import structlog

logger = structlog.get_logger()

@tool("research_market_data")
def research_market_data(query: str, market: str = "global") -> str:
    """
    Research market data for specified query and market.
    
    This tool follows CrewAI best practices:
    - Clear docstring with purpose
    - Type hints for parameters
    - Error handling with logging
    - Structured output format
    
    Args:
        query: Specific research query
        market: Target market (default: "global")
        
    Returns:
        Formatted research results
    """
    try:
        logger.info("Market research requested", query=query, market=market)
        
        # Tool implementation
        results = perform_market_research(query, market)
        
        # Format results consistently
        formatted_results = format_research_results(results)
        
        logger.info("Market research completed", 
                   query=query, 
                   results_count=len(results))
        
        return formatted_results
        
    except Exception as e:
        logger.error("Market research failed", 
                    query=query, 
                    error=str(e))
        return f"Research failed: {str(e)}"

def format_research_results(results: List[Dict[str, Any]]) -> str:
    """Format research results consistently"""
    
    if not results:
        return "No results found for the specified query."
    
    formatted = "# Market Research Results\n\n"
    
    for i, result in enumerate(results[:5], 1):
        formatted += f"## {i}. {result.get('title', 'Untitled')}\n"
        formatted += f"**Source:** {result.get('source', 'Unknown')}\n"
        formatted += f"**Date:** {result.get('date', 'Unknown')}\n"
        formatted += f"\n{result.get('summary', 'No summary available')}\n\n"
    
    return formatted
```

## Monitoring and Observability Best Practices

```python
# Search for monitoring guidance
monitoring_practices = search_crewai_knowledge(
    "CrewAI monitoring observability logging metrics performance",
    strategy="KB_FIRST"
)

# Implementation example
import structlog
import time
from contextlib import contextmanager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@contextmanager
def crew_execution_monitoring(crew_name: str):
    """Monitor crew execution with comprehensive logging"""
    start_time = time.time()
    
    logger.info("Crew execution started", 
               crew_name=crew_name,
               start_time=start_time)
    
    try:
        yield
        
        execution_time = time.time() - start_time
        logger.info("Crew execution completed successfully",
                   crew_name=crew_name,
                   execution_time=execution_time)
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error("Crew execution failed",
                    crew_name=crew_name,
                    execution_time=execution_time,
                    error=str(e))
        raise
    
    finally:
        logger.info("Crew execution finished",
                   crew_name=crew_name,
                   total_time=time.time() - start_time)

# Usage
def run_monitored_crew():
    with crew_execution_monitoring("ContentCreationCrew"):
        crew = ContentCreationCrew()
        return crew.kickoff()
```

## Testing Best Practices

```python
# Search for testing guidance
testing_practices = search_crewai_knowledge(
    "CrewAI testing unit tests integration tests best practices",
    strategy="HYBRID"
)

# Implementation example
import pytest
from unittest.mock import Mock, patch

class TestCrewAIBestPractices:
    """Test suite following CrewAI testing best practices"""
    
    def test_agent_creation(self):
        """Test agent follows best practices"""
        agent = BestPracticeAgent(
            role="Test Data Analyst",
            goal="Analyze test data and provide insights",
            backstory="You are an experienced test analyst with expertise in data validation",
            tools=[mock_analysis_tool]
        )
        
        assert agent.role == "Test Data Analyst"
        assert len(agent.backstory.split()) >= 10
        assert agent.memory is True
    
    def test_task_validation(self):
        """Test task creation validation"""
        with pytest.raises(ValueError):
            BestPracticeTask(
                description="Too short",  # Should fail validation
                agent=test_agent,
                expected_output="Brief output"
            )
    
    def test_crew_execution_timeout(self):
        """Test crew execution doesn't hang"""
        crew = BestPracticeCrew(
            agents=[test_agent],
            tasks=[test_task]
        )
        
        # Execute with timeout
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Crew execution timeout")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(60)  # 60 second timeout
        
        try:
            result = crew.kickoff()
            assert result is not None
        except TimeoutError:
            pytest.fail("Crew execution timed out")
        finally:
            signal.alarm(0)
    
    def test_tool_error_handling(self):
        """Test tool error handling"""
        with patch('research_market_data') as mock_tool:
            mock_tool.side_effect = Exception("API Error")
            
            result = research_market_data("test query")
            assert "Research failed" in result
```

## Performance Optimization Best Practices

```python
# Get performance optimization guidance
performance_tips = search_crewai_knowledge(
    "CrewAI performance optimization memory CPU utilization speed",
    strategy="KB_FIRST",
    limit=8
)

# Implementation examples based on best practices
class OptimizedCrewConfig:
    """Optimized crew configuration following best practices"""
    
    @staticmethod
    def create_lightweight_agent(role: str, goal: str, backstory: str, tools: List):
        """Create performance-optimized agent"""
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            verbose=False,  # Reduce logging overhead
            max_iter=10,    # Limit iterations
            memory=False    # Disable memory for simple tasks
        )
    
    @staticmethod
    def create_batch_processing_crew(agents: List[Agent], tasks: List[Task]):
        """Create crew optimized for batch processing"""
        return Crew(
            agents=agents,
            tasks=tasks,
            verbose=False,    # Reduce logging
            memory=False,     # Disable shared memory
            planning=False,   # Disable planning overhead
            max_rpm=120       # Increase rate limit
        )
```

This comprehensive example demonstrates how to use the Knowledge Base to find and implement CrewAI best practices across all aspects of the framework - from agent design to performance optimization.