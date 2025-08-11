import argparse
import json
import sys
from typing import Any, Dict

try:
    from ai_writing_flow.crews.writer_crew import WriterCrew
except ImportError:  # pragma: no cover
    import os
    import sys as _sys
    _sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ai_writing_flow", "src"))
    from ai_writing_flow.crews.writer_crew import WriterCrew  # type: ignore


def _print_json(data: Dict[str, Any]) -> None:
    json.dump(data, sys.stdout, ensure_ascii=False)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Kolegium Writer Crew CLI Playbook")
    parser.add_argument("--topic", required=True, help="Temat")
    parser.add_argument("--platform", required=True, help="Platforma docelowa (LinkedIn, Twitter, ...)")
    parser.add_argument("--audience-insights", required=True, help="Wskazówki dot. odbiorców")
    parser.add_argument("--research-summary", required=True, help="Streszczenie badań")
    parser.add_argument("--depth", type=int, default=2, help="Poziom głębi (1-3)")
    parser.add_argument("--editorial-url", default="http://localhost:8040", help="URL Editorial Service")

    args = parser.parse_args(argv)

    crew = WriterCrew(editorial_service_url=args.editorial_url)
    draft = crew.execute(
        args.topic,
        args.platform,
        args.audience_insights,
        args.research_summary,
        args.depth,
        {"platform": args.platform.lower()}
    )

    payload = {
        "title": draft.title,
        "word_count": draft.word_count,
        "structure_type": draft.structure_type,
        "key_sections": draft.key_sections,
        "non_obvious_insights": draft.non_obvious_insights,
        "draft": draft.draft,
    }
    _print_json(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
