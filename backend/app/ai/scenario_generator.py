from __future__ import annotations

import json
import os
import logging

logger = logging.getLogger(__name__)
from typing import Any


def _fallback_branches(decision: str) -> list[str]:
    """Choose the most specific domain first; investment wording can occur in any domain."""
    text = decision.lower()
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
    """Ask Gemini for structured scenario labels; return None on any failure."""
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash-lite")
        prompt = f"""You are the scenario-ideation component of WhatIf AI.
Generate 3 to 5 meaningfully different, concise scenario branch labels for the
user's decision. Prioritize the decision's main domain (for example learning,
career, health, or business) over incidental words like invest or budget.
Include a baseline and contrasting approaches. Do not invent numeric outcomes.
Return JSON only: {{"branches": ["short scenario label", "..."]}}

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
        # Log the exception type and a short sanitized message, never the API key.
        detail = str(exc).replace(api_key, "[REDACTED]")[:300]
        logger.warning("Gemini scenario generation failed (%s): %s", type(exc).__name__, detail)
        return None


def generate_branches_with_source(decision: str) -> tuple[list[str], str]:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        branches = _generate_with_gemini(decision, api_key)
        if branches:
            return branches, "Gemini API"
        return _fallback_branches(decision), "local keyword rules (Gemini unavailable or response invalid)"
    return _fallback_branches(decision), "local keyword rules (no API key configured)"


def generate_branches(decision: str) -> list[str]:
    return generate_branches_with_source(decision)[0]


def scenario_generation_mode() -> str:
    return "Gemini API configured" if os.getenv("GEMINI_API_KEY") else "local keyword rules"
