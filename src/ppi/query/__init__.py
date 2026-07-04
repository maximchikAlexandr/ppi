"""FastAPI-free shared query dispatcher for the dashboard read surface."""

from __future__ import annotations

from ppi.query.dispatch import build_project_info, dispatch

__all__ = ["build_project_info", "dispatch"]
