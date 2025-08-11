import argparse
import json
import sys
from typing import Any, Dict

try:
    from ai_writing_flow.crews.research_crew import ResearchCrew
except ImportError:  # pragma: no cover
    import os
    import sys as _sys
    _sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ai_writing_flow", "src"))
    from ai_writing_flow.crews.research_crew import ResearchCrew  # type: ignore


def _print_json(data: Dict[str, Any]) -> None:
    json.dump(data, sys.stdout, ensure_ascii=False)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Kolegium Research Crew CLI Playbook")
    parser.add_argument("--topic", required=True, help="Temat badań")
    parser.add_argument("--sources-path", required=True, help="Ścieżka do pliku/folderu źródeł (md)")
    parser.add_argument("--context", default="", help="Kontekst ze styleguide lub instrukcji")
    parser.add_argument("--content-ownership", default="EXTERNAL", choices=["ORIGINAL", "EXTERNAL"], help="Charakter treści")
    parser.add_argument("--topic-manager-url", default="http://localhost:8041", help="URL Topic Manager")

    args = parser.parse_args(argv)

    crew = ResearchCrew(topic_manager_url=args.topic_manager_url)
    result = crew.execute(args.topic, args.sources_path, args.context, args.content_ownership)

    payload = {
        "summary": result.summary,
        "sources": result.sources,
        "key_insights": result.key_insights,
        "data_points": result.data_points,
        "methodology": result.methodology,
    }
    _print_json(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
