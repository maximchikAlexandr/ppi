from __future__ import annotations

import json
import typing

import msgspec

from ppi.devtools.codegen.types import ValidationIssue
from ppi.devtools.codegen.render import render_python_file, render_typescript_file, render_markdown_file, render_template

# ponytail: hardcoded set of msgspec fields with defaults; extend when 2nd appears
_OPTIONAL_FIELDS: frozenset[str] = frozenset({"stderr_tail"})

_JSON_SCHEMA_TYPES: dict[type, dict] = {
    bool: {"type": "boolean"},
    int: {"type": "integer"},
    float: {"type": "number"},
    str: {"type": "string"},
}

_TS_TYPES: dict[type, str] = {
    bool: "boolean",
    int: "number",
    float: "number",
    str: "string",
}


def _type_to_json_schema(t: type) -> dict:
    origin = typing.get_origin(t)
    if origin is typing.Literal:
        args = typing.get_args(t)
        return {"enum": list(args)}
    return _JSON_SCHEMA_TYPES.get(t, {})


def _ts_type(t: type) -> str:
    origin = typing.get_origin(t)
    if origin is typing.Literal:
        args = typing.get_args(t)
        return " | ".join(repr(a) for a in args)
    return _TS_TYPES.get(t, "string")


def build_progress_schema() -> dict:
    import importlib
    mod = importlib.import_module("ppi.runtime.progress")
    union = getattr(mod, "ProgressEvent")
    variants = union.__args__
    one_of = []
    for v in variants:
        if not issubclass(v, msgspec.Struct):
            continue
        hints = typing.get_type_hints(v)
        props = {f: _type_to_json_schema(hints.get(f, str)) for f in v.__struct_fields__}
        required = ["type"] + [f for f in v.__struct_fields__ if f not in _OPTIONAL_FIELDS]
        one_of.append({
            "type": "object",
            "properties": {
                "type": {"const": _variant_tag(v)},
                **props,
            },
            "required": required,
        })
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "ProgressEvent",
        "oneOf": one_of,
    }


def generate_progress_schema_py(schema: dict, source: str, generator: str) -> str:
    body = f"""from __future__ import annotations

PROGRESS_EVENT_SCHEMA: dict = {json.dumps(schema, indent=2)}
"""
    return render_python_file(source, generator, body)


def generate_progress_docs(variants: tuple, source: str, generator: str) -> str:
    schema_list = []
    for v in variants:
        hints = typing.get_type_hints(v)
        fields = [(f, _ts_type(hints.get(f, str))) for f in v.__struct_fields__]
        schema_list.append({
            "tag": _variant_tag(v),
            "fields": fields,
        })
    body = render_template("progress_events.md.j2", events=schema_list)
    return render_markdown_file(source, generator, body)


def _ts_field_type(v: type, field: str) -> str:
    hints: dict[str, type] = typing.get_type_hints(v)
    return _ts_type(hints.get(field, str))


def _variant_tag(v: type) -> str:
    # ponytail: msgspec.Struct subclasses expose __struct_config__.tag
    return v.__struct_config__.tag  # type: ignore[attr-defined,no-any-return]


def generate_progress_ts(variants: tuple, source: str, generator: str) -> str:
    ifaces = []
    for v in variants:
        lines = []
        for f in v.__struct_fields__:
            optional = "?" if f in _OPTIONAL_FIELDS else ""
            lines.append(f"    {f}{optional}: {_ts_field_type(v, f)};")
        tag = _variant_tag(v)
        ifaces.append(f"export interface {v.__name__} {{\n    type: \"{tag}\";\n" + "\n".join(lines) + "\n}}")
    body = "\n\n".join(ifaces) + "\n\nexport type ProgressEvent =\n"
    body += " |\n".join(f"    {v.__name__}" for v in variants) + ";\n"
    return render_typescript_file(source, generator, body)


def generate_progress_validator_ts(schema: dict, source: str, generator: str) -> str:
    schema_str = json.dumps(schema, indent=2)
    body = f"""import Ajv from "ajv";

const ajv = new Ajv();
const schema = {schema_str} as const;
export const validateProgressEvent = ajv.compile(schema);
"""
    return render_typescript_file(source, generator, body)


def _demo() -> None:
    import json as _json
    import msgspec as _msgspec
    from ppi.runtime.progress import RunStarted
    schema = build_progress_schema()
    wire = _msgspec.json.encode(RunStarted(run_id="x", branch="m", mode="incremental", commits_total=1))
    payload = _json.loads(wire)
    consts = [v["properties"]["type"]["const"] for v in schema["oneOf"]]
    assert payload["type"] in consts, f"wire tag {payload['type']!r} not in schema consts {consts}"


if __name__ == "__main__":
    _demo()
