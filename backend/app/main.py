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


@app.post("/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest) -> SimulationResponse:
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
