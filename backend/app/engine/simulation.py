from __future__ import annotations

from copy import deepcopy

from ..models import Scenario, StateSnapshot
from .state import WorldState


def _decision_type(decision: str) -> str:
    text = decision.lower()

    if any(word in text for word in ("market", "advertis", "customer", "sales", "promotion")):
        return "marketing"
    if any(word in text for word in ("invest", "budget", "spend", "cost", "expense")):
        return "finance"
    if any(word in text for word in ("learn", "study", "skill", "practice", "course", "knowledge", "ai")):
        return "learning"
    if any(word in text for word in ("hire", "employee", "team", "staff")):
        return "hiring"
    return "general"


def _branch_factor(branch: str) -> float:
    text = branch.lower()

    if any(word in text for word in ("pessimistic", "worst", "risk", "avoid")):
        return -0.5
    if any(word in text for word in ("optimistic", "strong", "focus", "pursue", "best")):
        return 1.5
    if any(word in text for word in ("balanced", "realistic", "moderate")):
        return 0.5
    if "continue" in text:
        return 0.0
    return 0.5


def _monthly_changes(
    state: dict[str, float],
    decision_type: str,
    factor: float,
) -> dict[str, float]:
    changes: dict[str, float] = {}

    for key, value in state.items():
        name = key.lower()

        if decision_type == "marketing":
            if any(word in name for word in ("revenue", "sales")):
                rate = 0.08
            elif any(word in name for word in ("customer", "user")):
                rate = 0.10
            elif any(word in name for word in ("cost", "expense", "spend")):
                rate = 0.06
            else:
                rate = 0.02
        elif decision_type == "finance":
            if any(word in name for word in ("revenue", "income", "profit")):
                rate = 0.03
            elif any(word in name for word in ("cost", "expense", "debt")):
                rate = -0.05
            else:
                rate = 0.02
        elif decision_type == "learning":
            rate = (
                0.10
                if any(word in name for word in ("skill", "knowledge", "ai", "productivity"))
                else 0.02
            )
        elif decision_type == "hiring":
            if any(word in name for word in ("capacity", "productivity", "output")):
                rate = 0.08
            elif any(word in name for word in ("cost", "expense", "salary")):
                rate = 0.07
            else:
                rate = 0.02
        else:
            rate = 0.03

        changes[key] = round(value * rate * factor, 2)

    return changes


def simulate(
    initial_state: dict[str, float],
    branch: str,
    months: int,
    decision: str = "",
) -> Scenario:
    state = WorldState(initial_state)
    timeline: list[StateSnapshot] = []
    decision_type = _decision_type(decision)
    factor = _branch_factor(branch)

    for month in range(1, months + 1):
        changes = _monthly_changes(state.values, decision_type, factor)
        updated = state.apply(changes)
        events = [
            f"{key} {'increased' if change > 0 else 'decreased' if change < 0 else 'stayed unchanged'} by {abs(change):g}"
            for key, change in changes.items()
        ]
        timeline.append(
            StateSnapshot(month=month, values=deepcopy(updated), events=events)
        )

    return Scenario(name=branch.title(), assumption=branch, timeline=timeline)


def run_simulation(
    initial_state: dict[str, float],
    branches: list[str],
    months: int,
    decision: str = "",
) -> list[Scenario]:
    return [
        simulate(initial_state, branch, months, decision)
        for branch in branches
    ]
