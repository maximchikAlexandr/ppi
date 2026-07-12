from __future__ import annotations

import re

import yaml

from ppi.devtools.codegen.types import ValidationIssue
from ppi.devtools.codegen.render import render_python_file, render_typescript_file, render_markdown_file, render_template

VALID_CATEGORIES = {"client", "server", "runtime", "workspace", "contract", "transport", "extension", "unknown"}
VALID_STABILITIES = {"internal", "experimental", "public", "deprecated"}


def validate_errors(data: dict) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    errors = data.get("errors", [])
    seen_codes: set[str] = set()
    upper_snake = re.compile(r"^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$")

    for i, entry in enumerate(errors):
        code = entry.get("code", "")
        if not code:
            issues.append(ValidationIssue(f"errors[{i}]", "missing 'code'"))
            continue
        if not upper_snake.match(code):
            issues.append(ValidationIssue(f"errors[{i}]", f"code '{code}' must be uppercase snake case"))
        if code in seen_codes:
            issues.append(ValidationIssue(f"errors[{i}]", f"duplicate code '{code}'"))
        seen_codes.add(code)

        cat = entry.get("category", "")
        if cat not in VALID_CATEGORIES:
            issues.append(ValidationIssue(f"errors[{i}]", f"invalid category '{cat}'"))

        stab = entry.get("stability", "")
        if stab not in VALID_STABILITIES:
            issues.append(ValidationIssue(f"errors[{i}]", f"invalid stability '{stab}'"))

        desc = entry.get("description", "")
        if not desc and stab == "public":
            issues.append(ValidationIssue(f"errors[{i}]", f"description required for {stab} errors"))

        if stab == "deprecated":
            replacement = entry.get("replacement")
            removal_note = entry.get("removalNote")
            if not replacement and not removal_note:
                issues.append(ValidationIssue(f"errors[{i}]", "deprecated errors need 'replacement' or 'removalNote'"))

    return issues


def generate_errors_py(errors: list[dict], source: str, generator: str) -> str:
    enum_lines = "\n".join(f"    {e['code']} = \"{e['code']}\"" for e in errors)
    spec_lines = "\n".join(
        f"{e['code'].lower()}: Final[ErrorSpec] = ErrorSpec(\n"
        f"    code=ErrorCode.{e['code']},\n"
        f"    category=\"{e.get('category', '')}\",\n"
        f"    default_message=\"{e.get('defaultMessage', '')}\",\n"
        f"    retryable={'True' if e.get('retryable') else 'False'},\n"
        f"    stability=\"{e.get('stability', '')}\",\n"
        f"    description=\"{e.get('description', '')}\",\n"
        f"    http_status={e.get('httpStatus', 'None')},\n"
        f"    rpc_code=\"{e.get('rpcCode', '')}\",\n"
        f"    cli_exit_category=\"{e.get('cliExitCategory', '')}\",\n"
        f"    webview_action_mapping=\"{e.get('webviewActionMapping', '')}\",\n"
        f"    replacement=\"{e.get('replacement', '')}\",\n"
        f"    removal_note=\"{e.get('removalNote', '')}\",\n"
        f")"
        for e in errors
    )
    http_status_lines = "\n".join(
        f"    ErrorCode.{e['code']}: {e.get('httpStatus', 'None')},"
        for e in errors if e.get('httpStatus')
    )
    retryable_items = ", ".join(
        f"ErrorCode.{e['code']}" for e in errors if e.get('retryable')
    )
    errs_dict_items = ",\n".join(
        f"    ErrorCode.{e['code']}: {e['code'].lower()}" for e in errors
    )
    body = f"""from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final


class ErrorCode(str, Enum):
{enum_lines}


@dataclass(frozen=True)
class ErrorSpec:
    code: ErrorCode
    category: str = ""
    default_message: str = ""
    retryable: bool = False
    stability: str = ""
    description: str = ""
    http_status: int | None = None
    rpc_code: str = ""
    cli_exit_category: str = ""
    webview_action_mapping: str = ""
    replacement: str = ""
    removal_note: str = ""


_HTTP_STATUS_MAP: dict[ErrorCode, int | None] = {{
{http_status_lines}
}}

_RETRYABLE: frozenset[ErrorCode] = frozenset({{{retryable_items}}})


def http_status_for(code: ErrorCode) -> int | None:
    return _HTTP_STATUS_MAP.get(code)


def is_retryable(code: ErrorCode) -> bool:
    return code in _RETRYABLE


{spec_lines}

ERRORS: dict[ErrorCode, ErrorSpec] = {{
{errs_dict_items}
}}
"""
    return render_python_file(source, generator, body)


def generate_errors_docs(errors: list[dict], source: str, generator: str) -> str:
    entries = []
    for e in errors:
        entries.append({
            "code": e["code"],
            "category": e.get("category", ""),
            "default_message": e.get("defaultMessage", ""),
            "retryable": e.get("retryable", False),
            "stability": e.get("stability", ""),
            "description": e.get("description", ""),
            "http_status": e.get("httpStatus"),
            "rpc_code": e.get("rpcCode"),
            "cli_exit_category": e.get("cliExitCategory"),
            "webview_action_mapping": e.get("webviewActionMapping"),
        })
    body = render_template("errors.md.j2", errors=entries)
    return render_markdown_file(source, generator, body)


def generate_errors_ts(errors: list[dict], source: str, generator: str) -> str:
    lines = "\n".join(f"    {e['code']} = \"{e['code']}\"," for e in errors)
    body = f"""export enum ErrorCode {{
{lines}
}}
"""
    return render_typescript_file(source, generator, body)

