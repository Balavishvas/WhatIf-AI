from __future__ import annotations

from copy import deepcopy

from ..models import Scenario, StateSnapshot
from .state import WorldState


def _decision_type(decision: str) -> str:
    text = decision.lower()
    # Prioritize the core domain: "invest in learning AI" is a learning decision,
    # not a generic finance decision.
    if any(word in text for word in ("life insurance", "term insurance", "health insurance", "medical insurance", "insurance", "policy premium", "sum insured")):
        return "insurance"
    if any(word in text for word in ("bike", "motorcycle", "scooter", "car", "vehicle", "600cc", "600 cc")):
        return "vehicle"
    if any(word in text for word in ("learn", "learning", "study", "skill", "practice", "course", "knowledge", "ai", "project", "portfolio")):
        return "learning"
    if any(word in text for word in ("market", "advertis", "customer", "sales", "promotion")):
        return "marketing"
    if any(word in text for word in ("hire", "employee", "team", "staff")):
        return "hiring"
    if any(word in text for word in ("startup", "business", "quit", "career", "job", "resign")):
        return "career"
    if any(word in text for word in ("invest", "budget", "spend", "cost", "expense", "save", "saving")):
        return "finance"
    return "general"


def _branch_factor(branch: str) -> float:
    text = branch.lower()
    if any(word in text for word in ("pessimistic", "worst", "high risk")):
        return -0.5
    if any(word in text for word in ("aggressively", "aggressive", "rapidly", "intensive", "commit")):
        return 1.5
    if any(word in text for word in ("risk", "avoid", "reduce", "delay", "cautious", "conservative", "smaller workload")):
        return -0.5
    if any(word in text for word in ("optimistic", "strong", "focus", "pursue", "best", "increase")):
        return 1.5
    if any(word in text for word in ("balanced", "realistic", "moderate", "gradually", "part-time", "steady", "routine")):
        return 0.5
    if any(word in text for word in ("continue", "maintain", "current", "baseline", "keep")):
        return 0.0
    return 0.5


def _monthly_rate(key: str, decision_type: str) -> float:
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


def simulate(initial_state: dict[str, float], branch: str, months: int, decision: str = "") -> Scenario:
    state = WorldState(initial_state)
    timeline: list[StateSnapshot] = []
    decision_type = _decision_type(decision)
    factor = _branch_factor(branch)

    text_decision = decision.lower()
    if any(word in text_decision for word in ("bike", "motorcycle", "scooter", "car", "vehicle", "600cc", "600 cc")):
        # Only calculate values supplied by the user or explicitly extracted.
        # No local market prices, interest rates, insurance premiums, or mileage are invented.
        state.values.setdefault("vehicle_purchase_price_inr", 0.0)
        state.values.setdefault("down_payment_inr", 0.0)
        state.values.setdefault("monthly_fuel_cost_inr", 0.0)
        state.values.setdefault("monthly_maintenance_cost_inr", 0.0)
        state.values.setdefault("annual_insurance_cost_inr", 0.0)
        state.values.setdefault("monthly_emi_inr", 0.0)
        state.values.setdefault("monthly_ownership_cost_inr", 0.0)
        state.values.setdefault("upfront_cost_inr", 0.0)
        state.values["upfront_cost_inr"] = max(0.0, state.values["down_payment_inr"])
        state.values["monthly_ownership_cost_inr"] = max(0.0, state.values["monthly_fuel_cost_inr"] + state.values["monthly_maintenance_cost_inr"] + state.values["monthly_emi_inr"] + state.values["annual_insurance_cost_inr"] / 12.0)
        preferred_vehicle = ("vehicle_purchase_price_inr", "down_payment_inr", "monthly_emi_inr", "monthly_fuel_cost_inr", "monthly_maintenance_cost_inr", "annual_insurance_cost_inr", "monthly_ownership_cost_inr", "upfront_cost_inr")
        state.values = {key: state.values[key] for key in preferred_vehicle} | {key: value for key, value in state.values.items() if key not in preferred_vehicle}
        for month in range(1, months + 1):
            # Vehicle costs are treated as flat monthly budget estimates, not forecasts.
            updated = state.apply({})
            updated["cumulative_ownership_cost_inr"] = round(state.values["monthly_ownership_cost_inr"] * month + state.values["upfront_cost_inr"], 2)
            state.values["cumulative_ownership_cost_inr"] = updated["cumulative_ownership_cost_inr"]
            events = [
                "Ownership costs use only supplied or extracted values; missing values remain ₹0 placeholders, not estimates.",
                f"Modeled cumulative ownership cost: ₹{updated['cumulative_ownership_cost_inr']:,.0f} including stated upfront cost.",
            ]
            timeline.append(StateSnapshot(month=month, values=deepcopy(updated), events=events))
    elif decision_type == "learning":
        text = branch.lower()
        if any(word in text for word in ("intensive", "aggressive", "commit")):
            weekly_hours, project_rate, skill_rate, monthly_spend = 10.0, 0.75, 1.5, 1600.0
        elif any(word in text for word in ("cautious", "reduce", "smaller workload", "risk")):
            weekly_hours, project_rate, skill_rate, monthly_spend = 3.0, 0.25, 0.5, 400.0
        elif any(word in text for word in ("balanced", "steady", "gradually", "routine")):
            weekly_hours, project_rate, skill_rate, monthly_spend = 6.0, 0.5, 1.0, 800.0
        else:
            weekly_hours, project_rate, skill_rate, monthly_spend = 6.0, 0.4, 0.75, 700.0

        # Set a transparent illustrative baseline for a learning-specific scenario.
        state.values.setdefault("study_hours_per_week", 6.0)
        state.values.setdefault("projects_completed", 0.0)
        state.values.setdefault("skills_practiced", 0.0)
        state.values.setdefault("learning_budget_remaining_inr", 0.0)
        # Put the most useful learning outcomes first so compact UI cards show them.
        preferred = ("projects_completed", "skills_practiced", "study_hours_per_week", "learning_budget_remaining_inr")
        state.values = {key: state.values[key] for key in preferred} | {key: value for key, value in state.values.items() if key not in preferred}
        for month in range(1, months + 1):
            previous_budget = state.values["learning_budget_remaining_inr"]
            actual_spend = min(max(previous_budget, 0.0), monthly_spend)
            updated = state.apply({
                "study_hours_per_week": round(weekly_hours - state.values["study_hours_per_week"], 2),
                "projects_completed": project_rate,
                "skills_practiced": skill_rate,
                "learning_budget_remaining_inr": -actual_spend,
            })
            # Study hours represent the selected routine, not a cumulative total.
            updated["study_hours_per_week"] = weekly_hours
            state.values["study_hours_per_week"] = weekly_hours
            events = [
                f"Illustrative plan: {weekly_hours:g} study hours per week",
                f"Project progress: +{project_rate:g} project-equivalents this month",
                f"Learning spend: ₹{actual_spend:,.0f}; budget remaining ₹{updated['learning_budget_remaining_inr']:,.0f}",
            ]
            timeline.append(StateSnapshot(month=month, values=deepcopy(updated), events=events))
    else:
        for month in range(1, months + 1):
            changes = {
                key: round(value * _monthly_rate(key, decision_type) * factor, 2)
                for key, value in state.values.items()
            }
            updated = state.apply(changes)
            events = [
                f"{key} {'increased' if change > 0 else 'decreased' if change < 0 else 'stayed unchanged'} by {abs(change):g} "
                f"(illustrative starter rate {(_monthly_rate(key, decision_type) * factor * 100):g}%)"
                for key, change in changes.items()
            ]
            timeline.append(StateSnapshot(month=month, values=deepcopy(updated), events=events))

    return Scenario(name=branch.title(), assumption=branch, timeline=timeline)


def run_simulation(initial_state: dict[str, float], branches: list[str], months: int, decision: str = "") -> list[Scenario]:
    return [simulate(initial_state, branch, months, decision) for branch in branches]
