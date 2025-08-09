import json
import os
import tempfile
import time
from pathlib import Path

import pytest

# Helper to run CLI scripts via python -m for isolation is not used here; we import modules directly.

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "migration"
SCHEMA = MIGRATION / "schema" / "rule_document.schema.json"

# Conditionally import jsonschema if available in environment
try:
    from jsonschema import Draft202012Validator  # type: ignore
except Exception:  # pragma: no cover
    Draft202012Validator = None  # type: ignore


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.skipif(Draft202012Validator is None, reason="jsonschema not available in test environment")
def test_styleguides_transformation_schema_valid(tmp_path: Path):
    # Arrange: create a tiny styleguide markdown file
    md = tmp_path / "sg.md"
    md.write_text("""
- Avoid buzzwords like synergy.
- You must include a clear CTA.
""".strip())

    # Act
    from migration.transform_styleguides_to_rules import transform_styleguides  # type: ignore

    docs = transform_styleguides(str(tmp_path))

    # Assert: non-empty and schema-valid
    assert len(docs) >= 2

    schema = load_json(SCHEMA)
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(docs))
    assert errors == []


@pytest.mark.skipif(Draft202012Validator is None, reason="jsonschema not available in test environment")
def test_aiwf_transformation_dedup_and_schema(tmp_path: Path):
    # Arrange: create a simulated discovery catalog
    catalog = {
        "files": [
            {
                "file": "/tmp/a.py",
                "hits": [
                    {
                        "type": "forbidden_phrases",
                        "start_line": 1,
                        "end_line": 3,
                        "snippet": "forbidden_phrases = ['foo', 'bar']",
                        "values_preview": ["foo", "bar"],
                        "priority_guess": "high",
                        "category_guess": "forbidden",
                    },
                    {
                        "type": "directive_line",
                        "start_line": 10,
                        "end_line": 10,
                        "snippet": "You should avoid passive voice.",
                        "values_preview": [],
                        "priority_guess": "medium",
                        "category_guess": "directive_line",
                    },
                ],
            }
        ]
    }
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps(catalog))

    # Act
    from migration.transform_ai_writing_flow_rules import transform_catalog  # type: ignore

    docs = transform_catalog(load_json(catalog_path))

    # Assert: dedup by content and schema valid
    contents = [d["content"].lower() for d in docs]
    assert len(contents) == len(set(contents))

    schema = load_json(SCHEMA)
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(docs))
    assert errors == []


@pytest.mark.skipif(Draft202012Validator is None, reason="jsonschema not available in test environment")
def test_platform_transformation_platform_classified(tmp_path: Path):
    # Arrange: create publisher discovery catalog sample
    catalog = {
        "files": [
            {
                "file": "/tmp/publisher/linked.py",
                "hits": [
                    {
                        "type": "max_length",
                        "platform": "linkedin",
                        "line": 12,
                        "snippet": "MAX_LENGTH = 300  # linkedin",
                        "values": {"strings": ["linkedin"], "numbers": [300]},
                    },
                    {
                        "type": "forbidden_phrases",
                        "platform": "linkedin",
                        "line": 20,
                        "snippet": "Avoid 'salesy' wording",
                        "values": {"strings": ["salesy"], "numbers": []},
                    },
                ],
            }
        ]
    }
    catalog_path = tmp_path / "pub_catalog.json"
    catalog_path.write_text(json.dumps(catalog))

    # Act
    from migration.transform_publisher_platform_rules import transform_catalog  # type: ignore

    docs = transform_catalog(load_json(catalog_path))

    # Assert: schema valid and platform set to linkedin
    assert len(docs) >= 2
    assert all(d["metadata"]["platform"] == "linkedin" for d in docs)

    schema = load_json(SCHEMA)
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(docs))
    assert errors == []


@pytest.mark.skipif(Draft202012Validator is None, reason="jsonschema not available in test environment")
def test_engine_reports_metrics(tmp_path: Path, monkeypatch):
    # Arrange: small AIWF catalog
    catalog = {
        "files": [
            {
                "file": "/tmp/a.py",
                "hits": [
                    {
                        "type": "directive_line",
                        "start_line": 1,
                        "end_line": 1,
                        "snippet": "You must include a CTA.",
                        "values_preview": [],
                        "priority_guess": "high",
                        "category_guess": "directive_line",
                    }
                ],
            }
        ]
    }
    catalog_path = tmp_path / "engine_catalog.json"
    out_path = tmp_path / "engine_out.json"
    catalog_path.write_text(json.dumps(catalog))

    # Patch validator to point to local schema path (engine invokes CLI validator relative to migration dir)
    engine = MIGRATION / "rule_transformation_engine.py"
    assert engine.exists()

    # Execute engine via subprocess to capture stdout JSON
    import subprocess, sys
    cmd = [sys.executable, str(engine), "--source", "aiwf", "--input", str(catalog_path), "--output", str(out_path)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    assert proc.returncode == 0, proc.stderr
    meta = json.loads(proc.stdout)
    assert meta.get("status") in ("ok", "invalid")
    assert meta.get("count", 1) >= 1
    assert "ms" in meta and "ms_per_rule" in meta
