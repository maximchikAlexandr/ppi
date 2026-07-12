# Contract: Typing and Import Boundaries

## P0 blocking mypy scope

`make mypy-p0` must check only:

```text
src/ppi/generated
src/ppi/devtools/codegen
src/ppi/runtime/progress.py
src/ppi/contracts
src/ppi/devtools/cli.py
```

Missing paths are skipped with a clear message. Existing paths with type errors fail the command.

## Whole-project mypy

Whole-project mypy is outside the spec 011 CI contract and MUST NOT be added as a required gate.

## Import Linter P1 scope

Add `.importlinter` in P1 as a report-only command whose exit status is recorded but normalized to success for the CI job; upload its textual report as a CI artifact.

Initial contracts:

```text
ppi.generated must not import ppi.query, ppi.server, ppi.runtime, ppi.storage
ppi.runtime, ppi.server, ppi.query, ppi.storage must not import ppi.devtools.codegen
ppi.storage must not import ppi.server
```

Import Linter MUST NOT become blocking in spec 011. A separate future specification must define prerequisites, remediation, and the blocking transition.
