from __future__ import annotations

from copy import deepcopy

from ..models import Scenario, StateSnapshot
from .state import WorldState


def _decision_type(decision: str) -> str:
    text = decision.lower()
    if any(word in text for word in ("market", "advertis", "customer", "sales", "promotion")):
        return "marketing"
    if any(word in text for word in ("invest", "budget", "spend", "cost", "expense", "save", "saving")):
        return "finance"
    if any(word in text for word in ("learn", "study", "skill", "practice", "course", "knowledge", "ai")):
        return "learning"
    if any(word in text for word in ("hire", "employee", "team", "staff")):
        return "hiring"
    if any(word in text for word in ("startup", "business", "quit", "career", "job", "resign")):
        return "career"
    return "general"


def _branch_factor(branch: str) -> float:
    """Translate scenario wording into a transparent multiplier for starter rates."""
    text = branch.lower()
    if any(word in text for word in ("pessimistic", "worst", "high risk", "aggressively", "aggressive", "rapidly")):
        return 1.5 if any(word in text for word in ("aggressively", "aggressive", "rapidly")) else -0.5
    if any(word in text for word in ("risk", "avoid", "reduce", "delay", "cautious", "conservative")):
        return -0.5
    if any(word in text for word in ("optimistic", "strong", "focus", "pursue", "best", "increase", "intensive")):
        return 1.5
    if any(word in text for word in ("balanced", "realistic", "moderate", "gradually", "part-time", "steady")):
        return 0.5
    if any(word in text for word in ("continue", "maintain", "current", "baseline", "keep")):
        return 0.0
    return 0.5


def _monthly_rate(key: str, decision_type: str) -> float:
    """Starter monthly rate by metric and decision domain; not a real-world forecast."""
    name = key.lower()
    if decision_type == "marketing":
        if any(word in name for word in ("revenue", "sales")):
            return 0.08
        if any(word in name for word in ("customer", "user")):
            return 0.10
        if any(word in name for word in ("cost", "expense", "spend")):
            return 0.06
        return 0.02
    if decision_type == "finance":
        if any(word in name for word in ("revenue", "income", "profit")):
            return 0.03
        if any(word in name for word in ("cost", "expense", "debt")):
            return -0.05
        return 0.02
    if decision_type == "learning":
        return 0.10 if any(word in name for word in ("skill", "knowledge", "ai", "productivity")) else 0.02
    if decision_type == "hiring":
        if any(word in name for word in ("capacity", "productivity", "output")):
            return 0.08
        if any(word in name for word in ("cost", "expense", "salary")):
            return 0.07
        return 0.02
    if decision_type == "career":
        if any(word in name for word in ("revenue", "income", "salary", "runway", "saving", "savings")):
            return 0.04
        if any(word in name for word in ("cost", "expense", "burn")):
            return 0.05
        if any(word in name for word in ("customer", "user", "traction")):
            return 0.04
        return 0.02
    return 0.03


def _monthly_changes(
    state: dict[str, float],
    decision_type: str,
    factor: float,
) -> dict[str, float]:
    changes: dict[str, float] = {}
    for key, value in state.items():
        rate = _monthly_rate(key, decision_type)
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
            f"{key} {'increased' if change > 0 else 'decreased' if change < 0 else 'stayed unchanged'} by {abs(change):g} "
            f"(starter rate {(_monthly_rate(key, decision_type) * factor * 100):g}% for this scenario)"
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
    return [simulate(initial_state, branch, months, decision) for branch in branches]
