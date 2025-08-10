from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple

from agent_clients import CrewAIAgentClients


class LinearFlowEngine:
    """Deterministic multi-agent flow research→audience→writer→style→quality.

    Each step may return suggestions; we apply a simple mutation strategy to
    feed improved content to the next step.
    """

    ORDER: Tuple[str, ...] = (
        "research",
        "audience",
        "writer",
        "style",
        "quality",
    )

    def __init__(self, clients: CrewAIAgentClients) -> None:
        self.clients = clients

    async def run(
        self,
        content: str,
        platform: str,
        content_type: str = "article",
        prefer_comprehensive: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, Any]:
        prefer = prefer_comprehensive or {}
        current_content = content
        results: Dict[str, Any] = {"steps": []}

        for agent in self.ORDER:
            mode = "comprehensive" if prefer.get(agent, agent in ("research", "audience", "style", "quality")) else "selective"
            client = self.clients.get_agent(agent)
            validation = await client.validate_content(current_content, platform, validation_mode=mode)
            results["steps"].append({"agent": agent, "mode": mode, "result": validation})
            # Mutate content with suggestions if present
            suggestions: List[str] = validation.get("suggestions", []) if isinstance(validation, dict) else []
            if suggestions:
                current_content = self._apply_suggestions(current_content, suggestions)
        results["final_content"] = current_content
        return results

    def _apply_suggestions(self, content: str, suggestions: List[str]) -> str:
        # Simple strategy: append top-3 suggestions as actionable bullets at end
        top = suggestions[:3]
        if not top:
            return content
        lines = [content.strip(), "", "Improvements applied:"] + [f"- {s}" for s in top]
        return "\n".join(lines)
