from __future__ import annotations


def generate_branches(decision: str) -> list[str]:
    """Generate a small set of scenario branches using local keyword rules.

    This function requires no cloud model, API key, or network connection.
    It creates scenario labels, not predictions or domain-specific facts.
    """
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
