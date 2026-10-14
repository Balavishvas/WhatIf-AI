from __future__ import annotations

import re
from typing import Any

DOMAIN_LABELS = {
    "stock_learning": "Stock-market learning",
    "learning": "Education and skill development",
    "education_career": "Education vs career",
    "vehicle": "Vehicle ownership",
    "home_finance": "Home purchase and mortgage",
    "life_insurance": "Life insurance",
    "health_insurance": "Health insurance",
    "insurance": "Insurance comparison",
    "business": "Business planning",
    "technology_future": "AI and technology disruption",
    "humor_absurd": "Humorous & Absurd Possibilities",
    "personal_finance": "Personal finance",
    "health_habit": "Health and habits",
    "general": "General decision",
}

METRIC_CATALOG: dict[str, list[dict[str, str]]] = {
    "stock_learning": [
        {"key": "study_hours_per_week", "label": "Study hours per week", "unit": "hours/week", "kind": "plan"},
        {"key": "learning_budget_inr", "label": "Learning budget (INR)", "unit": "INR", "kind": "input"},
        {"key": "learning_cost_inr", "label": "Cumulative learning spend (INR)", "unit": "INR", "kind": "cost"},
        {"key": "paper_trading_sessions", "label": "Paper-trading sessions", "unit": "sessions", "kind": "plan"},
        {"key": "strategies_tested", "label": "Strategies tested", "unit": "strategies", "kind": "plan"},
        {"key": "concepts_practiced", "label": "Concepts practiced", "unit": "concepts", "kind": "plan"},
    ],
    "learning": [
        {"key": "study_hours_per_week", "label": "Study hours per week", "unit": "hours/week", "kind": "plan"},
        {"key": "learning_cost_inr", "label": "Learning spend (INR)", "unit": "INR", "kind": "cost"},
        {"key": "projects_completed", "label": "Project milestones", "unit": "milestones", "kind": "plan"},
        {"key": "skills_practiced", "label": "Skills practiced", "unit": "skills", "kind": "plan"},
    ],
    "education_career": [
        {"key": "education_cost_inr", "label": "Education cost (INR)", "unit": "INR", "kind": "cost"},
        {"key": "monthly_take_home_inr", "label": "Monthly take-home pay (INR)", "unit": "INR", "kind": "input"},
        {"key": "study_hours_per_week", "label": "Study hours per week", "unit": "hours/week", "kind": "plan"},
        {"key": "work_experience_months", "label": "Work experience (months)", "unit": "months", "kind": "plan"},
    ],
    "home_finance": [
        {"key": "home_price_inr", "label": "Home price (INR)", "unit": "INR", "kind": "input"},
        {"key": "down_payment_inr", "label": "Down payment (INR)", "unit": "INR", "kind": "input"},
        {"key": "loan_amount_inr", "label": "Loan amount (INR)", "unit": "INR", "kind": "input"},
        {"key": "annual_interest_rate_pct", "label": "Annual interest rate (%)", "unit": "%", "kind": "input"},
        {"key": "loan_term_years", "label": "Loan term (years)", "unit": "years", "kind": "input"},
        {"key": "monthly_mortgage_payment_inr", "label": "Estimated monthly payment (INR)", "unit": "INR", "kind": "calculated"},
        {"key": "total_interest_paid_inr", "label": "Total interest over loan (INR)", "unit": "INR", "kind": "calculated"},
    ],
    "vehicle": [
        {"key": "vehicle_purchase_price_inr", "label": "Purchase price (INR)", "unit": "INR", "kind": "input"},
        {"key": "down_payment_inr", "label": "Down payment (INR)", "unit": "INR", "kind": "input"},
        {"key": "monthly_emi_inr", "label": "Monthly EMI (INR)", "unit": "INR", "kind": "cost"},
        {"key": "monthly_fuel_cost_inr", "label": "Monthly fuel (INR)", "unit": "INR", "kind": "cost"},
        {"key": "monthly_maintenance_cost_inr", "label": "Monthly maintenance (INR)", "unit": "INR", "kind": "cost"},
        {"key": "annual_insurance_cost_inr", "label": "Annual insurance (INR)", "unit": "INR", "kind": "cost"},
        {"key": "monthly_ownership_cost_inr", "label": "Monthly ownership cost (INR)", "unit": "INR", "kind": "calculated"},
        {"key": "cumulative_ownership_cost_inr", "label": "Cumulative ownership cost (INR)", "unit": "INR", "kind": "calculated"},
    ],
    "life_insurance": [
        {"key": "monthly_premium_inr", "label": "Monthly premium (INR)", "unit": "INR", "kind": "input"},
        {"key": "coverage_amount_inr", "label": "Coverage amount (INR)", "unit": "INR", "kind": "input"},
        {"key": "premium_share_of_income_pct", "label": "Premium share of income (%)", "unit": "%", "kind": "calculated"},
        {"key": "annual_premium_inr", "label": "Annual premium (INR)", "unit": "INR", "kind": "calculated"},
    ],
    "health_insurance": [
        {"key": "monthly_premium_inr", "label": "Monthly premium (INR)", "unit": "INR", "kind": "input"},
        {"key": "coverage_amount_inr", "label": "Sum insured (INR)", "unit": "INR", "kind": "input"},
        {"key": "deductible_inr", "label": "Deductible (INR)", "unit": "INR", "kind": "input"},
        {"key": "copay_pct", "label": "Co-pay (%)", "unit": "%", "kind": "input"},
        {"key": "annual_premium_inr", "label": "Annual premium (INR)", "unit": "INR", "kind": "calculated"},
    ],
    "insurance": [
        {"key": "monthly_premium_inr", "label": "Monthly premium (INR)", "unit": "INR", "kind": "input"},
        {"key": "coverage_amount_inr", "label": "Coverage amount (INR)", "unit": "INR", "kind": "input"},
        {"key": "annual_premium_inr", "label": "Annual premium (INR)", "unit": "INR", "kind": "calculated"},
    ],
    "business": [
        {"key": "revenue", "label": "Revenue", "unit": "currency/month", "kind": "input"},
        {"key": "cost", "label": "Operating costs", "unit": "currency/month", "kind": "input"},
        {"key": "customers", "label": "Customers", "unit": "customers", "kind": "input"},
        {"key": "cash_on_hand", "label": "Cash on hand", "unit": "currency", "kind": "input"},
        {"key": "monthly_net_cashflow", "label": "Modeled net cash flow", "unit": "currency/month", "kind": "calculated"},
    ],
    "personal_finance": [
        {"key": "monthly_income_inr", "label": "Monthly income (INR)", "unit": "INR", "kind": "input"},
        {"key": "monthly_expenses_inr", "label": "Monthly expenses (INR)", "unit": "INR", "kind": "input"},
        {"key": "savings_inr", "label": "Savings (INR)", "unit": "INR", "kind": "input"},
        {"key": "monthly_surplus_inr", "label": "Monthly surplus (INR)", "unit": "INR", "kind": "calculated"},
    ],
    "health_habit": [
        {"key": "habit_days_per_week", "label": "Planned days per week", "unit": "days/week", "kind": "plan"},
        {"key": "habit_sessions_completed", "label": "Sessions completed", "unit": "sessions", "kind": "plan"},
        {"key": "habit_cost_inr", "label": "Habit-related cost (INR)", "unit": "INR", "kind": "input"},
    ],
    "technology_future": [
        {"key": "productivity_index", "label": "Productivity Index (Base=100)", "unit": "index", "kind": "calculated"},
        {"key": "workforce_demand_pct", "label": "Workforce Demand (% vs baseline)", "unit": "%", "kind": "calculated"},
        {"key": "adoption_rate_pct", "label": "Technology Adoption Rate (%)", "unit": "%", "kind": "calculated"},
    ],
    "humor_absurd": [
        {"key": "survival_odds_pct", "label": "Survival Odds (%)", "unit": "%", "kind": "calculated"},
        {"key": "regret_index", "label": "Instant Regret Index", "unit": "index", "kind": "calculated"},
        {"key": "flex_score", "label": "Social Flex / Clout Score", "unit": "index", "kind": "calculated"},
        {"key": "financial_ruin_risk_pct", "label": "Total Ruin Risk (%)", "unit": "%", "kind": "calculated"},
    ],
    "general": [
        {"key": "trajectory_index", "label": "Trajectory Index (Base=100)", "unit": "index", "kind": "calculated"},
        {"key": "resource_load", "label": "Resource / Effort Load", "unit": "units", "kind": "cost"},
        {"key": "feasibility_pct", "label": "Feasibility & Stability (%)", "unit": "%", "kind": "plan"},
    ],
}


def classify_domain(decision: str) -> str:
    text = re.sub(r"\s+", " ", decision.lower()).strip()
    if any(p in text for p in (
        "kidney", "kideney", "sell organ", "sell my organ", "fight 100", "fight a bear", "fight a kangaroo",
        "marry chatgpt", "marry my robot", "zombie", "alien invasion", "rob a bank", "become a pirate",
        "eat 100", "only instant noodles", "fake my death", "punch a", "sleep for 10 years",
        "jump into a black hole"
    )):
        return "humor_absurd"
    if any(p in text for p in ("life insurance", "term insurance", "life cover", "life coverage")):
        return "life_insurance"
    if any(p in text for p in ("health insurance", "medical insurance", "mediclaim", "hospitalization cover")):
        return "health_insurance"
    if any(p in text for p in ("insurance", "policy premium", "sum insured", "deductible", "co-pay", "copay")):
        return "insurance"
    if any(p in text for p in ("stock market", "stock-market", "stock marketing", "stock trading", "day trading", "paper trading", "learn trading", "learning trading", "investing course", "technical analysis")):
        return "stock_learning"
    if any(p in text for p in ("undergraduate", "join ug", "college", "university", "degree", "get into job", "job after school", "workforce", "study or work", "study vs job")):
        return "education_career"
    if any(p in text for p in ("mortgage", "home loan", "house loan", "buy a house", "buy a home", "home purchase", "purchase a home", "buying a home", "buying a house", "10 year mortgage", "30 year mortgage")):
        return "home_finance"
    if any(p in text for p in ("motorcycle", "motorbike", "bike", "scooter", "car", "vehicle", "600 cc", "600cc", "commuting", "emi")):
        return "vehicle"
    if any(p in text for p in ("automate", "automation", "ai replaces", "ai automates", "future of work", "disrupt", "universal basic income", "ubi", "agi")):
        return "technology_future"
    if any(p in text for p in ("quit my job", "leave my job", "quit job", "resign")) and any(p in text for p in ("start", "build", "company", "startup", "business", "agency", "venture", "founder")):
        return "business"
    if any(p in text for p in ("business", "startup", "company", "firm", "agency", "venture", "saas", "customer", "revenue", "marketing", "sales", "hire", "employee", "founder", "client", "monetize")):
        return "business"
    if any(p in text for p in ("learn", "learning", "study", "skill", "course", "practice", "project", "portfolio", "certification", "education")):
        return "learning"
    if any(p in text for p in ("income", "salary", "savings", "saving", "budget", "expense", "spend", "debt", "loan", "invest")):
        return "personal_finance"
    if any(p in text for p in ("eat", "food", "diet", "exercise", "workout", "habit", "sleep", "fasting")):
        return "health_habit"
    return "general"


def domain_metadata(decision: str) -> dict[str, Any]:
    domain = classify_domain(decision)
    return {
        "domain": domain,
        "domain_label": DOMAIN_LABELS[domain],
        "metrics": METRIC_CATALOG[domain],
        "calculation_mode": "transparent formulas and explicitly labelled planning assumptions",
    }


def domain_assumptions(domain: str, values: dict[str, float]) -> list[str]:
    assumptions = [
        "Only values explicitly supplied or clearly extracted are treated as user inputs.",
        "Planning milestones and behavior rates are illustrative targets, not predictions.",
        "Missing prices, premiums, salaries, interest rates, policy terms and market returns are not inferred.",
    ]
    if domain in ("life_insurance", "health_insurance", "insurance"):
        if not values.get("monthly_premium_inr") or not values.get("coverage_amount_inr"):
            assumptions.append("Enter a real insurer quote and stated coverage amount before comparing cost and coverage numerically.")
        assumptions.append("Policy exclusions, waiting periods, underwriting and claim outcomes require the actual policy wording and insurer confirmation.")
    elif domain == "home_finance":
        required = ("loan_amount_inr", "annual_interest_rate_pct", "loan_term_years")
        if any(values.get(key, 0.0) <= 0 for key in required):
            assumptions.append("Mortgage payment and total interest are shown only when loan amount, annual interest rate and loan term are supplied. No market rate is assumed.")
        assumptions.append("The mortgage estimate uses a fixed-rate monthly repayment formula and excludes taxes, insurance, fees, variable-rate changes and early repayments.")
    elif domain == "vehicle":
        missing = [key for key in ("monthly_emi_inr", "monthly_fuel_cost_inr", "monthly_maintenance_cost_inr", "annual_insurance_cost_inr") if values.get(key, 0.0) <= 0]
        if missing:
            assumptions.append("Some ownership-cost inputs are missing; zero placeholders are not estimates.")
    elif domain == "education_career":
        assumptions.append("Employment, admission, salary and graduation outcomes are uncertain; any values are scenario inputs, not guarantees.")
    elif domain == "business":
        assumptions.append("Business trajectories use illustrative monthly rates selected by scenario wording; replace them with evidence-backed rates before relying on the comparison.")
        assumptions.append("Net cash flow is calculated from the supplied revenue and operating-cost figures; it does not include unprovided taxes, financing, working capital or one-off costs.")
    elif domain == "stock_learning":
        assumptions.append("No trading profit or investment return is forecast. Metrics represent learning plans and paper-trading practice only.")
    elif domain == "humor_absurd":
        assumptions.append("Biological organs are non-refundable and are not covered under AppleCare warranty.")
        assumptions.append("Darwin Awards eligibility is significantly heightened for this hypothetical branch.")
        assumptions.append("Purely satirical scenario simulation: do not trade vital organs or attempt dangerous stunts in reality.")
    return assumptions
