#!/usr/bin/env python3
import argparse
import json
import os
from jsonschema import Draft202012Validator

SCHEMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "schema", "rule_document.schema.json"))


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_file(path: str) -> dict:
    schema = load_json(SCHEMA_PATH)
    data = load_json(path)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    return {
        "path": path,
        "errors": [
            {
                "path": list(e.path),
                "message": e.message,
                "schema_path": list(e.schema_path)
            }
            for e in errors
        ]
    }


def main():
    parser = argparse.ArgumentParser(description="Validate rule documents against schema")
    parser.add_argument("--path", required=True, help="Path to JSON file with rule documents (array)")
    args = parser.parse_args()

    result = validate_file(args.path)
    result["validation_errors"] = len(result["errors"])
    print(json.dumps(result))

if __name__ == "__main__":
    main()
