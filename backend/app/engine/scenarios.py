from __future__ import annotations

from ..ai.decision_extractor import ExtractedDecision


def build_scenarios(decision: ExtractedDecision, branches: list[str]) -> list[dict[str, str]]:
    """Turn a structured decision into explicit simulation branches."""
    scenarios = []
    for branch in branches:
        scenarios.append(
            {
                "name": branch.title(),
                "assumption": branch,
                "action": decision.action,
            }
        )
    return scenarios
