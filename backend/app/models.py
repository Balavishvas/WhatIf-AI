from __future__ import annotations

from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    decision: str = Field(min_length=3)
    initial_state: dict[str, float] = Field(default_factory=dict)
    months: int = Field(default=3, ge=1, le=24)
    # Empty means the backend will generate decision-relevant branches locally.
    branches: list[str] = Field(default_factory=list, min_length=0, max_length=8)


class StateSnapshot(BaseModel):
    month: int
    values: dict[str, float]
    events: list[str] = Field(default_factory=list)


class Scenario(BaseModel):
    name: str
    assumption: str
    timeline: list[StateSnapshot]
    tag: str = "ALTERNATIVE"
    considerations: list[str] = Field(default_factory=list)
    wildcards: list[str] = Field(default_factory=list)


class SimulationResponse(BaseModel):
    decision: str
    scenarios: list[Scenario]
    assumptions: list[str]
    domain: str = "general"
    domain_label: str = "General decision"
    metrics: list[dict[str, str]] = Field(default_factory=list)
    safety_notice: str | None = None
    disclaimer: str = (
        "This is a scenario simulation, not a prediction of the actual future."
    )
