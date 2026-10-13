from __future__ import annotations

import json
import os
import re
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
    """Extract clear values locally and use labelled starter metrics for learning scenarios."""
    text = decision.lower()
    horizon_match = re.search(r"\b(\d{1,2})\s*(?:months?|mos?)\b", text)
    horizon = max(1, min(24, int(horizon_match.group(1)))) if horizon_match else months
    variables: dict[str, float] = {}
    assumptions: list[str] = []

    money_match = re.search(
        r"(?:₹|rs\.?\s*|inr\s*)([\d,]+(?:\.\d+)?)|([\d,]+(?:\.\d+)?)\s*(?:rupees|inr|rs\.?|₹)",
        text,
        re.IGNORECASE,
    )
    amount_text = next((group for group in money_match.groups() if group), None) if money_match else None
    amount = float(amount_text.replace(",", "")) if amount_text else None

    is_learning = any(word in text for word in (
        "learn", "learning", "study", "skill", "practice", "course", "knowledge", "ai", "project", "portfolio"
    ))
    if is_learning:
        if amount is not None:
            variables["learning_budget_remaining_inr"] = amount
            assumptions.append(f"Learning budget starts at ₹{amount:,.0f}, extracted from the decision.")
        else:
            variables["learning_budget_remaining_inr"] = 0.0
            assumptions.append("No learning budget amount was stated; budget tracking starts at ₹0.")
        # These are explicit starter assumptions, not facts about the user.
        variables["study_hours_per_week"] = 6.0
        variables["projects_completed"] = 0.0
        variables["skills_practiced"] = 0.0
        assumptions.append("Illustrative baseline: 6 study hours per week, 0 completed projects, and 0 skills practiced; edit these assumptions for a personalized model.")
    else:
        assumptions.append("No domain-specific metrics were inferred; add numeric starting values for quantitative comparisons.")

    return ExtractedDecision(
        goal="Explore possible outcomes of the stated decision",
        action=decision.strip(),
        horizon_months=horizon,
        variables=variables,
        constraints=[],
        assumptions=assumptions,
    )


def extract_decision(decision: str, months: int = 3) -> ExtractedDecision:
    """Use Gemini when available; otherwise use deterministic local extraction."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            from google import genai

            client = genai.Client(api_key=api_key)
            model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
            response = client.models.generate_content(
                model=model,
                contents=f"{SYSTEM_PROMPT}\n\nUser decision:\n{decision}",
                config={"response_mime_type": "application/json"},
            )
            data: Any = json.loads(response.text)
            extracted = ExtractedDecision.model_validate(data)
            if extracted.horizon_months == 3:
                horizon_match = re.search(r"\b(\d{1,2})\s*(?:months?|mos?)\b", decision.lower())
                if horizon_match:
                    extracted.horizon_months = max(1, min(24, int(horizon_match.group(1))))
            # Preserve clear amounts/horizon if the model omitted them.
            local = _fallback_extract(decision, months)
            for key, value in local.variables.items():
                extracted.variables.setdefault(key, value)
            extracted.assumptions.extend(item for item in local.assumptions if item not in extracted.assumptions)
            return extracted
        except Exception:
            pass
    return _fallback_extract(decision, months)
