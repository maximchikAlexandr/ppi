from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from ppi.devtools.codegen.common import generated_header

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_ENV = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)))


def render_template(template_name: str, **kwargs: Any) -> str:
    return _ENV.get_template(template_name).render(**kwargs)


def render_python_file(source: str, generator: str, body: str) -> str:
    header = generated_header("python", source, generator)
    return f"{header}\n{body}"


def render_typescript_file(source: str, generator: str, body: str) -> str:
    header = generated_header("typescript", source, generator)
    return f"{header}\n{body}"


def render_markdown_file(source: str, generator: str, body: str) -> str:
    header = generated_header("markdown", source, generator)
    return f"{header}\n\n{body}"
