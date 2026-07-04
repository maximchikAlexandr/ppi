# History Store Fixtures

This directory contains representative `.ppi/history.duckdb` stores for
golden-output comparison and Ibis query migration testing.

## Layout

```
history_stores/
  README.md          — this file
  small/             — small repository fixture
  medium/            — medium repository fixture
  large/             — large repository fixture
```

Each subdirectory should contain a `.ppi/history.duckdb` file produced by
running `ppi analyze` on a representative repository with the current
baseline branch.

## Usage

Tests load fixtures via `store_path` resolution relative to each fixture root.
