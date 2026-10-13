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

    extracted = extract_decision(request.decision, request.months)
    # Keep extracted domain metrics and let explicit UI values override matching keys.
    state = {**extracted.variables, **request.initial_state}
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

    assumptions = extracted.assumptions + [
        f"Scenario branch source: {branch_source}.",
        "Scenario changes use deterministic illustrative rules; learning metrics are plan scenarios, not predicted outcomes.",
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
    )
