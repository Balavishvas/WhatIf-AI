from __future__ import annotations

import json
import os
import logging

logger = logging.getLogger(__name__)
import re
from typing import Any

from pydantic import BaseModel, Field

from ..engine.domains import classify_domain


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

    domain = classify_domain(decision)
    # Prefer domain-specific input names so the calculator never mistakes revenue
    # for salary, premium, education costs, or a vehicle purchase price.
    if domain == "stock_learning":
        variables = {
            "study_hours_per_week": 0.0,
            "learning_budget_inr": amount or 0.0,
            "learning_budget_specified": 1.0 if amount is not None else 0.0,
            "learning_cost_inr": 0.0,
            "paper_trading_sessions": 0.0,
            "strategies_tested": 0.0,
            "concepts_practiced": 0.0,
        }
        assumptions.append("Learning progress metrics are planning targets; no stock-market profit or return is predicted.")
        if amount is None:
            assumptions.append("No learning budget was specified; enter course and tool costs to personalize cost comparisons.")
        return ExtractedDecision(goal="Explore stock-market learning approaches", action=decision.strip(), horizon_months=horizon, variables=variables, constraints=[], assumptions=assumptions)
    if domain == "education_career":
        variables = {"education_cost_inr": 0.0, "monthly_take_home_inr": 0.0, "study_hours_per_week": 0.0, "work_experience_months": 0.0, "cumulative_education_cost_inr": 0.0, "cumulative_earnings_inr": 0.0}
        assumptions.append("Enter total course cost and a realistic take-home salary if known; future admission and employment are not guaranteed.")
        return ExtractedDecision(goal="Compare education and work pathways", action=decision.strip(), horizon_months=horizon, variables=variables, constraints=[], assumptions=assumptions)
    if domain in ("life_insurance", "health_insurance", "insurance"):
        variables = {"monthly_premium_inr": 0.0, "coverage_amount_inr": 0.0, "annual_premium_inr": 0.0}
        if amount is not None:
            if any(word in text for word in ("monthly premium", "per month premium", "premium each month")):
                variables["monthly_premium_inr"] = amount
            elif any(word in text for word in ("coverage", "cover of", "sum insured", "life cover")):
                variables["coverage_amount_inr"] = amount
            else:
                assumptions.append("The amount mentioned was not assigned to a premium or coverage field because its meaning is ambiguous.")
        assumptions.append("Use actual insurer quotes and policy wording; no premiums, coverage eligibility or claim outcomes are invented.")
        return ExtractedDecision(goal="Compare insurance options", action=decision.strip(), horizon_months=horizon, variables=variables, constraints=[], assumptions=assumptions)
    if domain == "home_finance":
        variables = {
            "home_price_inr": 0.0, "down_payment_inr": 0.0, "loan_amount_inr": 0.0,
            "annual_interest_rate_pct": 0.0, "loan_term_years": 0.0,
        }
        rate_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent)", text)
        term_match = re.search(r"\b(\d{1,2})\s*[- ]?year", text)
        if rate_match:
            variables["annual_interest_rate_pct"] = float(rate_match.group(1))
        if term_match:
            variables["loan_term_years"] = float(term_match.group(1))
        if amount is not None:
            if any(word in text for word in ("down payment", "downpayment", "deposit")):
                variables["down_payment_inr"] = amount
            elif any(word in text for word in ("loan amount", "mortgage amount", "borrow")):
                variables["loan_amount_inr"] = amount
            elif any(word in text for word in ("home price", "house price", "property price", "home costs", "house costs")):
                variables["home_price_inr"] = amount
            else:
                assumptions.append("The stated amount was not assigned to a home-price, down-payment or loan field because its meaning is ambiguous.")
        assumptions.append("Mortgage payment estimates require a known loan amount or home price/down payment, annual interest rate and term.")
        return ExtractedDecision(goal="Compare home-purchase financing paths", action=decision.strip(), horizon_months=horizon, variables=variables, constraints=[], assumptions=assumptions)
    if domain == "vehicle":
        variables = {"vehicle_purchase_price_inr": 0.0, "down_payment_inr": 0.0, "monthly_emi_inr": 0.0, "monthly_fuel_cost_inr": 0.0, "monthly_maintenance_cost_inr": 0.0, "annual_insurance_cost_inr": 0.0}
        if amount is not None:
            if "down payment" in text:
                variables["down_payment_inr"] = amount
            elif any(word in text for word in ("monthly emi", "emi of", "emi is")):
                variables["monthly_emi_inr"] = amount
            elif any(word in text for word in ("fuel cost", "fuel per month")):
                variables["monthly_fuel_cost_inr"] = amount
            elif any(word in text for word in ("bike costs", "bike price", "purchase price", "vehicle price", "car price")):
                variables["vehicle_purchase_price_inr"] = amount
            else:
                assumptions.append("The mentioned amount was not assigned to a vehicle-cost field because its meaning is ambiguous.")
        assumptions.append("Missing vehicle prices, loan terms, mileage, fuel prices, maintenance and insurance quotes remain unknown; supply actual values.")
        return ExtractedDecision(goal="Compare vehicle ownership paths", action=decision.strip(), horizon_months=horizon, variables=variables, constraints=[], assumptions=assumptions)
    if domain == "personal_finance":
        variables = {"monthly_income_inr": 0.0, "monthly_expenses_inr": 0.0, "savings_inr": 0.0}
        assumptions.append("Provide monthly income, expenses and current savings for a numeric budget simulation.")
        return ExtractedDecision(goal="Explore personal-finance trade-offs", action=decision.strip(), horizon_months=horizon, variables=variables, constraints=[], assumptions=assumptions)

    is_learning = any(word in text for word in (
        "learn", "learning", "study", "skill", "practice", "course", "knowledge", "ai", "project", "portfolio"
    ))
    if is_learning:
        if amount is not None:
            variables["learning_budget_inr"] = amount
            variables["learning_budget_specified"] = 1.0
            assumptions.append(f"Learning budget starts at ₹{amount:,.0f}, extracted from the decision.")
        else:
            variables["learning_budget_inr"] = 0.0
            variables["learning_budget_specified"] = 0.0
            assumptions.append("No learning budget amount was stated; budget tracking is uncapped until a budget is supplied.")
        # These are explicit starter assumptions, not facts about the user.
        variables["study_hours_per_week"] = 6.0
        variables["projects_completed"] = 0.0
        variables["skills_practiced"] = 0.0
        variables["learning_cost_inr"] = 0.0
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
                contents=f"{SYSTEM_PROMPT}\nDetected domain: {classify_domain(decision)}. Use only relevant domain metrics and never invent missing numeric values.\n\nUser decision:\n{decision}",
                config={"response_mime_type": "application/json"},
            )
            data: Any = json.loads(response.text)
            extracted = ExtractedDecision.model_validate(data)
            horizon_match = re.search(r"\b(\d{1,2})\s*(?:months?|mos?)\b", decision.lower())
            if horizon_match:
                # An explicit duration in the user's wording takes precedence over UI defaults.
                extracted.horizon_months = max(1, min(24, int(horizon_match.group(1))))
            else:
                # If the user did not state a duration, preserve the duration selected in the UI.
                extracted.horizon_months = max(1, min(24, months))
            # Preserve clear amounts/horizon if the model omitted them.
            local = _fallback_extract(decision, months)
            for key, value in local.variables.items():
                extracted.variables.setdefault(key, value)
            extracted.assumptions.extend(item for item in local.assumptions if item not in extracted.assumptions)
            return extracted
        except Exception as exc:
            detail = str(exc).replace(api_key, "[REDACTED]")[:300]
            logger.warning("Gemini decision extraction failed (%s): %s", type(exc).__name__, detail)
    return _fallback_extract(decision, months)
