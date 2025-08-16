"""
Utilities for processing Editorial Service validation results.

Provides aggregation and scoring helpers compatible with both
selective and comprehensive validation modes.
"""

from typing import Dict, Any


SEVERITY_WEIGHTS = {
    "critical": 3.0,
    "error": 2.0,
    "warning": 1.0,
    "info": 0.5,
}


def aggregate_rules(validation_result: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate applied rules and violations into a compact summary.

    Args:
        validation_result: Response dict returned by Editorial Service, expected
            to optionally include `rules_applied` and `violations` arrays.

    Returns:
        Dict with fields: rule_count, critical_count, score.
        Score is a weighted sum of violation severities (higher = worse).
    """
    rules = validation_result.get("rules_applied") or []
    violations = validation_result.get("violations") or []

    rule_count = len(rules)
    critical_count = sum(1 for v in violations if str(v.get("severity", "")).lower() == "critical")

    score = 0.0
    for v in violations:
        sev = str(v.get("severity", "")).lower()
        score += SEVERITY_WEIGHTS.get(sev, 0.0)

    return {
        "rule_count": rule_count,
        "critical_count": critical_count,
        "score": score,
    }
