# WhatIf AI ✳

> **Your future isn't one straight line. Explore the possibilities.**

WhatIf AI turns a decision into several possible paths, then lets you inspect illustrative month-by-month outcomes. Gemini can generate scenario branches; a transparent, deterministic starter engine simulates the numeric timeline.

## What you can do

- **Explore alternatives:** generate scenario branches with Gemini or local fallback rules.
- **Compare trajectories:** view a selected metric across possible paths.
- **Inspect monthly detail:** expand each path to see timeline values and change events.
- **Understand the assumptions:** see where branches came from and how to interpret the outputs.
- **Start with your own numbers:** optionally provide income/revenue, users/customers, and costs.

> **Important:** the numeric outputs use deterministic starter rules. They are illustrative scenario simulations, not validated forecasts or financial advice. Gemini can generate scenario descriptions; it does not calibrate the numeric rates.

## Run locally on Windows

### Recommended: launch both servers together

Requirements: Python 3.11+ and an internet connection for the initial dependency install.

1. Pull the latest code:
   ```powershell
   cd D:\whatif-ai\WhatIf-AI
   git pull origin main
   ```
2. Run the launcher from the repository root:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\run-whatif.ps1
   ```

The launcher prepares pip and the backend dependencies, starts FastAPI if it is not already healthy, starts the static frontend if it is not already responding, checks both services, and opens the frontend and Swagger. Keep the two server windows open while using the app.

- Frontend: http://127.0.0.1:5500
- Backend health: http://127.0.0.1:8000/health
- API docs (Swagger): http://127.0.0.1:8000/docs

### Optional: start manually

In one PowerShell window:
```powershell
cd D:\whatif-ai\WhatIf-AI\backend
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second PowerShell window:
```powershell
cd D:\whatif-ai\WhatIf-AI
.\backend\venv\Scripts\python.exe -m http.server 5500 --directory .\frontend --bind 127.0.0.1
```

Then open http://127.0.0.1:5500.

### Gemini setup (optional)

For Gemini-powered branch generation, set your key in the backend terminal before starting Uvicorn:
```powershell
$env:GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
$env:GEMINI_MODEL = "gemini-3.5-flash-lite"
```

Without a key, the backend uses its local branch-generation fallback. Never commit your API key to Git.

## Repository layout

```text
WhatIf-AI/
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   ├── engine/
│   │   ├── main.py
│   │   └── models.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── run-whatif.ps1
```

## Test the backend

```powershell
cd D:\whatif-ai\WhatIf-AI\backend
.\venv\Scripts\python.exe -m pytest -q
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

An empty `branches` array asks the backend to generate branches automatically. The response's assumptions identify whether branches came from Gemini, local fallback rules, or user-supplied input.

## Current limitations

- Numeric simulation uses deterministic, keyword-driven starter rates.
- A scenario label is not a calibrated model or evidence-based prediction.
- State variable meanings depend on the values supplied by the user.
- The frontend requires the backend API; the launcher checks both services before opening the app.

**WhatIf AI — Explore, don't predict.**
