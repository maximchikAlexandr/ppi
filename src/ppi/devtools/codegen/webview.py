from __future__ import annotations

from pathlib import Path

from ppi.devtools.codegen.validate import load_json_schema, validate_schema
from ppi.devtools.codegen.types import ValidationIssue
from ppi.devtools.codegen.render import render_markdown_file, render_typescript_file, render_template


def validate_webview_schema(path: Path) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not path.is_file():
        issues.append(ValidationIssue("webview-protocol", f"source not found: {path}"))
        return issues
    try:
        schema = load_json_schema(path)
    except (ValueError, OSError) as exc:
        issues.append(ValidationIssue("webview-protocol", str(exc)))
        return issues

    schema_errors = validate_schema(schema)
    for e in schema_errors:
        issues.append(ValidationIssue("webview-protocol", e))

    if "oneOf" not in schema:
        issues.append(ValidationIssue("webview-protocol", "schema must use oneOf (discriminated union), not bundle top-level properties"))
        return issues

    for i, variant in enumerate(schema.get("oneOf", [])):
        props = variant.get("properties", {})
        if "direction" not in props or "const" not in props.get("direction", {}):
            issues.append(ValidationIssue(f"webview-protocol[oneOf/{i}]", "each variant must have 'direction' const discriminator"))
            break

    return issues


def generate_webview_docs(schema: dict, source: str, generator: str) -> str:
    variants = schema.get("oneOf", [])
    rows = ""
    for i, v in enumerate(variants):
        direction = v.get("properties", {}).get("direction", {}).get("const", f"variant_{i}")
        fields = list(v.get("properties", {}).keys())
        rows += f"| {direction} | {', '.join(fields)} |\n"
    body = f"""# Webview Protocol

| Direction | Fields |
|-----------|--------|
{rows}
"""
    return render_markdown_file(source, generator, body)


def _ts_type_from_prop(p: dict) -> str:
    const = p.get("const")
    if const:
        return f'"{const}"'
    enum_vals = p.get("enum")
    if enum_vals:
        return " | ".join(f'"{v}"' for v in enum_vals)
    return {"string": "string", "integer": "number", "boolean": "boolean", "object": "Record<string, unknown>"}.get(p.get("type", "string"), "string")


def generate_webview_protocol_ts(schema: dict, source: str, generator: str) -> str:
    variants = schema.get("oneOf", [])
    ifaces = []
    for v in variants:
        direction = v.get("properties", {}).get("direction", {}).get("const", "message")
        name = f"{direction.capitalize()}Message"
        fields = "\n".join(
            f"    {f}: {_ts_type_from_prop(p)};" for f, p in v.get("properties", {}).items()
        )
        ifaces.append(f"export interface {name} {{\n{fields}\n}}")
    union_rhs = "\n    | ".join(f"{v.get('properties', {}).get('direction', {}).get('const', 'message').capitalize()}Message" for v in variants)
    body = "\n\n".join(ifaces) + f"\n\nexport type WebviewMessage =\n    {union_rhs};\n"
    return render_typescript_file(source, generator, body)


# validateWebviewMessage generator removed per K4 — no runtime consumer (Zod provides webview message validation)
