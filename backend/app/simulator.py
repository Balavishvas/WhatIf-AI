from __future__ import annotations

from copy import deepcopy

from .models import Scenario, StateSnapshot


def _delta_for_branch(branch: str, key: str) -> float:
    """Small deterministic starter rules.

    The first version intentionally avoids pretending that these numbers are
    real-world predictions. They provide a stable simulation substrate that
    can later be replaced by domain-specific models or an LLM event engine.
    """
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


def simulate(
    initial_state: dict[str, float],
    branch: str,
    months: int,
) -> Scenario:
    state = deepcopy(initial_state)
    timeline: list[StateSnapshot] = []

    for month in range(1, months + 1):
        events: list[str] = []

        for key in list(state):
            change = _delta_for_branch(branch, key)
            state[key] = round(state[key] + change, 2)

            if change > 0:
                events.append(f"{key} increased by {change:g}")
            elif change < 0:
                events.append(f"{key} decreased by {abs(change):g}")

        timeline.append(
            StateSnapshot(
                month=month,
                values=deepcopy(state),
                events=events,
            )
        )

    return Scenario(
        name=branch.title(),
        assumption=branch,
        timeline=timeline,
    )


def run_simulation(
    initial_state: dict[str, float],
    branches: list[str],
    months: int,
) -> list[Scenario]:
    return [
        simulate(initial_state=initial_state, branch=branch, months=months)
        for branch in branches
    ]
