import sys, pathlib
import asyncio
import pytest

# Add src to path
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from linear_flow_engine import LinearFlowEngine  # type: ignore


class DummyAgent:
    def __init__(self, agent_type: str, suggestions=None, fail=False):
        self.agent_type = agent_type
        self.suggestions = suggestions or []
        self.fail = fail
        self.calls = []

    async def validate_content(self, content: str, platform: str, validation_mode: str = "selective"):
        self.calls.append((content, platform, validation_mode))
        if self.fail:
            raise RuntimeError(f"agent_{self.agent_type}_failed")
        # Emulate Editorial Service envelope
        return {
            "mode": validation_mode,
            "rules_applied": [{"id": "r1"}],
            "rule_count": 1,
            "suggestions": list(self.suggestions),
        }


class DummyClients:
    def __init__(self, mapping):
        self.mapping = mapping

    def get_agent(self, t: str):
        return self.mapping[t]


@pytest.mark.asyncio
async def test_full_linear_flow_integration_happy_path():
    agents = {
        "research": DummyAgent("research", ["Add stats"]),
        "audience": DummyAgent("audience", ["Clarify audience"]),
        "writer": DummyAgent("writer", ["Improve hook"]),
        "style": DummyAgent("style", ["Use active voice"]),
        "quality": DummyAgent("quality", []),
    }
    engine = LinearFlowEngine(DummyClients(agents))

    result = await engine.run("Draft", platform="linkedin")

    assert len(result["steps"]) == 5
    # Modes: non-writer comprehensive by default, writer selective
    modes = {s["agent"]: s["mode"] for s in result["steps"]}
    assert modes["writer"] == "selective"
    assert modes["research"] == "comprehensive"
    assert isinstance(result["final_content"], str)
    assert "Improvements applied:" in result["final_content"]


@pytest.mark.asyncio
async def test_linear_flow_failure_resilience_stateful():
    agents = {
        "research": DummyAgent("research"),
        "audience": DummyAgent("audience"),
        "writer": DummyAgent("writer"),
        "style": DummyAgent("style", fail=True),  # force failure
        "quality": DummyAgent("quality"),
    }
    engine = LinearFlowEngine(DummyClients(agents))

    flow_id = await engine.execute_flow("Draft", platform="linkedin")

    # Poll until failed
    for _ in range(20):
        st = await engine.get_status(flow_id)
        if st and st.get("status") in ("failed", "completed"):
            break
        await asyncio.sleep(0.05)

    st = await engine.get_status(flow_id)
    assert st is not None
    assert st["status"] == "failed"
    # error message should be present (content may vary)
    assert st.get("error_message")
