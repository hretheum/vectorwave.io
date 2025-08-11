import argparse
import json
import sys
from typing import Any, Dict

# Ensure ai_writing_flow is importable when running from repo root
try:
    from ai_writing_flow.crews.style_crew import StyleCrew
except ImportError:  # pragma: no cover
    import os
    import sys as _sys
    _sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ai_writing_flow", "src"))
    from ai_writing_flow.crews.style_crew import StyleCrew  # type: ignore


def _print_json(data: Dict[str, Any]) -> None:
    json.dump(data, sys.stdout, ensure_ascii=False)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Kolegium Style Crew CLI Playbook")
    parser.add_argument("--draft", required=True, help="Tekst do walidacji stylu")
    parser.add_argument("--platform", default="general", help="Platforma docelowa (linkedin, twitter, beehiiv, ghost)")
    parser.add_argument("--editorial-url", default="http://localhost:8040", help="URL Editorial Service")
    parser.add_argument("--min-score", type=int, default=70, help="Minimalny wynik zgodności (0-100)")

    args = parser.parse_args(argv)

    crew = StyleCrew(editorial_service_url=args.editorial_url, min_compliance_score=args.min_score)
    result = crew.execute(args.draft, {"platform": args.platform})

    payload = {
        "is_compliant": result.is_compliant,
        "compliance_score": result.compliance_score,
        "violations": result.violations,
        "forbidden_phrases": result.forbidden_phrases,
        "suggestions": result.suggestions,
    }
    _print_json(payload)
    return 0 if result.is_compliant else 1


if __name__ == "__main__":
    sys.exit(main())
