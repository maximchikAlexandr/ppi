# Feature Specification: Non-Blocking Branch Analysis

**Feature Branch**: `012-isolated-analysis-workspaces`

**Created**: 2026-08-17

**Updated**: 2026-08-17

**Status**: Draft

**Input**: User description: "Python Project Inspector must analyze any requested Git branch without requiring the user to switch the active project checkout away from the branch where they are working."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Analyze Any Branch Without Switching the User Checkout (Priority: P1)

As a developer, I can request analysis of any existing Git branch while continuing to work in any branch in my active checkout.

**Why this priority**: This is the complete functional goal. Analysis must not block normal development or require branch switching.

**Independent Test**: Keep the active checkout on one branch with local changes, analyze a different branch, and verify that analysis completes while the active branch and local changes remain unchanged.

**Acceptance Scenarios**:

1. **Given** the user is working on branch `feature/a`, **When** analysis is requested for `dev`, **Then** Inspector analyzes `dev` without switching the active checkout from `feature/a`.
2. **Given** the active checkout contains staged, unstaged, or untracked changes, **When** another branch is analyzed, **Then** those changes remain unchanged.
3. **Given** the shared analysis store contains another branch, **When** a different branch is analyzed, **Then** Inspector refreshes that store for the requested branch without requiring the user to pass `--rebuild`.
4. **Given** the requested branch does not exist, **When** analysis is started, **Then** Inspector stops before changing analysis data and reports that the branch cannot be resolved.

### Edge Cases

- The active checkout and requested branch are the same.
- The active checkout is dirty.
- The requested branch is already checked out in another linked worktree.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The user MUST be able to select any existing Git branch for analysis.
- **FR-002**: Inspector MUST analyze the selected branch in an isolated checkout and MUST NOT switch, reset, clean, stash, stage, or otherwise modify the user's active checkout.
- **FR-003**: Inspector MUST continue writing analysis results to the repository's existing `.ppi/history.duckdb` so current clients can discover the report without a new selection mechanism.
- **FR-004**: When the existing store belongs to another branch, Inspector MUST automatically rebuild that same store for the requested branch instead of returning a branch-mismatch error.
- **FR-005**: Repeated analysis of the branch currently stored MUST remain incremental.
- **FR-007**: Inspector MUST validate that the requested branch exists before creating or clearing analysis data.
- **FR-008**: CLI analysis MUST execute through the workspace worker, and the worker MUST be the only owner that writes the repository store.
- **FR-009**: The requested branch MUST be carried unchanged through the existing worker analysis request and used by the worker instead of resolving its own current branch.

### Key Entities

- **Analysis Store**: The existing repository-local `.ppi/history.duckdb`, containing the report for the most recently analyzed branch.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of automated safety scenarios, analysis leaves the active branch, index, tracked changes, and untracked files unchanged.
- **SC-002**: A user can analyze a different branch with one command and without running `git switch`, `git checkout`, `git stash`, or `--rebuild`.
- **SC-003**: Sequential analysis of two branches succeeds without a manual rebuild; after each run the existing store identifies and reports the requested branch.
- **SC-004**: An invalid branch fails before any existing result store is changed.

## Assumptions

- Analysis covers committed Git history only; staged, unstaged, and untracked content is not included.
- When no branch is provided, Inspector analyzes the current branch.
- Existing detached-worktree history analysis remains the isolation mechanism unless implementation research finds a smaller equivalent native Git mechanism.
- The store contains one branch report at a time; preserving or comparing several branch reports simultaneously is outside this feature.
- `--analysis-dir` continues to control temporary runtime/worktree artifacts and does not relocate the repository-local store.
- The unchanged `.ppi/history.duckdb` path preserves compatibility with existing report consumers; migration of their read flows is outside this feature.
- Automatic branch switching uses the existing destructive rebuild semantics: once rebuild starts, the previous branch report is not guaranteed to remain available if the new analysis fails.
- Tags, arbitrary commit SHAs, remote cloning, submodule initialization, and analysis of uncommitted changes are outside this feature.
