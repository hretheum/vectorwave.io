# Example: Searching for Flow Patterns

This example demonstrates how to search for CrewAI flow patterns using the Knowledge Base integration.

## Basic Flow Pattern Search

```python
from ai_writing_flow.tools.enhanced_knowledge_tools import search_crewai_knowledge

# Search for agent patterns
result = search_crewai_knowledge(
    "CrewAI agent creation patterns role goal backstory",
    strategy="HYBRID",
    limit=5,
    score_threshold=0.7
)

print(result)
```

**Expected Output:**
```
# Knowledge Search Results
**Query:** CrewAI agent creation patterns role goal backstory
**Strategy used:** HYBRID
**Response time:** 245ms

## 📚 Knowledge Base Results

### 1. Agent Configuration Best Practices
*Relevance: 0.92*

Creating effective CrewAI agents requires careful consideration of:
- Role definition with clear responsibilities
- Specific, measurable goals
- Detailed backstory for context
- Appropriate tool selection

```python
agent = Agent(
    role="Senior Data Analyst",
    goal="Extract actionable insights from complex datasets",
    backstory="You are an experienced data analyst with 10+ years...",
    tools=[data_analysis_tool, visualization_tool]
)
```

### 2. Agent Role Design Patterns
*Relevance: 0.88*

Effective agent roles follow these patterns:
- Specific expertise areas
- Clear decision-making authority
- Defined interaction protocols
...
```

## Advanced Pattern Search

```python
# Search for specific workflow patterns
workflow_result = search_crewai_knowledge(
    "sequential task execution workflow dependencies",
    strategy="KB_FIRST",
    limit=3,
    score_threshold=0.8
)

# Search for error handling patterns
error_patterns = search_crewai_knowledge(
    "CrewAI error handling exception management retry logic",
    strategy="HYBRID",
    limit=5
)
```

## Using Flow Examples Tool

```python
from ai_writing_flow.tools.enhanced_knowledge_tools import get_flow_examples

# Get agent pattern examples
agent_examples = get_flow_examples("agent_patterns")

# Get task orchestration examples  
task_examples = get_flow_examples("task_orchestration")

# Get error handling examples
error_examples = get_flow_examples("error_handling")

print(agent_examples)
```

**Expected Output:**
```
# 🔧 Patterns for creating and configuring CrewAI agents

## 📚 Knowledge Base Results

### 1. Basic Agent Creation Pattern
*Relevance: 0.95*

```python
from crewai import Agent

def create_research_agent():
    return Agent(
        role="Research Specialist",
        goal="Conduct thorough research on specified topics",
        backstory="""You are an expert researcher with access to 
        comprehensive knowledge bases and analytical tools.""",
        tools=[search_tool, analysis_tool],
        verbose=True,
        allow_delegation=False
    )
```

### 2. Agent with Memory Configuration
*Relevance: 0.89*

```python
agent = Agent(
    role="Content Creator",
    goal="Generate high-quality content",
    memory=True,  # Enable memory
    max_iter=5,   # Limit iterations
    tools=[content_tool, review_tool]
)
```
```

## Pattern-Specific Searches

### 1. Memory Management Patterns

```python
memory_patterns = search_crewai_knowledge(
    "CrewAI memory management short term long term configuration",
    strategy="HYBRID"
)
```

### 2. Tool Integration Patterns

```python
tool_patterns = search_crewai_knowledge(
    "CrewAI custom tool integration @tool decorator patterns",
    strategy="KB_FIRST",
    score_threshold=0.75
)
```

### 3. Crew Configuration Patterns

```python
crew_patterns = search_crewai_knowledge(
    "CrewAI crew setup configuration verbose planning manager",
    strategy="HYBRID",
    limit=7
)
```

## Performance Optimization

```python
# For faster responses, use lower thresholds
quick_search = search_crewai_knowledge(
    "agent patterns",
    strategy="FILE_FIRST",  # Faster strategy
    limit=3,                # Fewer results
    score_threshold=0.5     # Lower threshold
)

# For comprehensive results, use higher thresholds
comprehensive_search = search_crewai_knowledge(
    "complex multi-agent workflow orchestration",
    strategy="KB_FIRST",    # More thorough
    limit=10,               # More results
    score_threshold=0.8     # Higher quality
)
```

## Error Handling

```python
try:
    result = search_crewai_knowledge(
        "flow patterns",
        strategy="HYBRID"
    )
except Exception as e:
    print(f"Search failed: {e}")
    # Fallback to simpler search
    result = search_crewai_knowledge(
        "flow patterns",
        strategy="FILE_FIRST"
    )
```

## Real-World Usage in Crews

```python
from crewai import Agent, Task, Crew
from ai_writing_flow.tools.enhanced_knowledge_tools import search_crewai_knowledge

# Agent that uses KB for self-improvement
class KnowledgeEnhancedAgent(Agent):
    def research_best_practices(self, topic: str):
        """Research best practices for a topic"""
        return search_crewai_knowledge(
            f"CrewAI {topic} best practices patterns",
            strategy="HYBRID",
            limit=5
        )
    
    def get_examples(self, pattern_type: str):
        """Get specific pattern examples"""
        return get_flow_examples(pattern_type)

# Usage in task
def create_enhanced_research_task():
    return Task(
        description="""
        Research CrewAI best practices and create implementation guide.
        Use search_crewai_knowledge to find relevant patterns and examples.
        """,
        agent=research_agent,
        tools=[search_crewai_knowledge, get_flow_examples]
    )
```

## Tips for Effective Searches

1. **Use specific keywords**: Include "CrewAI" and specific concepts
2. **Combine terms**: Mix technical terms with use cases
3. **Try different strategies**: HYBRID for general, KB_FIRST for complex queries
4. **Adjust thresholds**: Lower for broader results, higher for precision
5. **Use pattern tools**: `get_flow_examples()` for structured patterns

## Common Search Patterns

```python
# Installation and setup
search_crewai_knowledge("CrewAI installation requirements setup")

# Configuration
search_crewai_knowledge("CrewAI configuration yaml agents tasks")

# Troubleshooting
search_crewai_knowledge("CrewAI common issues errors debugging")

# Performance
search_crewai_knowledge("CrewAI performance optimization speed")

# Advanced features
search_crewai_knowledge("CrewAI advanced features memory planning")
```