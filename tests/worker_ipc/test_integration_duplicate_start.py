"""Integration test: duplicate worker start prevention (T066)."""


import pytest


@pytest.mark.skip(reason="Requires concurrent subprocess orchestration; covered by test_gateway_race.py at unit level")
def test_concurrent_start_returns_one_worker_id() -> None:
    """Two concurrent worker start calls return one worker id.

    This is tested at the unit level in test_gateway_race.py
    via mocked Supervisor. A full integration test would require
    real subprocess concurrency orchestration.
    """
    pass
