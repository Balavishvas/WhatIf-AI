from __future__ import annotations

import json
import logging
import os
from typing import Any

from ..engine.domains import DOMAIN_LABELS, METRIC_CATALOG, classify_domain
from ..models import Scenario, SimulationResponse, StateSnapshot

logger = logging.getLogger(__name__)


def _fallback_branches(decision: str) -> list[str]:
    """Choose domain-specific paths when Gemini is unavailable."""
    text = decision.lower()

    if any(word in text for word in ("kidney", "kideney", "sell organ", "organ")):
        return [
            "Keep both kidneys: retain basic biological filtration and use your current phone",
            "Sell kidney for iPhone: enjoy 4K hospital selfies until the iPhone 19 renders your sacrifice obsolete",
            "Get scammed by shady organ brokers and wake up in a bathtub with no phone and one less organ",
            "Work a boring side hustle instead and survive long enough to buy the iPhone 25",
        ]
    if any(word in text for word in ("fight 100", "fight a bear", "fight a kangaroo", "zombie", "alien invasion", "rob a bank", "become a pirate")):
        return [
            "Reconsider immediately and preserve your life and dignity",
            "Go full throttle into the chaos and document the immediate disaster",
            "Attempt a cowardly tactical compromise that minimizes bodily harm",
            "Watch a documentary about it from the safety of your couch instead",
        ]

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
First identify its main domain and tailor paths to that domain.
If the decision is comedic, absurd, satirical, or a meme (e.g. selling a kidney for an iPhone, fighting 100 animals, marrying a robot), match the user's humor with hilarious, witty, and satirical branches that playfully expose the absurdity.
Do not use generic business/finance paths for a personal, vehicle, health, insurance, career, humor, or education question.
For home purchase or mortgage decisions, compare loan terms such as 10, 15 and 30 years only as alternatives, explaining monthly-payment versus total-interest trade-offs; include delaying purchase as an option. Do not invent interest rates, loan amounts, monthly payments or savings. For vehicle decisions consider purchase timing, financing, running costs,
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


def generate_rich_simulation(
    decision: str,
    horizon_months: int = 6,
    initial_state: dict[str, float] | None = None,
) -> SimulationResponse | None:
    """Generate high-conviction, non-sloppy multi-scenario simulation using Gemini."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

        initial_state = initial_state or {}
        domain_hint = classify_domain(decision)
        domain_label_hint = DOMAIN_LABELS.get(domain_hint, "Scenario Planning")
        catalog_metrics = METRIC_CATALOG.get(domain_hint, [])

        prompt = f"""You are the lead strategic foresight and simulation intelligence for WhatIf AI.
Your objective is to generate an in-depth, rigorous scenario simulation for a user's what-if decision or hypothetical question.
CRITICAL QUALITY DIRECTIVES:
- NO generic platitudes or boilerplate fluff.
- NO identical numbers or flat trajectories across scenarios: each scenario MUST have distinct numerical progressions reflecting its specific risks, resource burn, and outcomes.
- USER-CONTROLLED STARTING INPUTS:
    * If the user explicitly supplied starting numbers (initial state), your metrics MUST include those keys and start from those values.
    * If the user did NOT supply starting numbers (initial_state is empty), DO NOT ask for revenue or financial numbers. Instead, automatically synthesize realistic, plausible real-world general baseline benchmarks and trajectories tailored to the decision (e.g., realistic baseline costs, runway, time commitments, or adoption rates) so the user gets concrete, meaningful real-life possibilities.
- CRITICAL TONE & HUMOR DIRECTIVE:
    * Detect if the user's question or decision is comedic, funny, absurd, satirical, reckless, or a meme (e.g. "what if I sell my kidney to buy new iphone 18", "what if I fight 100 duck-sized horses", "what if I eat only instant noodles for 10 years", "what if I marry my robot vacuum"):
    * DO NOT be a boring, dry, serious corporate advisor! Match the user's comedic energy with razor-sharp wit, dark humor, satirical realism, and playful roasting!
    * Directly highlight the hilarious absurdity of the premise in the scenario titles and assumptions. For instance, for selling a kidney for an iPhone:
        - Highlight that you might not live long enough to enjoy the 120Hz display.
        - Highlight that even though you bought the iPhone 18, you won't survive until the iPhone 19 release, and you have no spare kidneys left for future upgrades!
        - Contrast iPhone battery health (100%) against biological kidney function (plummeting to 20%).
        - Note that hospital dialysis Wi-Fi is too slow to backup iCloud photos.
    * Make the 1st, 2nd, and 3rd order considerations, monthly events, and wildcards genuinely funny, punchy, and witty!
    * Provide funny, creative custom metrics tailored to the joke (e.g. survival_odds_pct, regret_index, flex_score, kidney_count).
- Provide 3 to 4 distinct scenario archetypes:
    1. BASELINE: Continuation of current trajectory or standard minimal-deviation transition.
    2. GROWTH / ACCELERATED: High ambition, maximum resource allocation, high divergence and higher risk.
    3. CAUTIOUS / MITIGATED: Defensive, staged risk-managed approach, preserving runway and capital.
    4. ALTERNATIVE / PIVOT: Creative, hybrid, or counter-intuitive paradigm shift.

User Decision/Question: {decision}
Simulation Horizon: {horizon_months} months
User-supplied Initial State: {json.dumps(initial_state)}
Suggested Domain: {domain_hint} ({domain_label_hint})

For each scenario provide:
- "name": Concise, high-conviction title (e.g., "Full-Time Sprint: Bootstrapped MVP")
- "tag": "BASELINE", "GROWTH", "CAUTIOUS", or "ALTERNATIVE"
- "assumption": 1-2 sharp sentences articulating the core thesis and trade-offs.
- "considerations": Exactly 3 to 4 multi-order impacts:
    * "1st Order (Immediate): [Direct operational or tactical change in months 1-2]"
    * "2nd Order (Cascading): [Ripple effects on dependencies, burn, behavior, or market in months 3-4]"
    * "3rd Order (Systemic): [Structural transformation, compounding outcome, or career shift by month {horizon_months}]"
- "wildcards": 1 to 2 critical hinge variables that could overturn this path.
- "timeline": Exactly {horizon_months} monthly snapshots (from month 1 to month {horizon_months}):
    * "month": integer from 1 to {horizon_months}
    * "values": numeric values for each metric in your metrics list, evolving logically across months.
    * "events": 1-2 concrete, realistic milestones or friction points for that month.

Return JSON only in this exact schema:
{{
  "domain": "{domain_hint}",
  "domain_label": "{domain_label_hint}",
  "metrics": [
    {{"key": "metric_key_name", "label": "Human Readable Label", "unit": "INR|USD|%|hours|index|users", "kind": "calculated|cost|plan|input"}}
  ],
  "scenarios": [
    {{
      "name": "Scenario Title",
      "tag": "BASELINE|GROWTH|CAUTIOUS|ALTERNATIVE",
      "assumption": "Clear driving thesis.",
      "considerations": [
        "1st Order (Immediate): ...",
        "2nd Order (Cascading): ...",
        "3rd Order (Systemic): ..."
      ],
      "wildcards": [
        "Critical dependency or unknown variable."
      ],
      "timeline": [
        {{
          "month": 1,
          "values": {{"metric_key_name": 100.0}},
          "events": ["Specific operational milestone for month 1"]
        }}
      ]
    }}
  ],
  "assumptions": [
    "Overarching simulation principle or boundary condition."
  ]
}}"""

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        data = json.loads(response.text)
        if not isinstance(data, dict):
            return None

        scenarios_data = data.get("scenarios")
        if not isinstance(scenarios_data, list) or len(scenarios_data) < 2:
            return None

        parsed_scenarios: list[Scenario] = []
        for s in scenarios_data:
            if not isinstance(s, dict):
                continue
            timeline_list: list[StateSnapshot] = []
            for t in s.get("timeline", []):
                if isinstance(t, dict) and "month" in t:
                    raw_values = t.get("values", {})
                    clean_values = {
                        str(k): float(v)
                        for k, v in raw_values.items()
                        if isinstance(v, (int, float))
                    }
                    timeline_list.append(
                        StateSnapshot(
                            month=int(t["month"]),
                            values=clean_values,
                            events=[str(e) for e in t.get("events", []) if isinstance(e, str)],
                        )
                    )
            if not timeline_list:
                continue

            parsed_scenarios.append(
                Scenario(
                    name=str(s.get("name", "Scenario")),
                    assumption=str(s.get("assumption", "")),
                    timeline=timeline_list,
                    tag=str(s.get("tag", "ALTERNATIVE")).upper(),
                    considerations=[str(c) for c in s.get("considerations", []) if isinstance(c, str)],
                    wildcards=[str(w) for w in s.get("wildcards", []) if isinstance(w, str)],
                )
            )

        if len(parsed_scenarios) < 2:
            return None

        domain = str(data.get("domain", domain_hint))
        domain_label = str(data.get("domain_label", domain_label_hint))
        metrics = data.get("metrics")
        if not isinstance(metrics, list) or not metrics:
            metrics = METRIC_CATALOG.get(domain, METRIC_CATALOG.get("general", []))

        assumptions = [str(a) for a in data.get("assumptions", []) if isinstance(a, str)]
        assumptions.extend([
            "Scenario branch source: Gemini AI simulation intelligence.",
            "Modeled trajectories evaluate multi-order consequences and trade-offs; they are not guaranteed forecasts.",
            "Verify real-world quotes, contracts, and empirical data before committing major resources.",
        ])

        return SimulationResponse(
            decision=decision,
            scenarios=parsed_scenarios,
            assumptions=assumptions,
            domain=domain,
            domain_label=domain_label,
            metrics=metrics,
            disclaimer="This is an exploratory AI scenario simulation, not a guaranteed prediction.",
        )
    except Exception as exc:
        detail = str(exc).replace(api_key, "[REDACTED]")[:300]
        logger.warning("Rich Gemini simulation failed (%s): %s", type(exc).__name__, detail)
        return None
