# CrewAI Agents

Agents are the core building blocks of CrewAI. Each agent is designed to perform specific roles and collaborate with other agents.

## Agent Configuration

- **Role**: The agent's job title and main responsibility
- **Goal**: What the agent is trying to achieve
- **Backstory**: Context that helps the agent understand its role
- **Tools**: Custom functions the agent can use
- **Verbose**: Whether to show agent's thinking process

## Example Agent

```python
from crewai import Agent

researcher = Agent(
    role='Research Specialist',
    goal='Gather and analyze information on given topics',
    backstory='You are an expert researcher with years of experience',
    tools=[search_tool, scraping_tool],
    verbose=True
)
```

Agents can be equipped with various tools and work together in crews to accomplish complex tasks.
EOF < /dev/null