# Research: Non-Blocking Branch Analysis

## Decision

Keep the existing detached worktree and `<repo>/.ppi/history.duckdb`. Route CLI analysis through the existing worker, add the requested branch to the existing `analysis.start` payload, bind that worker to the repository store, and automatically use the existing rebuild path when the requested branch differs from the stored branch.

## Rationale

This is the smallest constitution-compliant change that leaves the user's checkout untouched, keeps the worker as the only writer, and keeps the report visible to existing VS Code/dashboard clients.

## Alternative Rejected

Separate branch stores would require workspace selection and client changes. Multi-branch data in one store would require schema and query changes. Preserving the old report through a failed rebuild would require a second candidate store. None is required when existing destructive rebuild semantics and the latest requested branch report are sufficient.
