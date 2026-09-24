from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    decision: str = Field(min_length=3)
    initial_state: dict[str, float] = Field(default_factory=dict)
    months: int = Field(default=3, ge=1, le=24)
    branches: list[str] = Field(
        default_factory=lambda: [
            "continue current path",
            "strongly pursue the decision",
            "take a balanced approach",
        ],
        min_length=1,
        max_length=8,
    )


class StateSnapshot(BaseModel):
    month: int
    values: dict[str, float]
    events: list[str] = Field(default_factory=list)


class Scenario(BaseModel):
    name: str
    assumption: str
    timeline: list[StateSnapshot]


class SimulationResponse(BaseModel):
    decision: str
    scenarios: list[Scenario]
    assumptions: list[str]
    disclaimer: str = (
        "This is a scenario simulation, not a prediction of the actual future."
    )
