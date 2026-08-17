# CLI Contract: Non-Blocking Branch Analysis

Existing syntax remains:

```text
ppi --repo PATH [--branch BRANCH] [--profile PROFILE] [--analysis-dir ROOT] COMMAND
```

- `--branch` selects an existing Git branch and defaults to the current branch.
- `--analysis-dir` retains its current temporary/runtime artifact behavior and does not relocate the repository store.
- An invalid branch fails before a store is created, cleared, or opened for writing.
- CLI analysis starts or attaches the existing workspace worker and sends mode, reason, and requested branch through the existing `analysis.start` IPC request; CLI does not write the store directly.
- Results continue to be written to and read from `<repo>/.ppi/history.duckdb`.
- Analysis uses committed branch history through the existing isolated checkout.
- If the store already contains the requested branch, analysis remains incremental.
- If it contains another branch, Inspector automatically rebuilds the same store for the requested branch.
- Automatic rebuild retains the existing destructive semantics; a failed rebuild does not guarantee preservation of the previous branch report.

The prior error `Branch changed from 'X' to 'Y'; rerun with --rebuild` is replaced by an automatic rebuild for `Y`. No new flag or client-side branch-store selection is introduced.

The branch field is required for CLI-originated analysis requests. The worker validates it before opening the store and does not substitute the worker process's current branch.
