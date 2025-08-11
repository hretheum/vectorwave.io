import argparse
import json
import sys
from typing import Any, Dict, List

try:
    from ai_writing_flow.crews.quality_crew import QualityCrew
except ImportError:  # pragma: no cover
    import os
    import sys as _sys
    _sys.path.append(os.path.join(os.path.dirname(__file__), "..", "ai_writing_flow", "src"))
    from ai_writing_flow.crews.quality_crew import QualityCrew  # type: ignore


def _print_json(data: Dict[str, Any]) -> None:
    json.dump(data, sys.stdout, ensure_ascii=False)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Kolegium Quality Crew CLI Playbook")
    parser.add_argument("--draft", required=True, help="Szkic treści do oceny")
    parser.add_argument("--platform", default="general", help="Platforma docelowa")
    parser.add_argument("--content-type", default="article", help="Typ treści (article, post, newsletter)")
    parser.add_argument("--sources", nargs='*', default=[], help="Źródła w formacie JSON (lista dictów)")
    parser.add_argument("--editorial-url", default="http://localhost:8040", help="URL Editorial Service")

    args = parser.parse_args(argv)

    # Parse sources if provided as JSON string(s)
    sources: List[Dict[str, str]] = []
    for s in args.sources:
        try:
            sources.append(json.loads(s))
        except Exception:
            pass

    crew = QualityCrew(editorial_service_url=args.editorial_url)
    assessment = crew.execute(args.draft, sources, {"platform": args.platform, "content_type": args.content_type})

    payload = {
        "is_approved": assessment.is_approved,
        "quality_score": assessment.quality_score,
        "fact_check_results": assessment.fact_check_results,
        "code_verification": assessment.code_verification,
        "ethics_checklist": assessment.ethics_checklist,
        "improvement_suggestions": assessment.improvement_suggestions,
        "requires_human_review": assessment.requires_human_review,
        "controversy_score": assessment.controversy_score,
    }
    _print_json(payload)
    return 0 if assessment.is_approved else 1


if __name__ == "__main__":
    sys.exit(main())
