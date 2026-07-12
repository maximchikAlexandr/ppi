import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def script_path():
    p = Path("scripts/check_api_runtime_contract.sh")
    if not p.is_file():
        pytest.skip("script not found")
    return p.resolve()


def test_runtime_script_missing_schema_fails(tmp_path: Path, script_path: Path):
    result = subprocess.run(
        ["bash", str(script_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert "Schema" in result.stdout or "schema" in result.stdout.lower()


def test_runtime_script_missing_fixture_fails(tmp_path: Path, script_path: Path):
    # Create schema so it fails on fixture instead
    (tmp_path / "openapi").mkdir(parents=True)
    (tmp_path / "openapi" / "openapi.json").write_text("{}", encoding="utf-8")
    result = subprocess.run(
        ["bash", str(script_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert "Fixture" in result.stdout or "fixture" in result.stdout.lower()
