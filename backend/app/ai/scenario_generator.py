from __future__ import annotations

import json
import os
from typing import Any


def _fallback_branches(decision: str) -> list[str]:
    """Generate scenario labels locally when Gemini is not configured or fails."""
    text = decision.lower()

    if any(word in text for word in ("job", "career", "quit", "resign", "startup", "business")):
        return [
            "keep current path",
            "transition gradually with a balanced approach",
            "make the change aggressively",
            "delay the decision and reduce risk",
        ]

    if any(word in text for word in ("market", "advertis", "customer", "sales", "promotion", "marketing")):
        return [
            "continue current marketing strategy",
            "increase marketing investment optimistically",
            "increase marketing investment cautiously",
            "reduce marketing spend to limit risk",
        ]

    if any(word in text for word in ("invest", "budget", "spend", "cost", "expense", "save", "saving")):
        return [
            "maintain the current budget",
            "increase investment with an optimistic approach",
            "make a balanced investment",
            "reduce spending and prioritize savings",
        ]

    if any(word in text for word in ("learn", "study", "skill", "practice", "course", "knowledge", "ai")):
        return [
            "continue the current learning routine",
            "commit to an intensive learning plan",
            "follow a balanced learning schedule",
            "reduce the workload and learn steadily",
        ]

    if any(word in text for word in ("hire", "employee", "team", "staff")):
        return [
            "keep the current team size",
            "expand the team aggressively",
            "hire gradually as demand grows",
            "delay hiring and control costs",
        ]

    return [
        "continue the current path",
        "pursue the decision optimistically",
        "take a balanced approach",
        "choose a cautious approach to reduce risk",
    ]


def _generate_with_gemini(decision: str, api_key: str) -> list[str] | None:
    """Ask Gemini for structured scenario labels; return None on any failure."""
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        prompt = f"""You are the scenario-ideation component of WhatIf AI.
Generate 3 to 5 meaningfully different, concise scenario branch labels for the
user's decision. Include a reasonable baseline and contrasting approaches where
appropriate. Do not claim to know the future, invent numeric outcomes, or provide
advice as a certainty. Return JSON only in this shape:
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
        # Keep the API's documented maximum of eight branches and reject empty output.
        return cleaned[:8] if 3 <= len(cleaned) <= 8 else None
    except Exception:
        # Keep simulations available if the key, network, model, or response fails.
        return None


def scenario_generation_mode() -> str:
    """Return the configured generation mode for response transparency."""
    return "Gemini API" if os.getenv("GEMINI_API_KEY") else "local keyword rules"


def generate_branches(decision: str) -> list[str]:
    """Generate branches with Gemini when configured, otherwise use local rules."""
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        branches = _generate_with_gemini(decision, api_key)
        if branches:
            return branches
    return _fallback_branches(decision)
