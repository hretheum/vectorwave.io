#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import time
from typing import Dict

HERE = os.path.abspath(os.path.dirname(__file__))
OUT_DIR = os.path.join(HERE, "output")
SCHEMA_VALIDATOR = os.path.join(HERE, "validate_against_schema.py")

STYLEGUIDES_SCRIPT = os.path.join(HERE, "transform_styleguides_to_rules.py")
AIWF_SCRIPT = os.path.join(HERE, "transform_ai_writing_flow_rules.py")
PLATFORM_SCRIPT = os.path.join(HERE, "transform_publisher_platform_rules.py")


def run_cmd(cmd: list[str]) -> str:
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout.strip()


def validate_schema(path: str) -> Dict:
    output = run_cmd([sys.executable, SCHEMA_VALIDATOR, "--path", path])
    data = json.loads(output)
    return {"validation_errors": data.get("validation_errors", 999), "errors": data.get("errors", [])}


def transform_styleguides(input_dir: str, output: str) -> Dict:
    t0 = time.perf_counter()
    out = run_cmd([sys.executable, STYLEGUIDES_SCRIPT, "--input-dir", input_dir, "--output", output])
    elapsed = (time.perf_counter() - t0) * 1000.0
    meta = json.loads(out)
    count = int(meta.get("count", 0))
    return {"count": count, "ms": round(elapsed, 2), "ms_per_rule": round(elapsed / max(1, count), 3)}


def transform_aiwf(catalog: str, output: str) -> Dict:
    t0 = time.perf_counter()
    out = run_cmd([sys.executable, AIWF_SCRIPT, "--catalog", catalog, "--output", output])
    elapsed = (time.perf_counter() - t0) * 1000.0
    meta = json.loads(out)
    count = int(meta.get("count", 0))
    return {"count": count, "ms": round(elapsed, 2), "ms_per_rule": round(elapsed / max(1, count), 3)}


def transform_platform(catalog: str, output: str) -> Dict:
    t0 = time.perf_counter()
    out = run_cmd([sys.executable, PLATFORM_SCRIPT, "--catalog", catalog, "--output", output])
    elapsed = (time.perf_counter() - t0) * 1000.0
    meta = json.loads(out)
    count = int(meta.get("count", 0))
    return {"count": count, "ms": round(elapsed, 2), "ms_per_rule": round(elapsed / max(1, count), 3)}


def main():
    parser = argparse.ArgumentParser(description="Unified Rule Transformation Engine (with schema validation)")
    parser.add_argument("--source", required=True, choices=["styleguides", "aiwf", "platform"], help="Source type")
    parser.add_argument("--input", required=True, help="Input path (dir for styleguides; catalog JSON for aiwf/platform)")
    parser.add_argument("--output", required=False, help="Output JSON path")
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    output = args.output or {
        "styleguides": os.path.join(OUT_DIR, "engine_styleguides_rules.json"),
        "aiwf": os.path.join(OUT_DIR, "engine_aiwf_rules.json"),
        "platform": os.path.join(OUT_DIR, "engine_platform_rules.json"),
    }[args.source]

    try:
        if args.source == "styleguides":
            stats = transform_styleguides(args.input, output)
        elif args.source == "aiwf":
            stats = transform_aiwf(args.input, output)
        else:
            stats = transform_platform(args.input, output)

        schema = validate_schema(output)
        success = schema.get("validation_errors", 1) == 0

        print(json.dumps({
            "status": "ok" if success else "invalid",
            "source": args.source,
            "output": output,
            **stats,
            "schema_errors": schema.get("validation_errors")
        }))
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "error": str(e)
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
