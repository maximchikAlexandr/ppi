# Source Notes

- User request: create the 8th specification for ROP migration in `https://github.com/maximchikAlexandr/ppi`.
- User-provided pipeline map identifies the main backend axis as history walk -> Odoo project analysis -> discovery/enrichment/provider/edges/export and the frontend/VS Code bridge axes.
- Public GitHub repository page confirms project structure includes Python source under `src/ppi`, TypeScript frontend under `frontend`, VS Code extension under `vscode-extension`, and existing `specs` directory.


## Plan research sources

- Public GitHub repository page confirmed mixed Python/TypeScript layout, CLI commands, dashboard frontend, VS Code extension, JSON progress stream, JSON-RPC read surface, DuckDB history store, and language split.
- Local project constitution and `pyproject.toml` confirmed `Expression` as the Python Result/Option/pipe dependency.
- Effect documentation confirmed typed workflow values that can succeed or fail, typed error/context tracking, and relevant docs for error management, resource management, streams, schema, concurrency, and building pipelines.
- `fp-ts` and `neverthrow` were considered but rejected for this feature to avoid multiple TypeScript FP vocabularies beside `Effect`.

## Analyze/checklist verification notes

- Public GitHub repository view shows root folders/files including `frontend`, `src/ppi`, `tests`, `vscode-extension`, `pyproject.toml`, and README.
- Public `src/ppi` tree shows current Python package folders including `adapters`, `cli`, `core`, `history`, `query`, `runtime`, `server`, and `storage`; no `src/ppi/analysis` folder was visible.
- Public `frontend/src` tree shows current frontend folders including `api`, `components`, `domain`, `pages`, `registry`, `transforms`, and `utils`; no `frontend/src/features` or `frontend/src/lib` folder was visible.
- Public `frontend/src/api` tree shows `client.ts`, `dataSource.ts`, `schemas.ts`, and related tests, so frontend API pipeline tasks were moved under `frontend/src/api`.
