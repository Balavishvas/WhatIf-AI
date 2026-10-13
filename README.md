# WhatIf AI ✳

> **Don't predict the future. Explore it.**

WhatIf AI turns a decision into several possible paths, then lets you inspect their illustrative month-by-month outcomes. Gemini can generate scenario branches; a transparent rule-based engine simulates the numeric timeline.

## The experience

- **AI-assisted branching:** generate alternative scenario labels with Gemini, with local keyword rules as a fallback.
- **Scenario-aware simulation:** compare baseline, growth, cautious and other paths using deterministic starter rates.
- **Trajectory comparison:** view a selected metric across all branches on a chart.
- **Explainable outputs:** inspect monthly values, change events, scenario source and assumptions.
- **Decision-first interface:** a dark, animated multiverse-inspired UI that emphasizes exploration over prediction.

> **Important:** These numbers are illustrative outputs from starter rules, not validated forecasts or financial advice. Gemini generates scenario descriptions; it does not validate the simulation's numeric rates.

## Repository layout

```text
WhatIf-AI/
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── decision_extractor.py
│   │   │   └── scenario_generator.py
│   │   ├── engine/
│   │   │   ├── simulation.py
│   │   │   └── state.py
│   │   ├── main.py
│   │   └── models.py
│   ├── tests/
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── styles.css
    └── app.js
```

## Requirements

- Python 3.11+
- A Gemini API key for Gemini-powered generation (optional; local branch generation remains available without it)
- A modern browser

## Run locally on Windows

### 1. Configure the backend

Open PowerShell in the repository root:

```powershell
cd backend
.env\Scripts\python.exe -m pip install -r requirements.txt
$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
$env:GEMINI_MODEL = "gemini-3.5-flash-lite"
.env\Scripts\python.exe -m uvicorn app.main:app --reload
```

If you created your virtual environment with a different folder name, use that environment's Python executable. Keep the key in your terminal or a local ignored environment file—never commit it to Git.

API documentation: http://127.0.0.1:8000/docs

### 2. Run the frontend

Open a **second** PowerShell window:

```powershell
cd D:\whatif-ai\WhatIf-AI\frontend
python -m http.server 5500
```

Open http://127.0.0.1:5500

The frontend calls the backend at `http://127.0.0.1:8000`. Both servers need to be running. To change the API base, set `window.WHATIF_API_BASE` before `app.js` loads.

### 3. Run tests

From the repository root:

```powershell
cd backend
.env\Scripts\python.exe -m pytest -q
```

## Example request

```json
{
  "decision": "What if I quit my job to build an AI startup?",
  "initial_state": {
    "revenue": 10000,
    "customers": 100,
    "cost": 3000
  },
  "months": 12,
  "branches": []
}
```

An empty `branches` array asks the backend to generate scenario branches automatically. The response's `assumptions` array identifies whether branches came from Gemini, local fallback rules, or user-supplied input.

## Current limitations

- The numeric simulation uses deterministic, keyword-driven starter rates.
- A scenario label is not itself a calibrated model or evidence-based prediction.
- State variable meanings are user-provided; use meaningful starting values for useful comparisons.
- Browser frontend is a static app and requires the backend API to be running.

## Roadmap

- [x] FastAPI simulation API and world-state engine
- [x] Gemini-powered scenario generation with local fallback
- [x] Scenario-specific starter rates and monthly explanations
- [x] Distinctive interactive frontend and trajectory comparison
- [x] Automated backend tests and GitHub Actions
- [ ] Calibrated, domain-specific simulation models
- [ ] Save and compare previous simulations
- [ ] Branch from a prior point in a timeline
- [ ] More robust simulation evaluation

**WhatIf AI — Don't predict the future. Explore it.**
