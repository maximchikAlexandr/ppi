from __future__ import annotations

from pathlib import Path

from typing import Any

import jsonschema
import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        msg = f"{path}: expected a YAML mapping"
        raise ValueError(msg)
    return data


def load_json_schema(path: Path) -> dict[str, Any]:
    import json
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        msg = f"{path}: expected a JSON object"
        raise ValueError(msg)
    return data


def validate_schema(schema: dict[str, Any]) -> list[str]:
    try:
        jsonschema.Draft7Validator.check_schema(schema)
    except jsonschema.SchemaError as e:
        return [str(e)]
    return []



