import argparse
import json
import sys
from typing import Any, Dict

try:
    from ai_writing_flow.crews.audience_crew import AudienceCrew
except ImportError:  # pragma: no cover
    import os
    import sys as _sys
    _sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ai_writing_flow", "src"))
    from ai_writing_flow.crews.audience_crew import AudienceCrew  # type: ignore


def _print_json(data: Dict[str, Any]) -> None:
    json.dump(data, sys.stdout, ensure_ascii=False)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Kolegium Audience Crew CLI Playbook")
    parser.add_argument("--topic", required=True, help="Temat do analizy")
    parser.add_argument("--platform", required=True, help="Platforma docelowa")
    parser.add_argument("--research-summary", default="", help="Streszczenie badań/kontekst")
    parser.add_argument("--editorial-recs", default="", help="Rekomendacje redakcyjne")
    parser.add_argument("--editorial-url", default="http://localhost:8040", help="URL Editorial Service")

    args = parser.parse_args(argv)

    crew = AudienceCrew(editorial_service_url=args.editorial_url)
    result = crew.execute(args.topic, args.platform, args.research_summary, args.editorial_recs)

    payload = {
        "recommended_depth": result.recommended_depth,
        "tone_calibration": result.tone_calibration,
        "key_messages": result.key_messages,
        "scores": {
            "technical_founder": result.technical_founder_score,
            "senior_engineer": result.senior_engineer_score,
            "decision_maker": result.decision_maker_score,
            "skeptical_learner": result.skeptical_learner_score,
        },
    }
    _print_json(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
