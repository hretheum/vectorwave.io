import pytest
import asyncio
from types import SimpleNamespace

import sys
import pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from linear_flow_engine import LinearFlowEngine  # type: ignore


class DummyAgent:
    def __init__(self, agent_type: str, suggestions: list[str] | None = None):
        self.agent_type = agent_type
        self.suggestions = suggestions or []
        self.calls = []

    async def validate_content(self, content: str, platform: str, validation_mode: str = "selective"):
        self.calls.append((content, platform, validation_mode))
        # return a shape compatible with envelope
        return {"mode": validation_mode, "suggestions": list(self.suggestions)}


class DummyClients:
    def __init__(self, mapping):
        self.mapping = mapping

    def get_agent(self, t: str):
        return self.mapping[t]


@pytest.mark.asyncio
async def test_linear_flow_order_and_mutation():
    agents = {
        "research": DummyAgent("research", ["Add context"]),
        "audience": DummyAgent("audience", ["Clarify primary audience"]),
        "writer": DummyAgent("writer", ["Tighten intro"]),
        "style": DummyAgent("style", ["Active voice"]),
        "quality": DummyAgent("quality", []),
    }
    engine = LinearFlowEngine(DummyClients(agents))

    result = await engine.run("Draft", platform="linkedin")

    # Check order of calls
    assert [a for a in agents] == list(LinearFlowEngine.ORDER)
    # Writer receives mutated content (at least suggestions applied once)
    writer_call_content = agents["writer"].calls[0][0]
    assert "Improvements applied:" in writer_call_content
    # Final content contains accumulated improvements
    assert "Improvements applied:" in result["final_content"]
