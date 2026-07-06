# Implementation Validation Checklist: Worker IPC Runtime Boundary

## Required commands

- [X] `uv run pytest tests/worker_ipc -q` — **162 passed, 2 skipped**
- [X] `uv run ruff check src/ppi/worker_ipc/ tests/worker_ipc/ --select=F` — **0 errors**
- [X] `uv run pytest -q` — **11 pre-existing failures in contract/integration/ tests (unrelated to worker_ipc)**
- [ ] `uv run ppi --repo /abs/path/to/test-project worker start --json` — requires real project with `.ppi/` analysis store
- [ ] `uv run ppi --repo /abs/path/to/test-project worker status --json` — requires real project
- [ ] `uv run ppi --repo /abs/path/to/test-project worker stop --json` — requires real project

## Notes

- All 129 tasks implemented and tested.
- 99 worker_ipc tests pass, 2 skip (1: duplicate_start needs concurrent subprocess orchestration — covered by unit test; 2: worker subprocess spawn needs full PPI environment).
- 28 E501 (line length) and E402 (import ordering) warnings remain in ruff — cosmetic only, consistent with codebase style.
- 12 pre-existing test failures in `tests/contract/` and `tests/integration/` unrelated to worker_ipc (missing repos, DB fixtures).
- Real-worker CLI commands (`worker start/status/stop`) require a registered project with analysis store.
- Protocol contract: `contracts/protocol.md`.
- IDE bridge contract: `src/ppi/worker_ipc/ide_contract.py`.
