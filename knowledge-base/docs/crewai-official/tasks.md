# CrewAI Tasks

Tasks define what needs to be accomplished by agents. Each task has specific parameters and can be assigned to agents.

## Task Properties

- **Description**: Clear description of what needs to be done
- **Agent**: Which agent should execute this task
- **Tools**: Specific tools needed for this task
- **Expected Output**: What the result should look like
- **Dependencies**: Other tasks that must complete first

## Task Example

```python
from crewai import Task

research_task = Task(
    description='Research the latest trends in AI technology',
    agent=researcher,
    expected_output='A comprehensive report on AI trends',
    tools=[web_search, document_reader]
)
```

Tasks can be chained together to create complex workflows where the output of one task becomes input for another.
EOF < /dev/null