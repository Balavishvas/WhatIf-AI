# WhatIf AI 🔀

> **Don't predict the future. Explore it.**

WhatIf AI is an AI-powered scenario simulation engine for exploring how different decisions can lead to different possible futures under explicit assumptions.

Instead of asking an AI *"What should I do?"*, WhatIf AI asks:

**"What could happen if I choose this?"**

## Core idea

A decision becomes a set of possible branches. Each branch has a state, events, assumptions, and measurable changes over time.

```text
                    DECISION
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Scenario A   Scenario B   Scenario C
          │            │            │
       Month 1       Month 1       Month 1
          │            │            │
       Month 2       Month 2       Month 2
          │            │            │
       Month 3       Month 3       Month 3
          └────────────┼────────────┘
                       ▼
                Compare outcomes
```

## What makes it different?

WhatIf AI is designed around a **stateful simulation engine**, not a simple chatbot.

- Natural-language decision parsing
- Explicit world state
- Branching scenarios
- Timeline-based simulation
- State transitions
- Assumptions and constraints
- Scenario comparison
- Re-branching from any point in a timeline
- AI-generated events
- Visual future trajectories

### Important

WhatIf AI does **not** claim to predict a person's actual future. It explores possible trajectories based on stated assumptions and simulation rules.

## Project structure

```text
WhatIf-AI/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   └── simulator.py
│   └── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## Quick start

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs will be available at:

```
http://127.0.0.1:8000/docs
```

## Example request

```json
{
  "decision": "Spend the next 3 months learning AI",
  "initial_state": {
    "ai_skill": 20,
    "web_skill": 70,
    "available_hours_per_week": 20
  },
  "months": 3,
  "branches": [
    "focus on AI",
    "balance AI and web development",
    "continue focusing on web development"
  ]
}
```

## Roadmap

- [x] Initial simulation engine
- [x] Scenario state model
- [x] Timeline generation
- [ ] LLM decision parser
- [ ] LangGraph orchestration
- [ ] Event generation agent
- [ ] React visualization
- [ ] Scenario comparison dashboard
- [ ] Persistent simulations
- [ ] Branch-from-history ("What if I changed this?")
- [ ] Simulation evaluation framework

## Vision

Turn vague **"What if?"** questions into structured, explorable simulations.

**WhatIf AI — Don't predict the future. Explore it.**
