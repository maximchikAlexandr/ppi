# Quickstart Validation: Non-Blocking Branch Analysis

Use a disposable repository with branches `dev` and `feature/test`.

On `feature/test`, create staged, unstaged, and untracked changes and record the branch, HEAD, diffs, status, and file hashes.

```bash
uv run ppi --repo /absolute/repository --branch dev analyze
uv run ppi --repo /absolute/repository --branch feature/test analyze
uv run ppi --repo /absolute/repository --branch feature/test analyze
```

Expected:

- every run uses the existing `.ppi/history.duckdb`;
- CLI analysis is executed by the workspace worker;
- switching the analyzed branch triggers an automatic rebuild, not a branch-mismatch error;
- the repeated `feature/test` run remains incremental;
- the active checkout and all recorded local changes remain unchanged.
