

---

## 🚨 DEPRECATED NOTICE (2025-08-08)

**This developer guide has been DEPRECATED and replaced.**

**Reason**: Contains mixed architecture patterns and outdated approaches  
**Replacement**: `docs/developer/ONBOARDING_GUIDE.md` - Target architecture focused  
**Status**: Historical reference only - DO NOT FOLLOW

**Key Issues with This Guide**:
- Mixed @router/@listen examples (causes infinite loops)
- References to hardcoded rules as acceptable solutions
- Outdated port allocations and service configurations
- Missing container-first development patterns

**Current Developer Resources**:
- `docs/developer/ONBOARDING_GUIDE.md` - Complete onboarding guide
- `target-version/` - Single source of truth for architecture
- `docs/integration/` - Production system integration patterns

---
# Vector Wave AI Kolegium - Developer Guide

## 🚀 Quick Start for New Developers

**Time to productive development**: <1 minute with automated setup

### Prerequisites

- Docker and Docker Compose
- Git
- Python 3.11+ (optional, runs in containers)

### One-Command Setup

```bash
# Clone and setup everything
git clone --recurse-submodules https://github.com/hretheum/vectorwave.io.git
cd vectorwave.io/kolegium
make dev-setup
```

That's it! The system is now running with:
- ✅ API Server: http://localhost:8003
- ✅ Health Dashboard: http://localhost:8083  
- ✅ API Documentation: http://localhost:8003/docs
- ✅ System Health: http://localhost:8003/health

## 🏗️ Understanding the Architecture

### Linear Flow Pattern (No Infinite Loops)

```python
# OLD: @router/@listen patterns (caused infinite loops)
@router(condition="content_type == 'TECHNICAL'")
def technical_route(state):
    return technical_flow(state)  # Could loop forever

# NEW: Linear Flow (guaranteed to complete)
class LinearExecutionChain:
    def execute(self, inputs):
        state = WritingFlowState(inputs)
        
        # Sequential execution with guards
        state = self.research_stage.execute(state)
        state = self.audience_stage.execute(state) 
        state = self.writer_stage.execute(state)
        state = self.style_stage.execute(state)
        state = self.quality_stage.execute(state)
        
        return state.final_output
```

**Why Linear Flow?**
- ✅ **Predictable execution time**: Always completes in <30s
- ✅ **Zero infinite loops**: Sequential stages prevent loops
- ✅ **Easy debugging**: Clear execution path
- ✅ **Performance optimization**: Each stage can be optimized independently

### The 5 Core AI Agents

```python
# 1. Research Agent - Deep content research
class ResearchCrew:
    def kickoff(self, inputs):
        if inputs.content_ownership == "ORIGINAL":
            return self.skip_research()  # 20% faster for original content
        return self.deep_research(inputs.topic_title)

# 2. Audience Agent - Platform optimization  
class AudienceCrew:
    def kickoff(self, research_result):
        return self.optimize_for_platform(research_result, platform="LinkedIn")

# 3. Writer Agent - Content generation
class WriterCrew:
    def kickoff(self, audience_result):
        return self.generate_draft(audience_result)

# 4. Style Agent - TRUE Agentic RAG
class StyleCrew:
    def kickoff(self, draft):
        # Agent autonomously decides what to search for
        rules = self.agentic_rag.discover_relevant_rules(draft)
        return self.apply_style_rules(draft, rules)

# 5. Quality Agent - Final validation
class QualityCrew:
    def kickoff(self, styled_draft):
        return self.final_quality_check(styled_draft)
```

## 🔧 Development Workflows

### Adding New Agents

```python
# 1. Create new crew class
class NewFeatureCrew:
    def __init__(self):
        self.agent = Agent(
            role="Feature Specialist", 
            goal="Implement new feature",
            backstory="Expert in feature development"
        )
    
    def kickoff(self, inputs):
        # Your implementation here
        return results

# 2. Add to linear flow
class LinearExecutionChain:
    def __init__(self):
        self.stages = [
            ResearchStage(),
            AudienceStage(), 
            WriterStage(),
            StyleStage(),
            NewFeatureStage(),  # Add here
            QualityStage()
        ]
```

### Using AI Assistant Function Calls

```python
# Available function calls for AI Assistant
functions = [
    {
        "name": "analyze_draft_impact",
        "description": "Analyze impact of changes on draft quality",
        "parameters": {
            "change_description": str,
            "current_draft": str
        }
    },
    {
        "name": "regenerate_draft_with_suggestions", 
        "description": "Regenerate draft with specific improvements",
        "parameters": {
            "suggestions": List[str],
            "focus_areas": List[str]
        }
    },
    {
        "name": "analyze_style_compliance",
        "description": "Check draft compliance with style guide", 
        "parameters": {
            "draft_content": str,
            "platform": str
        }
    }
]

# Example usage in chat
user_message = "Make the hook more engaging"
# AI Assistant automatically calls regenerate_draft_with_suggestions
```

### Testing Your Changes

```bash
# Run all tests (277+ tests)
make test

# Run specific test categories
make test-unit           # Unit tests only
make test-integration    # Integration tests only  
make test-performance    # Performance benchmarks

# Run with coverage
make test-coverage       # Generate coverage report

# Validate environment
make validate-env        # Check all system requirements
```

### Debugging Linear Flow

```python
# Enable detailed logging
import logging
logging.getLogger("ai_writing_flow").setLevel(logging.DEBUG)

# Track execution with profiler
from ai_writing_flow.profiling import FlowProfiler

profiler = FlowProfiler()
with profiler.profile_section("my_feature"):
    result = my_function()

print(profiler.get_recommendations())  # Get optimization suggestions
```

## 📊 Monitoring & Observability

### Real-Time Metrics

```python
# Access live metrics
from ai_writing_flow.monitoring import FlowMetrics

metrics = FlowMetrics()

# Track custom metrics
metrics.track_execution("my_stage", execution_time=1.5)
metrics.increment_counter("my_feature_usage")

# Get current KPIs
current_metrics = metrics.get_current_metrics()
print(f"Average execution time: {current_metrics['avg_execution_time']}s")
```

### Health Monitoring

```bash
# Check system health
curl http://localhost:8003/health

# Response includes:
{
  "status": "healthy",
  "components": {
    "linear_flow": "healthy",
    "ai_assistant": "healthy", 
    "agentic_rag": "healthy",
    "monitoring": "healthy"
  },
  "metrics": {
    "avg_execution_time": 25.3,
    "memory_usage_mb": 87.2,
    "cpu_usage_percent": 23.1
  }
}
```

### Dashboard Integration

```python
# Get dashboard metrics for UI
from ai_writing_flow.monitoring import DashboardAPI

dashboard = DashboardAPI()

# Time-series data for charts
metrics = dashboard.get_time_series_metrics(
    start_time="2025-08-06T00:00:00Z",
    end_time="2025-08-06T23:59:59Z"
)

# Real-time KPIs
current_kpis = dashboard.get_current_kpis()
```

## 🔍 TRUE Agentic RAG Development

### Understanding Agentic RAG

```python
# Traditional RAG (hardcoded queries)
def traditional_rag(content):
    queries = [
        "LinkedIn writing style",      # Fixed query
        "professional tone rules",    # Predetermined 
        "engagement techniques"       # Hardcoded
    ]
    
# TRUE Agentic RAG (agent decides)
def agentic_rag(content):
    # Agent analyzes content and decides what to search
    decisions = agent.analyze_content(content)
    
    queries = []
    for decision in decisions:
        # Agent generates unique query for each decision
        query = agent.generate_search_query(decision)
        queries.append(query)
    
    # Result: Different queries for same input = unique content
```

### Adding New Style Rules

```python
# Style rules are loaded from markdown files
# Location: /styleguides/*.md

# Example rule format:
"""
## Hook Effectiveness Rules

### Strong Hooks
- Start with surprising statistic: "87% of marketers..."
- Use power words: "Revolutionary", "Breakthrough", "Unprecedented"
- Ask compelling questions: "What if I told you..."

### Platform-Specific
- **LinkedIn**: Professional tone with personal insights
- **Twitter**: Conversational, use emojis sparingly
"""

# Rules are automatically indexed in ChromaDB
# Agent searches semantically: "How to write engaging hooks"
```

### Monitoring Agentic RAG

```python
# Track RAG performance
from ai_writing_flow.monitoring import RAGMetrics

rag_metrics = RAGMetrics()

# See what agent is searching for
search_log = rag_metrics.get_recent_searches()
for search in search_log:
    print(f"Query: {search.query}")
    print(f"Results: {len(search.results)}")
    print(f"Relevance: {search.avg_relevance_score}")
```

## 🚀 Deployment & Production

### Local Development

```bash
# Start development environment
make dev                 # Starts all services with hot reload

# Services available:
# - API: http://localhost:8003
# - Docs: http://localhost:8003/docs  
# - Health: http://localhost:8083
# - ChromaDB: http://localhost:8000
```

### Production Deployment

```bash
# Production build
make build-production

# Deploy to production
make deploy-production

# Monitor deployment
make monitor-production

# Rollback if needed
make rollback-production
```

### Environment Configuration

```bash
# Required environment variables
export OPENAI_API_KEY="your-openai-key"

# Optional (with defaults)
export CHROMA_HOST="localhost"      # ChromaDB host
export CHROMA_PORT="8000"           # ChromaDB port  
export REDIS_URL="redis://localhost:6379"  # Redis cache
export LOG_LEVEL="INFO"             # Logging level
export MAX_WORKERS="4"              # API workers
```

## 🔧 Common Development Tasks

### Adding Custom Tools

```python
from crewai.tools import tool

@tool("My Custom Tool")
def my_custom_tool(input_text: str) -> str:
    """Description of what the tool does"""
    # Your implementation
    return result

# Add to agent
agent = Agent(
    role="My Agent",
    tools=[my_custom_tool, existing_tools...]
)
```

### Extending AI Assistant

```python
# Add new function call capability
def new_assistant_function(parameter: str) -> str:
    """New capability for AI Assistant"""
    # Implementation
    return result

# Register with AI Assistant
assistant.register_function({
    "name": "new_assistant_function",
    "description": "What this function does",
    "function": new_assistant_function
})
```

### Performance Optimization

```bash
# Profile your changes
make profile-flow        # Profile complete flow execution

# Check memory usage  
make profile-memory      # Memory usage analysis

# Performance benchmarks
make benchmark          # Compare with baseline performance

# Cache optimization
make profile-cache      # Cache hit rate analysis
```

## 📚 Best Practices

### Code Style

```python
# Use type hints
def process_content(content: str, platform: str) -> ProcessedContent:
    pass

# Document functions
def complex_function(param: str) -> dict:
    """
    Brief description of function.
    
    Args:
        param: Description of parameter
        
    Returns:
        dict: Description of return value
        
    Raises:
        ValueError: When validation fails
    """
    pass

# Use logging instead of print
import logging
logger = logging.getLogger(__name__)

logger.info("Processing started")  # Not print()
```

### Error Handling

```python
from ai_writing_flow.utils import CircuitBreaker, RetryManager

# Use circuit breakers for external services
@CircuitBreaker(failure_threshold=5, timeout=60)
def call_external_api():
    # API call
    pass

# Implement retries with exponential backoff
@RetryManager(max_retries=3, backoff_factor=2)
def potentially_failing_operation():
    # Operation that might fail
    pass
```

### Testing Guidelines

```python
# Test structure
class TestMyFeature:
    def test_happy_path(self):
        """Test normal operation"""
        pass
        
    def test_edge_cases(self):
        """Test boundary conditions"""
        pass
        
    def test_error_handling(self):
        """Test failure scenarios"""
        pass
        
    def test_performance(self):
        """Test meets performance requirements"""
        pass
```

## 🐛 Troubleshooting

### Common Issues

**Issue**: "LinearExecutionChain taking too long"
```python
# Solution: Check execution guards
from ai_writing_flow.execution_guards import ExecutionGuards

guards = ExecutionGuards()
guards.set_max_execution_time(30)  # 30 second limit
guards.set_max_memory_usage(100)   # 100MB limit
```

**Issue**: "ChromaDB connection failed"
```bash
# Check ChromaDB health
curl http://localhost:8000/api/v1/heartbeat

# Restart ChromaDB container
docker-compose restart chroma-db
```

**Issue**: "AI Assistant not responding"
```bash
# Check AI Assistant health
curl http://localhost:8003/api/chat/health

# Check OpenAI API key
echo $OPENAI_API_KEY
```

### Performance Debugging

```python
# Enable performance profiling
from ai_writing_flow.profiling import FlowProfiler

profiler = FlowProfiler()
with profiler.profile_execution():
    result = flow.execute(inputs)

# Get bottleneck analysis
recommendations = profiler.get_recommendations()
print(f"Slowest stage: {recommendations['bottleneck']}")
print(f"Optimization: {recommendations['suggestion']}")
```

### Debug Logging

```python
# Enable debug logging for specific components
import logging

# Linear flow debugging
logging.getLogger("ai_writing_flow.linear").setLevel(logging.DEBUG)

# AI Assistant debugging  
logging.getLogger("ai_writing_flow.assistant").setLevel(logging.DEBUG)

# Agentic RAG debugging
logging.getLogger("ai_writing_flow.agentic_rag").setLevel(logging.DEBUG)
```

## 🎯 Advanced Topics

### Custom Monitoring Metrics

```python
from ai_writing_flow.monitoring import CustomMetric

# Create custom metric
my_metric = CustomMetric(
    name="feature_usage",
    type="counter", 
    description="Track usage of my feature"
)

# Track usage
my_metric.increment({"feature_name": "my_feature"})

# Query metrics
usage_data = my_metric.query_time_series(
    start_time="2025-08-06T00:00:00Z",
    end_time="2025-08-06T23:59:59Z"
)
```

### Extending Agentic RAG

```python
class CustomRAGAgent(AgenticRAGAgent):
    def analyze_content(self, content: str, platform: str):
        # Your custom analysis logic
        decisions = super().analyze_content(content, platform)
        
        # Add custom search decisions
        decisions.append({
            "search_type": "custom_feature",
            "reasoning": "Need to check custom feature rules",
            "query_context": {"feature": "my_feature"}
        })
        
        return decisions
```

### Container Customization

```dockerfile
# Extend base container
FROM kolegium-base:latest

# Add custom dependencies
RUN pip install my-custom-package

# Copy custom configurations
COPY custom-config.yaml /app/config/

# Custom health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

## 📞 Getting Help

### Documentation Resources

- **API Reference**: http://localhost:8003/docs (when running)
- **Architecture Guide**: [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Production Context**: [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md)
- **System Health**: http://localhost:8003/health

### Debug Commands

```bash
# System information
make system-info         # Show system configuration

# Log analysis
make logs               # Show recent logs
make logs-follow        # Follow logs in real-time

# Performance analysis
make performance-report # Generate performance report

# Health checks
make health-check       # Run all health validations
```

### Support Channels

- **Health Dashboard**: http://localhost:8083 (system metrics)
- **API Documentation**: http://localhost:8003/docs (interactive docs)
- **System Status**: http://localhost:8003/health (real-time status)

---

**Developer Guide Status**: ✅ Complete for production-ready Vector Wave AI Kolegium system with Linear Flow architecture, Enterprise Monitoring, AI Assistant integration, and Container-First deployment.

**Happy Coding!** 🚀