import os
import sys


# Ensure src on sys.path for direct pytest from repo root
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from ai_writing_flow.clients.editorial_utils import aggregate_rules


def test_aggregate_rules_empty():
    summary = aggregate_rules({})
    assert summary["rule_count"] == 0
    assert summary["critical_count"] == 0
    assert summary["score"] == 0.0


def test_aggregate_rules_weighting():
    validation = {
        "rules_applied": [{"rule_id": "r1"}, {"rule_id": "r2"}],
        "violations": [
            {"severity": "critical"},
            {"severity": "warning"},
            {"severity": "error"},
            {"severity": "info"},
            {"severity": "unknown"},
        ],
    }
    summary = aggregate_rules(validation)
    assert summary["rule_count"] == 2
    assert summary["critical_count"] == 1
    # 3.0 + 1.0 + 2.0 + 0.5 + 0.0 = 6.5
    assert abs(summary["score"] - 6.5) < 1e-6
