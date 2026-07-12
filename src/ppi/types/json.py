from __future__ import annotations

from typing import Any

JsonScalar = str | int | float | bool | None
JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject = dict[str, JsonValue]
JsonRows = list[JsonObject]
