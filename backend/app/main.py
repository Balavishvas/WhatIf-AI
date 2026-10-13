from fastapi import FastAPI

from .ai.decision_extractor import extract_decision
from .ai.scenario_generator import generate_branches, scenario_generation_mode
from .models import SimulationRequest, SimulationResponse
from .engine.simulation import run_simulation

app = FastAPI(
    title="WhatIf AI",
    version="0.4.0",
    description="A stateful scenario simulation engine for exploring possible futures.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "whatif-ai"}


@app.post("/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest) -> SimulationResponse:
    extracted = extract_decision(request.decision, request.months)
    state = request.initial_state or extracted.variables
    months = extracted.horizon_months or request.months
    branches = request.branches or generate_branches(request.decision)

    scenarios = run_simulation(
        initial_state=state,
        branches=branches,
        months=months,
        decision=request.decision,
    )

    assumptions = extracted.assumptions + [
        f"Automatically generated scenario branches use {scenario_generation_mode()} when branches are not supplied.",
        "Scenario changes use deterministic, decision-category starter rules.",
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
