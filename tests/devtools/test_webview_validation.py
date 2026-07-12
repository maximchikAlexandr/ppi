import json
from pathlib import Path

from ppi.devtools.codegen.webview import validate_webview_schema


def test_invalid_webview_schema_rejection(tmp_path: Path):
    schema_file = tmp_path / "bad.schema.json"
    schema_file.write_text(json.dumps({"type": "invalid"}), encoding="utf-8")
    issues = validate_webview_schema(schema_file)
    assert len(issues) > 0


def test_valid_oneof_webview_schema_passes(tmp_path: Path):
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "WebviewProtocol",
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    "direction": {"const": "inbound"},
                    "action": {"type": "string", "enum": ["ppi/test"]},
                    "payload": {"type": "string"},
                },
                "required": ["direction", "action", "payload"],
            },
            {
                "type": "object",
                "properties": {
                    "direction": {"const": "outbound"},
                    "command": {"type": "string", "enum": ["ppi/test"]},
                    "payload": {"type": "string"},
                },
                "required": ["direction", "command", "payload"],
            },
        ],
    }
    schema_file = tmp_path / "valid.schema.json"
    schema_file.write_text(json.dumps(schema), encoding="utf-8")
    issues = validate_webview_schema(schema_file)
    assert len(issues) == 0


def test_bundle_schema_rejected(tmp_path: Path):
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "inbound": {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
            "outbound": {"type": "object", "properties": {"y": {"type": "string"}}, "required": ["y"]},
        },
        "required": ["inbound", "outbound"],
    }
    schema_file = tmp_path / "bundle.schema.json"
    schema_file.write_text(json.dumps(schema), encoding="utf-8")
    issues = validate_webview_schema(schema_file)
    assert any("oneof" in i.message.lower() or "oneOf" in i.message for i in issues)
