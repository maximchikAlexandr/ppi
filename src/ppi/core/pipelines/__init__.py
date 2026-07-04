"""Pipeline stage modules for the Python core analysis railway.

Each module defines one or more named stages following the ROP contract:
``StageInput -> StageResult[StageOutput, TypedStageError]``.

Stages are composed in ``odoo_project_analysis_pipeline`` and its
sibling pipelines.
"""
