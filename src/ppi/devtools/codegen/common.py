from __future__ import annotations


HEADER_PYTHON = """# Generated file. Do not edit manually.
# Source: {source}
# Generator: {generator}
"""

HEADER_TS = """// Generated file. Do not edit manually.
// Source: {source}
// Generator: {generator}
"""

HEADER_MD = """<!-- Generated file. Do not edit manually. Source: {source}. Generator: {generator}. -->"""


def generated_header(language: str, source: str, generator: str) -> str:
    headers = {
        "python": HEADER_PYTHON,
        "typescript": HEADER_TS,
        "markdown": HEADER_MD,
    }
    header = headers.get(language)
    if header is None:
        msg = f"unsupported language: {language}"
        raise ValueError(msg)
    return header.format(source=source, generator=generator) if header else ""



