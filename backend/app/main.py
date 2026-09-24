from fastapi import FastAPI

from .models import SimulationRequest, SimulationResponse
from .simulator import run_simulation

app = FastAPI(
    title="WhatIf AI",
    version="0.1.0",
    description="A stateful scenario simulation engine for exploring possible futures.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "whatif-ai"}


@app.post("/simulate", response_model=SimulationResponse)
def simulate(request: SimulationRequest) -> SimulationResponse:
    scenarios = run_simulation(
        initial_state=request.initial_state,
        branches=request.branches,
        months=request.months,
    )

    return SimulationResponse(
        decision=request.decision,
        scenarios=scenarios,
        assumptions=[
            "The current engine uses deterministic starter rules.",
            "Scenario values are illustrative simulation outputs, not forecasts.",
        ],
    )
