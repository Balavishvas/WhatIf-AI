from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env before importing modules that read GEMINI_API_KEY.
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ai.decision_extractor import extract_decision
from .ai.scenario_generator import generate_branches_with_source
from .models import SimulationRequest, SimulationResponse
from .engine.simulation import run_simulation
from .engine.domains import DOMAIN_LABELS, METRIC_CATALOG, classify_domain, domain_assumptions, domain_metadata

app = FastAPI(
    title="WhatIf AI",
    version="0.6.0",
    description="A stateful scenario simulation engine for exploring possible futures.",
)

# Allow the local static frontend to call the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/domains")
def domains() -> dict:
    """Return supported domains and metric definitions for the frontend."""
    return {"domains": [{"id": key, "label": label, "metrics": METRIC_CATALOG[key]} for key, label in DOMAIN_LABELS.items()]}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "whatif-ai"}


def _health_safety_notice(decision: str) -> str | None:
    """Avoid fake outcome simulations for potentially dangerous food restriction."""
    text = decision.lower()
    food_terms = ("eat", "food", "eating", "fast", "fasting", "starv", "meal", "calorie")
    restriction_terms = ("don't eat", "dont eat", "not eat", "no food", "without food", "stop eating", "skip meals", "starve", "fast for", "days without")
    if any(term in text for term in food_terms) and any(term in text for term in restriction_terms):
        return (
            "Going without food for several days can be dangerous. WhatIf AI cannot safely predict "
            "individual medical outcomes for this scenario. Please don't use this simulation to plan "
            "prolonged food restriction; speak with a healthcare professional before attempting a prolonged fast. "
            "If you have already gone without food and feel faint, confused, very weak, or unwell, seek urgent medical help."
        )
    return None


@app.post("/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest) -> SimulationResponse:
    safety_notice = _health_safety_notice(request.decision)
    if safety_notice:
        return SimulationResponse(
            decision=request.decision,
            scenarios=[],
            assumptions=["Health-sensitive request: generic numerical scenarios were intentionally not generated."],
            safety_notice=safety_notice,
            disclaimer="This tool does not provide medical advice or predict individual health outcomes.",
        )

    domain = classify_domain(request.decision)
    extracted = extract_decision(request.decision, request.months)
    # For typed domains, discard unrelated LLM-produced keys rather than showing
    # revenue/customer metrics on an insurance or learning decision.
    allowed_keys = {metric["key"] for metric in METRIC_CATALOG[domain]}
    allowed_keys.update({
        "annual_premium_inr", "premium_share_of_income_pct", "cumulative_premium_paid_inr",
        "monthly_income_inr", "monthly_expenses_inr", "savings_inr", "monthly_surplus_inr",
        "cumulative_education_cost_inr", "cumulative_earnings_inr", "habit_sessions_completed",
        "habit_cost_inr", "upfront_cost_inr",
    })
    extracted_variables = extracted.variables if domain in ("business", "general", "learning") else {
        key: value for key, value in extracted.variables.items() if key in allowed_keys
    }
    filtered_request_state = request.initial_state if domain in ("business", "general", "learning") else {
        key: value for key, value in request.initial_state.items() if key in allowed_keys
    }
    # Explicit user-entered values override extracted values.
    state = {**extracted_variables, **filtered_request_state}
    months = extracted.horizon_months or request.months

    if request.branches:
        branches = request.branches
        branch_source = "user-supplied branches"
    else:
        branches, branch_source = generate_branches_with_source(request.decision)

    scenarios = run_simulation(
        initial_state=state,
        branches=branches,
        months=months,
        decision=request.decision,
    )

    assumptions = extracted.assumptions + domain_assumptions(domain, state) + [
        f"Scenario branch source: {branch_source}.",
        "Scenario changes use domain-specific transparent formulas and illustrative planning targets; they are not forecasts.",
        "Scenario values are illustrative simulation outputs, not forecasts.",
    ]
    if not state:
        assumptions.append(
            "No numeric starting state was supplied or extracted; provide initial_state values for quantitative comparisons."
        )

    return SimulationResponse(
        decision=request.decision,
        scenarios=scenarios,
        assumptions=assumptions,
        domain=domain,
        domain_label=DOMAIN_LABELS[domain],
        metrics=METRIC_CATALOG[domain],
    )
