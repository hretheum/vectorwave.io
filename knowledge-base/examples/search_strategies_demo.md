# Example: Using Different Search Strategies

This example demonstrates the different search strategies available in the Knowledge Base and when to use each one.

## Overview of Search Strategies

The Knowledge Base supports 4 distinct search strategies:

1. **HYBRID** - Intelligent combination of all sources (Recommended)
2. **KB_FIRST** - Prioritize Knowledge Base with file enhancement  
3. **FILE_FIRST** - Fast local search with KB enhancement
4. **KB_ONLY** - Pure vector search without fallback

## Strategy Comparison Demo

```python
from ai_writing_flow.tools.enhanced_knowledge_tools import search_crewai_knowledge
import time

def compare_search_strategies(query: str):
    """Compare all search strategies for the same query"""
    
    strategies = ["HYBRID", "KB_FIRST", "FILE_FIRST", "KB_ONLY"]
    results = {}
    
    for strategy in strategies:
        start_time = time.time()
        
        try:
            result = search_crewai_knowledge(
                query=query,
                strategy=strategy,
                limit=3,
                score_threshold=0.6
            )
            
            response_time = (time.time() - start_time) * 1000
            results[strategy] = {
                "result": result,
                "response_time_ms": response_time,
                "success": True
            }
            
        except Exception as e:
            results[strategy] = {
                "error": str(e),
                "response_time_ms": (time.time() - start_time) * 1000,
                "success": False
            }
    
    return results

# Test with a complex query
query = "CrewAI agent memory configuration and troubleshooting"
comparison = compare_search_strategies(query)

for strategy, result in comparison.items():
    print(f"\n=== {strategy} Strategy ===")
    print(f"Response Time: {result['response_time_ms']:.0f}ms")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Content Preview: {result['result'][:200]}...")
```

**Expected Output:**
```
=== HYBRID Strategy ===
Response Time: 245ms
Success: True
Content Preview: # Knowledge Search Results
**Query:** CrewAI agent memory configuration and troubleshooting
**Strategy used:** HYBRID
**Response time:** 245ms

## 📚 Knowledge Base Results

### 1. Agent Memory Configuration Guide
*Relevance: 0.94*

CrewAI agents support both short-term and long-term memory:

```python
agent = Agent(
    role="Research Assistant",
    memory=True,  # Enable memory
    max_memory_items=1000
)
```

=== KB_FIRST Strategy ===
Response Time: 312ms
Success: True
Content Preview: # Knowledge Search Results
**Query:** CrewAI agent memory configuration and troubleshooting
**Strategy used:** KB_FIRST
**Response time:** 312ms

## 📚 Knowledge Base Results

### 1. Memory System Architecture
*Relevance: 0.91*

The CrewAI memory system consists of:
- Short-term memory for task context
- Long-term memory for learning...

=== FILE_FIRST Strategy ===
Response Time: 89ms
Success: True
Content Preview: # Knowledge Search Results
**Query:** CrewAI agent memory configuration and troubleshooting
**Strategy used:** FILE_FIRST
**Response time:** 89ms

## 📖 Local Documentation

Memory configuration in CrewAI:

```python
# Basic memory setup
agent = Agent(role="Assistant", memory=True)
```

=== KB_ONLY Strategy ===
Response Time: 156ms
Success: True
Content Preview: # Knowledge Search Results
**Query:** CrewAI agent memory configuration and troubleshooting
**Strategy used:** KB_ONLY
**Response time:** 156ms

## 📚 Knowledge Base Results

### 1. Advanced Memory Patterns
*Relevance: 0.88*

Semantic search found related concepts:
- Memory persistence strategies
- Context window management...
```

## Strategy-Specific Use Cases

### 1. HYBRID Strategy - General Purpose (Recommended)

**Best for**: Most queries, balanced performance and coverage

```python
# General CrewAI questions
general_help = search_crewai_knowledge(
    "How to set up CrewAI agents with custom tools",
    strategy="HYBRID"
)

# Complex conceptual queries
concept_help = search_crewai_knowledge(
    "CrewAI flow control patterns and best practices",
    strategy="HYBRID",
    limit=7,
    score_threshold=0.6
)

# Troubleshooting questions
troubleshoot_help = search_crewai_knowledge(
    "CrewAI memory issues debugging steps",
    strategy="HYBRID"
)
```

**Advantages:**
- Best overall coverage
- Intelligent fallback
- Good performance
- Handles KB outages gracefully

**When to use:**
- Default choice for most searches
- When you need comprehensive results
- When KB availability is uncertain
- For production applications

### 2. KB_FIRST Strategy - Semantic Search Priority

**Best for**: Complex conceptual queries, discovery, research

```python
# Complex conceptual searches
concepts = search_crewai_knowledge(
    "design patterns for multi-agent collaboration in complex workflows",
    strategy="KB_FIRST",
    score_threshold=0.7
)

# Research and discovery
discovery = search_crewai_knowledge(
    "emerging patterns in agent orchestration and task dependencies",
    strategy="KB_FIRST",
    limit=10
)

# Deep technical questions
technical = search_crewai_knowledge(
    "advanced memory persistence strategies and performance optimization",
    strategy="KB_FIRST"
)
```

**Advantages:**
- Best semantic understanding
- Finds related concepts
- Comprehensive knowledge coverage
- Good for exploration

**When to use:**
- Research and discovery tasks
- Complex conceptual questions
- When you need semantic similarity
- For comprehensive analysis

**Trade-offs:**
- Slower response time
- Requires KB to be available
- May return broader results

### 3. FILE_FIRST Strategy - Fast Local Search

**Best for**: Quick lookups, references, simple queries

```python
# Quick reference lookups
quick_ref = search_crewai_knowledge(
    "CrewAI installation steps",
    strategy="FILE_FIRST"
)

# Simple how-to questions
howto = search_crewai_knowledge(
    "create CrewAI agent with tools",
    strategy="FILE_FIRST",
    limit=3
)

# Basic syntax questions
syntax = search_crewai_knowledge(
    "CrewAI task definition syntax",
    strategy="FILE_FIRST"
)

# Development workflow
workflow = search_crewai_knowledge(
    "CrewAI development setup requirements",
    strategy="FILE_FIRST"
)
```

**Advantages:**
- Fastest response time
- Works offline
- Reliable local content
- Good for simple queries

**When to use:**
- Quick reference needs
- Simple how-to questions
- Development environments
- When speed is critical
- Offline/unstable connections

**Trade-offs:**
- Limited semantic understanding
- May miss related concepts
- Depends on local file quality

### 4. KB_ONLY Strategy - Pure Semantic Search

**Best for**: Exploratory search, finding similar concepts

```python
# Exploratory searches
explore = search_crewai_knowledge(
    "concepts similar to agent memory",
    strategy="KB_ONLY",
    limit=10,
    score_threshold=0.5
)

# Find related patterns
patterns = search_crewai_knowledge(
    "patterns related to task orchestration",
    strategy="KB_ONLY"
)

# Research similar concepts
similar = search_crewai_knowledge(
    "alternatives to @router decorator",
    strategy="KB_ONLY",
    score_threshold=0.6
)
```

**Advantages:**
- Pure semantic search
- Fastest when KB is healthy
- Finds unexpected connections
- Good similarity detection

**When to use:**
- Exploratory research
- Finding similar concepts
- When KB is known to be healthy
- For creative problem solving

**Trade-offs:**
- No fallback if KB fails
- May miss exact matches in files
- Requires KB to be available

## Performance Optimization by Strategy

### Response Time Optimization

```python
def optimized_search_by_urgency(query: str, urgency: str = "normal"):
    """Optimize search strategy based on urgency"""
    
    if urgency == "urgent":
        # Fastest response
        return search_crewai_knowledge(
            query,
            strategy="FILE_FIRST",
            limit=3,
            score_threshold=0.5
        )
    
    elif urgency == "thorough":
        # Most comprehensive
        return search_crewai_knowledge(
            query,
            strategy="KB_FIRST",
            limit=10,
            score_threshold=0.7
        )
    
    else:  # normal
        # Balanced approach
        return search_crewai_knowledge(
            query,
            strategy="HYBRID",
            limit=5,
            score_threshold=0.6
        )

# Usage examples
urgent_help = optimized_search_by_urgency(
    "CrewAI syntax error fix",
    urgency="urgent"
)

thorough_research = optimized_search_by_urgency(
    "advanced agent collaboration patterns",
    urgency="thorough"
)
```

### Adaptive Strategy Selection

```python
def adaptive_search(query: str, context: dict = None):
    """Automatically select best strategy based on query and context"""
    
    # Analyze query characteristics
    query_words = query.lower().split()
    
    # Simple/direct queries -> FILE_FIRST
    simple_keywords = ["install", "setup", "syntax", "example", "how to"]
    if any(keyword in query.lower() for keyword in simple_keywords):
        return search_crewai_knowledge(query, strategy="FILE_FIRST")
    
    # Complex/conceptual queries -> KB_FIRST
    complex_keywords = ["pattern", "design", "architecture", "best practice", "optimize"]
    if any(keyword in query.lower() for keyword in complex_keywords):
        return search_crewai_knowledge(query, strategy="KB_FIRST")
    
    # Exploratory queries -> KB_ONLY
    explore_keywords = ["similar", "alternative", "related", "like"]
    if any(keyword in query.lower() for keyword in explore_keywords):
        return search_crewai_knowledge(query, strategy="KB_ONLY")
    
    # Default to HYBRID
    return search_crewai_knowledge(query, strategy="HYBRID")

# Examples
result1 = adaptive_search("how to install CrewAI")  # Uses FILE_FIRST
result2 = adaptive_search("design patterns for agent collaboration")  # Uses KB_FIRST  
result3 = adaptive_search("alternatives to router decorator")  # Uses KB_ONLY
result4 = adaptive_search("memory configuration help")  # Uses HYBRID
```

## Error Handling by Strategy

### Strategy-Specific Error Handling

```python
def robust_search_with_fallback(query: str, preferred_strategy: str = "HYBRID"):
    """Search with intelligent fallback between strategies"""
    
    strategies = ["HYBRID", "KB_FIRST", "FILE_FIRST", "KB_ONLY"]
    
    # Start with preferred strategy
    if preferred_strategy in strategies:
        strategies.remove(preferred_strategy)
        strategies.insert(0, preferred_strategy)
    
    for strategy in strategies:
        try:
            result = search_crewai_knowledge(
                query,
                strategy=strategy,
                limit=5
            )
            
            print(f"✅ Success with {strategy} strategy")
            return result
            
        except Exception as e:
            print(f"❌ {strategy} failed: {str(e)}")
            continue
    
    return "❌ All search strategies failed. Please check system health."

# Usage
result = robust_search_with_fallback(
    "CrewAI configuration guide",
    preferred_strategy="KB_FIRST"
)
```

### Strategy Health Monitoring

```python
def monitor_strategy_health():
    """Monitor health of different search strategies"""
    
    test_query = "CrewAI basic setup"
    strategies = ["HYBRID", "KB_FIRST", "FILE_FIRST", "KB_ONLY"]
    
    health_report = {}
    
    for strategy in strategies:
        start_time = time.time()
        
        try:
            result = search_crewai_knowledge(
                test_query,
                strategy=strategy,
                limit=1
            )
            
            response_time = (time.time() - start_time) * 1000
            
            health_report[strategy] = {
                "status": "healthy",
                "response_time_ms": response_time,
                "has_results": len(result) > 100  # Basic content check
            }
            
        except Exception as e:
            health_report[strategy] = {
                "status": "unhealthy", 
                "error": str(e),
                "response_time_ms": (time.time() - start_time) * 1000
            }
    
    return health_report

# Run health check
health = monitor_strategy_health()
for strategy, status in health.items():
    print(f"{strategy}: {status['status']} ({status.get('response_time_ms', 0):.0f}ms)")
```

## Advanced Strategy Combinations

### Sequential Strategy Execution

```python
def sequential_search(query: str, strategies: list = None):
    """Execute multiple strategies in sequence and combine results"""
    
    if not strategies:
        strategies = ["FILE_FIRST", "KB_FIRST"]  # Fast then thorough
    
    all_results = []
    
    for strategy in strategies:
        try:
            result = search_crewai_knowledge(
                query,
                strategy=strategy,
                limit=3
            )
            
            all_results.append({
                "strategy": strategy,
                "result": result
            })
            
        except Exception as e:
            print(f"Strategy {strategy} failed: {e}")
    
    # Combine results
    combined = f"# Combined Search Results for: {query}\n\n"
    
    for item in all_results:
        combined += f"## Results from {item['strategy']} Strategy\n\n"
        combined += item['result']
        combined += "\n\n---\n\n"
    
    return combined

# Usage
comprehensive_results = sequential_search(
    "CrewAI performance optimization",
    strategies=["FILE_FIRST", "KB_FIRST", "KB_ONLY"]
)
```

### Parallel Strategy Execution

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def parallel_search(query: str, strategies: list = None):
    """Execute multiple strategies in parallel"""
    
    if not strategies:
        strategies = ["HYBRID", "KB_FIRST", "FILE_FIRST"]
    
    def run_search(strategy):
        return search_crewai_knowledge(
            query,
            strategy=strategy,
            limit=3
        )
    
    # Execute in parallel
    with ThreadPoolExecutor(max_workers=len(strategies)) as executor:
        futures = {
            executor.submit(run_search, strategy): strategy 
            for strategy in strategies
        }
        
        results = {}
        for future in futures:
            strategy = futures[future]
            try:
                result = future.result(timeout=30)  # 30 second timeout
                results[strategy] = result
            except Exception as e:
                results[strategy] = f"Error: {str(e)}"
    
    return results

# Usage (requires async context)
# parallel_results = await parallel_search("CrewAI troubleshooting")
```

This comprehensive example demonstrates how to effectively use different search strategies based on your specific needs, performance requirements, and system conditions.