from ppi.devtools.codegen.progress import (
    build_progress_schema,
    generate_progress_schema_py,
    generate_progress_ts,
)
from ppi.runtime.progress import ProgressEvent


def test_progress_schema_is_deterministic():
    schema1 = build_progress_schema()
    schema2 = build_progress_schema()
    assert schema1 == schema2


def test_progress_schema_contains_one_of():
    schema = build_progress_schema()
    assert "oneOf" in schema
    assert len(schema["oneOf"]) > 0


def test_progress_schema_tags_match_wire_format():
    schema = build_progress_schema()
    consts = [v["properties"]["type"]["const"] for v in schema["oneOf"]]
    assert "run_started" in consts
    assert "commit_progress" in consts
    assert "run_completed" in consts
    assert "run_failed" in consts


def test_progress_schema_py_generation():
    schema = {"$schema": "...", "title": "ProgressEvent", "oneOf": []}
    result = generate_progress_schema_py(schema, "progress.py::ProgressEvent", "progress")
    assert "PROGRESS_EVENT_SCHEMA" in result
    assert "Generated file. Do not edit manually." in result


def test_progress_typescript_interfaces_have_single_closing_brace():
    result = generate_progress_ts(ProgressEvent.__args__, "progress.py::ProgressEvent", "progress")

    assert "\n}}\n" not in result
    assert "export interface RunStarted" in result

