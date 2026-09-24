from __future__ import annotations

from copy import deepcopy

from ..models import Scenario, StateSnapshot
from .state import WorldState


def _delta_for_branch(branch: str, key: str) -> float:
    text = branch.lower()
    if "strong" in text or "focus" in text or "pursue" in text:
        if "skill" in key or "ai" in key or "knowledge" in key:
            return 8.0
        if "web" in key:
            return -2.0
    if "balanced" in text:
        return 4.0
    if "continue" in text:
        return 2.0
    return 1.0


def simulate(initial_state: dict[str, float], branch: str, months: int) -> Scenario:
    state = WorldState(initial_state)
    timeline: list[StateSnapshot] = []

    for month in range(1, months + 1):
        changes = {key: _delta_for_branch(branch, key) for key in state.values}
        updated = state.apply(changes)
        events = [
            f"{key} {'increased' if change > 0 else 'decreased'} by {abs(change):g}"
            for key, change in changes.items()
            if change != 0
        ]
        timeline.append(
            StateSnapshot(month=month, values=deepcopy(updated), events=events)
        )

    return Scenario(name=branch.title(), assumption=branch, timeline=timeline)


def run_simulation(initial_state: dict[str, float], branches: list[str], months: int):
    return [simulate(initial_state, branch, months) for branch in branches]
