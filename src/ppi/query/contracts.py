"""msgspec contracts for the read-only stdio JSON-RPC servant (``ppi rpc``)
and immutable query parameter models."""

from __future__ import annotations

from dataclasses import dataclass

import msgspec


class RpcRequest(msgspec.Struct, frozen=True, kw_only=True):
    method: str
    id: int = 0
    params: dict = {}


@dataclass(frozen=True)
class QueryParams:
    metric: str
    module_name: str | None = None
    file_path: str | None = None
    commit_hash: str | None = None
    agg: str = "mean"
    include_zero_score: bool = False
    metric_id: str | None = None
    level: str = "module"
    limit: int = 20
