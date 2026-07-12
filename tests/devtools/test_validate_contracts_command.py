import pytest
from click.testing import CliRunner

from ppi.devtools.cli import dev_group


def test_validate_contracts_writes_no_files(tmp_path, monkeypatch):
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    # Create minimal contract sources
    errors_dir = tmp_path / "contracts"
    errors_dir.mkdir()
    (errors_dir / "errors.yaml").write_text(
        "version: 1\n"
        "owner: backend\n"
        "errors:\n"
        "  - code: TEST_ERROR\n"
        "    category: client\n"
        "    defaultMessage: Test error.\n"
        "    retryable: false\n"
        "    stability: internal\n"
        "    description: Test.\n",
        encoding="utf-8",
    )

    src_ppi = tmp_path / "src" / "ppi" / "runtime"
    src_ppi.mkdir(parents=True)
    (src_ppi / "__init__.py").write_text("", encoding="utf-8")
    (src_ppi / "progress.py").write_text(
        "import msgspec\n"
        "class TestEvent(msgspec.Struct, frozen=True, tag='test_event'):\n"
        "    pass\n"
        "ProgressEvent = TestEvent\n",
        encoding="utf-8",
    )

    result = runner.invoke(dev_group, ["validate-contracts"])
    # May fail due to missing webview schema in tmp dir, but should not write any files
    generated_files = list(tmp_path.rglob("*.py")) + list(tmp_path.rglob("*.ts"))
    generated_in_output = [f for f in generated_files if "generated" in str(f)]
    assert len(generated_in_output) == 0
