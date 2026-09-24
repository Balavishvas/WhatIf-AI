from __future__ import annotations

from copy import deepcopy


class WorldState:
    """Mutable simulation state with explicit numeric variables."""

    def __init__(self, values: dict[str, float] | None = None):
        self.values = deepcopy(values or {})

    def apply(self, changes: dict[str, float]) -> dict[str, float]:
        for key, delta in changes.items():
            self.values[key] = round(self.values.get(key, 0.0) + delta, 2)
        return deepcopy(self.values)

    def snapshot(self) -> dict[str, float]:
        return deepcopy(self.values)
