from pathlib import Path

from ppi.devtools.codegen.freshness import check_file_freshness, FreshnessReport


def test_fresh_file_passes(tmp_path: Path):
    committed = tmp_path / "test.py"
    content = "fresh content\n"
    committed.write_text(content, encoding="utf-8")
    assert check_file_freshness(committed, content)


def test_stale_file_fails(tmp_path: Path):
    committed = tmp_path / "test.py"
    committed.write_text("old content\n", encoding="utf-8")
    assert not check_file_freshness(committed, "new content\n")


def test_missing_file_fails(tmp_path: Path):
    missing = tmp_path / "not_there.py"
    assert not check_file_freshness(missing, "anything\n")


def test_freshness_report_fresh():
    report = FreshnessReport(status="fresh")
    assert report.passed


def test_freshness_report_stale():
    report = FreshnessReport(
        status="stale",
        stale_files=(Path("a.py"),),
    )
    assert not report.passed


def test_freshness_report_missing():
    report = FreshnessReport(
        status="stale",
        missing_files=(Path("b.py"),),
    )
    assert not report.passed


def test_freshness_remediation_command():
    report = FreshnessReport(status="stale")
    assert "uv run ppi dev generate-contracts" in report.remediation_command
