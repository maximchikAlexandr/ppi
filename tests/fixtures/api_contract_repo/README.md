# API Contract Fixture Repository

This directory is a **contract fixture** for the runtime API conformance
command (`make api-runtime-contract`). It simulates a real Python project
with Git history so that Schemathesis and the ppi API server have
deterministic data to work with.

## Change Control

**Do not change this fixture for unrelated tests.** This fixture is the
baseline for spec 011 P0b runtime conformance. If you need different data
for a separate test, create a separate fixture.

If you must update this fixture, verify that:

1. `make api-runtime-contract` still passes.
2. Every existing OpenAPI example and enum value in `openapi/openapi.json`
   still matches the fixture data.
3. At least 3 commits, 2 Python modules, and 4 Python files remain.
