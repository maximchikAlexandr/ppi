"""Export the FastAPI app's OpenAPI schema to a deterministic JSON file.

Usage:
    uv run python scripts/export_openapi.py --output openapi/openapi.json

The output is written with sorted keys and a trailing newline so that
the contract is stable across runs and amenable to diff-based governance.

ponytail: the export passes a non-existent store path because OpenAPI
generation only walks registered routers and never probes the store.
If a future router adds a startup store probe, this breaks loudly;
upgrade to an app_factory_for_openapi path in ppi.server.app then.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ppi.server.app import openapi_schema


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("openapi/openapi.json"),
        help="Output path for the OpenAPI JSON file.",
    )
    args = parser.parse_args()

    schema = openapi_schema(Path("/nonexistent.duckdb"), Path("/nonexistent.lock"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())