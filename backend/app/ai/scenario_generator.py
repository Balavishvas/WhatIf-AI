from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def _fallback_branches(decision: str) -> list[str]:
    """Choose domain-specific paths when Gemini is unavailable."""
    text = decision.lower()

    if any(word in text for word in ("stock market", "stock-market", "stock marketing", "stock trading", "day trading", "paper trading", "learn trading", "learning trading", "technical analysis")):
        return [
            "Build a consistent stock-market learning routine while keeping real money out of the process",
            "Follow a structured financial-analysis course and practice concepts with a paper portfolio",
            "Study long-term investing principles and test written strategies with historical data",
            "Combine study with paper trading and review a learning journal before considering real-money risk",
        ]
    if any(word in text for word in ("undergraduate", "join ug", "college", "university", "degree", "get into job", "job after school", "workforce", "study or work", "study vs job")):
        return [
            "Enroll in undergraduate study and budget for the full course",
            "Enter the workforce first and build experience while saving for study",
            "Work part-time while pursuing a degree if schedule and admission rules allow",
            "Compare scholarships, accredited lower-cost programs, and a planned deferred start",
        ]
    if any(word in text for word in ("life insurance", "term insurance", "life cover", "life coverage")):
        return [
            "Compare affordable term-life cover for the needed protection period",
            "Compare a higher coverage amount against the premium budget",
            "Review existing employer or family coverage before buying another policy",
            "Delay purchase briefly while comparing policy terms and exclusions",
        ]
    if any(word in text for word in ("health insurance", "medical insurance", "hospitalization cover", "mediclaim")):
        return [
            "Choose a policy prioritizing adequate hospitalization coverage",
            "Compare a lower premium with its deductible and co-pay",
            "Compare individual cover with a family floater",
            "Review exclusions, waiting periods, and network hospitals before choosing",
        ]
    if any(word in text for word in ("insurance", "policy premium", "sum insured", "coverage amount", "deductible", "copay", "co-pay")):
        return [
            "Prioritize essential coverage within the premium budget",
            "Compare broader coverage with the added premium",
            "Compare deductibles, exclusions, and claim conditions before choosing",
            "Wait and compare multiple policy terms before committing",
        ]
    if any(word in text for word in ("mortgage", "home loan", "house loan", "buy a house", "buy a home", "home purchase", "purchase a home", "buying a home", "buying a house")):
        return [
            "Buy with a 10-year mortgage: higher monthly payments, less total interest",
            "Choose a 30-year mortgage: lower required monthly payments, more total interest",
            "Choose a 15-year mortgage: balance monthly affordability and total interest",
            "Delay buying and save a larger down payment before taking a mortgage",
        ]
    if any(word in text for word in ("bike", "motorcycle", "scooter", "car", "vehicle", "600 cc", "600cc", "emi", "fuel", "commuting")):
        return [
            "Buy now and budget for full ownership costs",
            "Buy with financing after checking EMI affordability",
            "Use the vehicle mainly for weekends and limit running costs",
            "Delay the purchase and save toward a larger down payment",
        ]
    if any(word in text for word in ("ice cream", "sweets", "sweet", "sugar", "snack", "junk food", "eat every day", "eating every day", "daily diet", "diet", "nutrition", "food habit")):
        return [
            "Keep the habit but choose a smaller, mindful portion",
            "Pair occasional treats with a varied, balanced eating routine",
            "Make the treat occasional rather than an everyday habit",
            "Track the habit for a few weeks and adjust based on how you feel",
        ]
    if any(word in text for word in ("learn", "learning", "study", "skill", "practice", "course", "knowledge", "ai", "project", "build portfolio")):
        return [
            "Maintain a steady learning routine",
            "Commit to an intensive AI learning and project plan",
            "Follow a balanced learning schedule with regular projects",
            "Learn cautiously with a smaller workload and budget",
        ]
    if any(word in text for word in ("market", "advertis", "customer", "sales", "promotion", "marketing")):
        return [
            "Continue the current marketing strategy",
            "Increase marketing investment optimistically",
            "Test a balanced marketing investment",
            "Reduce marketing spend to limit risk",
        ]
    if any(word in text for word in ("hire", "employee", "team", "staff")):
        return [
            "Keep the current team size",
            "Expand the team aggressively",
            "Hire gradually as demand grows",
            "Delay hiring and control costs",
        ]
    if any(word in text for word in ("job", "career", "quit", "resign", "startup", "business")):
        return [
            "Keep the current path",
            "Transition gradually with a balanced approach",
            "Make the change aggressively",
            "Delay the decision and reduce risk",
        ]
    if any(word in text for word in ("invest", "budget", "spend", "cost", "expense", "save", "saving")):
        return [
            "Maintain the current budget",
            "Increase investment with an optimistic approach",
            "Make a balanced investment",
            "Reduce spending and prioritize savings",
        ]
    return [
        "Continue the current path",
        "Pursue the decision optimistically",
        "Take a balanced approach",
        "Choose a cautious approach to reduce risk",
    ]


def _generate_with_gemini(decision: str, api_key: str) -> list[str] | None:
    """Ask Gemini for domain-specific scenario labels, not numeric predictions."""
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        prompt = f"""You are the scenario-ideation component of WhatIf AI.
Generate 3 to 5 distinct, practical scenario paths for this decision.
First identify its main domain and tailor paths to that domain. Do not use generic
business/finance paths for a personal, vehicle, health, insurance, career, or education
question. For vehicle decisions consider purchase timing, financing, running costs,
maintenance, insurance, and use patterns where relevant. For life/health insurance,
consider coverage needs, affordability, policy duration, exclusions, deductibles or
waiting periods where relevant. Do not claim to give individualized medical, legal,
insurance, or financial advice. Do not invent numeric outcomes or policy terms.
Include a baseline and meaningful alternatives. Return JSON only:
{{"branches": ["short scenario label", "..."]}}

User decision:
{decision}"""
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        payload: Any = json.loads(response.text)
        branches = payload.get("branches") if isinstance(payload, dict) else None
        if not isinstance(branches, list):
            return None
        cleaned = [item.strip() for item in branches if isinstance(item, str) and item.strip()]
        return cleaned[:8] if 3 <= len(cleaned) <= 8 else None
    except Exception as exc:
        detail = str(exc).replace(api_key, "[REDACTED]")[:300]
        logger.warning("Gemini scenario generation failed (%s): %s", type(exc).__name__, detail)
        return None


def generate_branches_with_source(decision: str) -> tuple[list[str], str]:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        branches = _generate_with_gemini(decision, api_key)
        if branches:
            return branches, "Gemini API"
        return _fallback_branches(decision), "local domain rules (Gemini unavailable or response invalid)"
    return _fallback_branches(decision), "local domain rules (no API key configured)"


def generate_branches(decision: str) -> list[str]:
    return generate_branches_with_source(decision)[0]


def scenario_generation_mode() -> str:
    return "Gemini API configured" if os.getenv("GEMINI_API_KEY") else "local domain rules"
