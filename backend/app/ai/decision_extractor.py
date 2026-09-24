from __future__ import annotations

import json
import os
from typing import Any

from pydantic import BaseModel, Field


class ExtractedDecision(BaseModel):
    """Structured representation of a user's decision."""

    goal: str
    action: str
    horizon_months: int = Field(default=3, ge=1, le=24)
    variables: dict[str, float] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


SYSTEM_PROMPT = """You are the decision extraction layer for WhatIf AI.
Convert a natural-language decision into structured JSON for a scenario simulation.
Do not predict the user's future. Extract only what the user said and reasonable
explicit assumptions needed to model the scenario. If a numeric value is unknown,
do not invent one. Use an empty object/list instead.

Return JSON with exactly these fields:
goal: string
action: string
horizon_months: integer from 1 to 24
variables: object mapping measurable variable names to numeric starting values
constraints: array of strings
assumptions: array of strings
"""


def _fallback_extract(decision: str, months: int) -> ExtractedDecision:
    """Safe local fallback when no LLM credentials are configured."""
    return ExtractedDecision(
        goal="Explore the possible outcomes of the stated decision",
        action=decision.strip(),
        horizon_months=months,
        variables={},
        constraints=[],
        assumptions=["The decision was not yet converted into domain-specific numeric state."],
    )


def extract_decision(decision: str, months: int = 3) -> ExtractedDecision:
    """Extract structured decision data using Gemini when configured.

    The LLM is optional. Without GEMINI_API_KEY, the API remains usable through
    the deterministic fallback so development does not depend on credentials.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _fallback_extract(decision, months)

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        response = client.models.generate_content(
            model=model,
            contents=f"{SYSTEM_PROMPT}\n\nUser decision:\n{decision}",
            config={"response_mime_type": "application/json"},
        )
        data: Any = json.loads(response.text)
        return ExtractedDecision.model_validate(data)
    except Exception:
        # Keep the core simulation service available even if the external model
        # is unavailable, misconfigured, or returns invalid JSON.
        return _fallback_extract(decision, months)
