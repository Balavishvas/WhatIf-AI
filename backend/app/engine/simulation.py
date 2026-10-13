from __future__ import annotations

from copy import deepcopy

from ..models import Scenario, StateSnapshot
from .state import WorldState
from .domains import classify_domain


def _decision_type(decision: str) -> str:
    text = decision.lower()
    domain = classify_domain(decision)
    if domain in ("stock_learning", "education_career", "life_insurance", "health_insurance", "insurance", "personal_finance", "health_habit", "vehicle"):
        return domain
    if domain == "business":
        if any(word in text for word in ("quit", "resign", "career", "job", "startup")):
            return "career"
        if any(word in text for word in ("hire", "employee", "team", "staff")):
            return "hiring"
        if any(word in text for word in ("market", "advertis", "sales", "promotion")):
            return "marketing"
        return "career"
    if any(word in text for word in ("learn", "learning", "study", "skill", "practice", "course", "knowledge", "ai", "project", "portfolio")):
        return "learning"
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
    elif decision_type == "stock_learning":
        # No profit, return, or trading win-rate prediction: only learning-plan milestones.
        branch_text = branch.lower()
        if any(word in branch_text for word in ("paper trading", "without immediate financial risk", "cautious", "risk")):
            hours, sessions, strategies, concepts, spend = 4.0, 8.0, 1.0, 2.0, 500.0
        elif any(word in branch_text for word in ("course", "certification", "structured")):
            hours, sessions, strategies, concepts, spend = 6.0, 4.0, 1.0, 3.0, 1800.0
        elif any(word in branch_text for word in ("day trading", "intensive", "aggressive")):
            hours, sessions, strategies, concepts, spend = 10.0, 12.0, 2.0, 3.0, 1200.0
        else:
            hours, sessions, strategies, concepts, spend = 6.0, 6.0, 1.0, 2.0, 700.0
        state.values.setdefault("study_hours_per_week", 0.0)
        state.values.setdefault("paper_trading_sessions", 0.0)
        state.values.setdefault("strategies_tested", 0.0)
        state.values.setdefault("concepts_practiced", 0.0)
        state.values.setdefault("learning_budget_inr", 0.0)
        state.values.setdefault("learning_cost_inr", 0.0)
        for month in range(1, months + 1):
            budget = state.values["learning_budget_inr"]
            actual_spend = min(max(budget, 0.0), spend) if budget > 0 else spend
            updated = state.apply({
                "paper_trading_sessions": sessions,
                "strategies_tested": strategies,
                "concepts_practiced": concepts,
                "learning_cost_inr": actual_spend,
                "learning_budget_inr": -actual_spend if budget > 0 else 0.0,
            })
            updated["study_hours_per_week"] = hours
            state.values["study_hours_per_week"] = hours
            events = [
                f"Illustrative learning plan: {hours:g} study hours per week.",
                f"Practice target: {sessions:g} paper-trading sessions and {strategies:g} strategy tests this month.",
                f"Illustrative learning spend: ₹{actual_spend:,.0f} this month.",
                "No trading profits, market returns, or win rates are predicted.",
            ]
            timeline.append(StateSnapshot(month=month, values=deepcopy(updated), events=events))
    elif decision_type == "education_career":
        branch_text = branch.lower()
        study_path = any(word in branch_text for word in ("study", "college", "undergraduate", "degree", "academic"))
        work_path = any(word in branch_text for word in ("workforce", "job", "work while", "career", "employment"))
        hybrid = any(word in branch_text for word in ("part-time", "hybrid", "while working"))
        state.values.setdefault("education_cost_inr", 0.0)
        state.values.setdefault("monthly_take_home_inr", 0.0)
        state.values.setdefault("study_hours_per_week", 0.0)
        state.values.setdefault("work_experience_months", 0.0)
        state.values.setdefault("cumulative_education_cost_inr", 0.0)
        state.values.setdefault("cumulative_earnings_inr", 0.0)
        for month in range(1, months + 1):
            tuition_monthly = max(0.0, state.values["education_cost_inr"]) / max(months, 1) if study_path else 0.0
            earnings = max(0.0, state.values["monthly_take_home_inr"]) if work_path or hybrid else 0.0
            updated = state.apply({
                "cumulative_education_cost_inr": tuition_monthly,
                "cumulative_earnings_inr": earnings,
                "work_experience_months": 1.0 if work_path or hybrid else 0.0,
            })
            updated["study_hours_per_week"] = 6.0 if hybrid else 12.0 if study_path else 0.0
            state.values["study_hours_per_week"] = updated["study_hours_per_week"]
            events = [
                f"Modeled education cost this month: ₹{tuition_monthly:,.0f} from the supplied total-cost input." if study_path else "No education cost was applied to this work-first path.",
                f"Modeled take-home earnings this month: ₹{earnings:,.0f} from the supplied monthly-pay input.",
                "Admission, graduation, hiring and future salary are not predicted.",
            ]
            timeline.append(StateSnapshot(month=month, values=deepcopy(updated), events=events))
    elif decision_type in ("life_insurance", "health_insurance", "insurance"):
        # Policy details are user-provided quote inputs. Never invent benefits or claim outcomes.
        state.values.setdefault("monthly_premium_inr", 0.0)
        state.values.setdefault("coverage_amount_inr", 0.0)
        state.values.setdefault("annual_premium_inr", 0.0)
        if state.values["annual_premium_inr"] <= 0 and state.values["monthly_premium_inr"] > 0:
            state.values["annual_premium_inr"] = round(state.values["monthly_premium_inr"] * 12, 2)
        if state.values.get("monthly_income_inr", 0.0) > 0 and state.values["monthly_premium_inr"] > 0:
            state.values["premium_share_of_income_pct"] = round(state.values["monthly_premium_inr"] / state.values["monthly_income_inr"] * 100, 2)
        for month in range(1, months + 1):
            updated = state.snapshot()
            updated["cumulative_premium_paid_inr"] = round(state.values["monthly_premium_inr"] * month, 2)
            events = [
                f"Cumulative premium at the supplied monthly quote: ₹{updated['cumulative_premium_paid_inr']:,.0f}.",
                "Coverage, exclusions, waiting periods, underwriting and claim decisions depend on the actual policy and insurer.",
                "A missing premium or coverage amount remains unknown; zero is a placeholder, not an estimate.",
            ]
            timeline.append(StateSnapshot(month=month, values=deepcopy(updated), events=events))
    elif decision_type == "personal_finance":
        state.values.setdefault("monthly_income_inr", 0.0)
        state.values.setdefault("monthly_expenses_inr", 0.0)
        state.values.setdefault("savings_inr", 0.0)
        state.values["monthly_surplus_inr"] = round(state.values["monthly_income_inr"] - state.values["monthly_expenses_inr"], 2)
        for month in range(1, months + 1):
            surplus = state.values["monthly_surplus_inr"]
            updated = state.apply({"savings_inr": surplus})
            events = [f"Modeled savings change by ₹{surplus:,.0f} using supplied monthly income and expenses."]
            timeline.append(StateSnapshot(month=month, values=deepcopy(updated), events=events))
    elif decision_type == "health_habit":
        branch_text = branch.lower()
        target = 3.0 if any(word in branch_text for word in ("cautious", "gradual", "reduce")) else 5.0 if any(word in branch_text for word in ("intensive", "daily", "aggressive")) else 4.0
        state.values.setdefault("habit_days_per_week", 0.0)
        state.values.setdefault("habit_sessions_completed", 0.0)
        state.values.setdefault("habit_cost_inr", 0.0)
        for month in range(1, months + 1):
            updated = state.apply({"habit_sessions_completed": target * 4.0, "habit_cost_inr": max(0.0, state.values["habit_cost_inr"])})
            updated["habit_days_per_week"] = target
            state.values["habit_days_per_week"] = target
            timeline.append(StateSnapshot(month=month, values=deepcopy(updated), events=[f"Illustrative habit target: {target:g} days per week.", "Actual health effects are individual and are not predicted."]))
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
        state.values.setdefault("learning_budget_inr", 0.0)
        state.values.setdefault("learning_cost_inr", 0.0)
        # Put domain-relevant learning outcomes first for the cards and chart.
        preferred = ("projects_completed", "skills_practiced", "study_hours_per_week", "learning_cost_inr", "learning_budget_inr")
        state.values = {key: state.values[key] for key in preferred} | {key: value for key, value in state.values.items() if key not in preferred}
        for month in range(1, months + 1):
            available_budget = state.values["learning_budget_inr"]
            actual_spend = min(max(available_budget, 0.0), monthly_spend) if available_budget > 0 else monthly_spend
            updated = state.apply({
                "study_hours_per_week": round(weekly_hours - state.values["study_hours_per_week"], 2),
                "projects_completed": project_rate,
                "skills_practiced": skill_rate,
                "learning_cost_inr": actual_spend,
                "learning_budget_inr": -actual_spend if available_budget > 0 else 0.0,
            })
            # Study hours represent the selected routine, not a cumulative total.
            updated["study_hours_per_week"] = weekly_hours
            state.values["study_hours_per_week"] = weekly_hours
            events = [
                f"Illustrative plan: {weekly_hours:g} study hours per week",
                f"Project progress: +{project_rate:g} project-equivalents this month",
                f"Illustrative learning spend this month: ₹{actual_spend:,.0f}; remaining supplied budget ₹{updated['learning_budget_inr']:,.0f}",
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
