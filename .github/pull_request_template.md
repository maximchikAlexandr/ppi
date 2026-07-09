<!--
Thanks for opening a PR. Please fill out the sections below; the
template is intentionally lightweight so it does not become busywork.
If a section does not apply, write "n/a".
-->

## Summary

What does this PR do, and why? One short paragraph is enough.

## Spec / issue

- [ ] Linked issue (`Fixes #…`) or spec ticket (`Spec 010`).
- [ ] If the change is contract-affecting, linked the OpenAPI baseline
      bump: `make api-bump-baseline` + a note in `frontend/MIGRATION.md`.

## Generic / legacy split

- [ ] New generic code goes into `frontend/src/components/generic/**`,
      `domain/**`, `registry/**`, or `utils/**`. No new files in
      `frontend/src/components/` outside `generic/`.
- [ ] If a legacy file was added or kept, it is on the boundary
      scanner's exemption list and tracked in `MIGRATION.md`.

## Deleted / deprecated code

- [ ] Removed all obsolete files, fixtures, and tests in the same
      commit. Knip is clean (`make check`).
- [ ] If the PR adds an adapter or helper, it does not duplicate an
      existing one. Cross-checked with `frontend/MIGRATION.md`.

## Tests

- [ ] `npm run check:all` exits 0.
- [ ] `make api-contract` exits 0 (lint + types + diff + boundaries +
      freshness).
- [ ] New behaviour is covered by a focused test. Tests assert
      **real** behaviour, not just "no crash" (e.g. assert the D3
      simulation actually moved nodes, not only that `nodes.length`
      is correct).
- [ ] If a new contract fixture was added (unknown entity kind,
      unknown metric, unknown relation, unknown line category,
      unknown table column, unknown query result kind), it is exercised
      by at least one test.

## Size / coupling budget

- [ ] `make size-budget` exits 0. If the bundle grew, the chunk size
      is below the configured limit (default 900 kB) and any new
      dependency is justified in the PR description.
- [ ] No new cross-page imports; the page that owns the new hook
      also consumes it. No circular module references.

## Migrations

- [ ] If the contract changed, `openapi/openapi.json` and
      `frontend/src/api/generated/schema.d.ts` are both committed
      in the same PR.
- [ ] If a new forbidden token is unavoidable in a generic file
      (rare), the scanner's exemption list and `MIGRATION.md` are
      updated in the same PR.
- [ ] If a new dependency was added, it is justified in the PR
      description (why, alternatives considered, lockfile
      implications).

## Checklist before merge

- [ ] `make api-contract` green
- [ ] `npm run check:all` green
- [ ] `make size-budget` green
- [ ] `make api-freshness` green (no uncommitted contract drift)
- [ ] At least one other reviewer (the spec does not require a
      formal approval, but no PR merges into `main` without a
      second pair of eyes on a contract change)
