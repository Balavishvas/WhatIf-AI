from fastapi import FastAPI

from .ai.decision_extractor import extract_decision
from .models import SimulationRequest, SimulationResponse
from .engine.simulation import run_simulation

app = FastAPI(
    title="WhatIf AI",
    version="0.2.0",
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

    scenarios = run_simulation(
        initial_state=state,
        branches=request.branches,
        months=months,
    )

    return SimulationResponse(
        decision=request.decision,
        scenarios=scenarios,
        assumptions=extracted.assumptions + [
            "The simulation engine currently uses deterministic starter rules.",
            "Scenario values are illustrative simulation outputs, not forecasts.",
        ],
    )
