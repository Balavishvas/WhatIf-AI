from fastapi.testclient import TestClient

from app.ai import scenario_generator
from app.ai.scenario_generator import generate_branches, generate_branches_with_source
from app.main import app

client = TestClient(app)


def test_generates_job_and_startup_branches_offline(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    branches = generate_branches("What if I quit my job to build a startup?")

    assert len(branches) >= 3
    assert any("current path" in branch for branch in branches)
    assert any("gradually" in branch or "balanced" in branch for branch in branches)
    assert any("aggressively" in branch or "risk" in branch for branch in branches)


def test_generates_marketing_branches_offline(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    branches = generate_branches("What if I increase marketing spend?")

    assert len(branches) >= 3
    assert any("marketing" in branch for branch in branches)


def test_simulate_automatically_generates_branches_when_omitted(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post(
        "/simulate",
        json={
            "decision": "What if I increase marketing spend?",
            "initial_state": {"revenue": 10000, "customers": 100, "cost": 3000},
            "months": 2,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["scenarios"]) >= 3
    assert any("marketing" in scenario["assumption"].lower() for scenario in payload["scenarios"])
    assert any("no API key configured" in assumption for assumption in payload["assumptions"])


def test_user_supplied_branches_are_preserved(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post(
        "/simulate",
        json={
            "decision": "What if I invest more in marketing?",
            "initial_state": {"revenue": 10000},
            "months": 1,
            "branches": ["custom scenario A", "custom scenario B"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert [scenario["assumption"] for scenario in payload["scenarios"]] == [
        "custom scenario A",
        "custom scenario B",
    ]
    assert any("user-supplied branches" in assumption for assumption in payload["assumptions"])


def test_uses_gemini_branches_when_available(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    expected = ["baseline", "growth approach", "cautious approach"]
    monkeypatch.setattr(scenario_generator, "_generate_with_gemini", lambda decision, api_key: expected)

    branches, source = generate_branches_with_source("What if I start a business?")

    assert branches == expected
    assert source == "Gemini API"


def test_falls_back_to_local_rules_when_gemini_fails(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(scenario_generator, "_generate_with_gemini", lambda decision, api_key: None)

    branches, source = generate_branches_with_source("What if I increase marketing spend?")

    assert len(branches) >= 3
    assert any("marketing" in branch for branch in branches)
    assert "Gemini unavailable" in source


def test_gemini_extraction_preserves_selected_horizon_when_decision_has_no_duration(monkeypatch):
    """Keep the UI-selected horizon when Gemini returns its default duration."""
    import json
    import sys
    from types import SimpleNamespace

    from app.ai import decision_extractor

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    payload = {
        "goal": "Learn AI",
        "action": "Learn AI",
        "horizon_months": 3,
        "variables": {},
        "constraints": [],
        "assumptions": [],
    }
    fake_response = SimpleNamespace(text=json.dumps(payload))
    fake_client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kwargs: fake_response))
    fake_genai = SimpleNamespace(Client=lambda **kwargs: fake_client)
    monkeypatch.setitem(sys.modules, "google", SimpleNamespace(genai=fake_genai))

    extracted = decision_extractor.extract_decision("What if I learn AI?", months=12)

    assert extracted.horizon_months == 12


def test_explicit_decision_duration_overrides_selected_horizon(monkeypatch):
    """Prefer a duration explicitly stated by the user over the UI selection."""
    import json
    import sys
    from types import SimpleNamespace

    from app.ai import decision_extractor

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    payload = {
        "goal": "Learn AI",
        "action": "Learn AI for six months",
        "horizon_months": 3,
        "variables": {},
        "constraints": [],
        "assumptions": [],
    }
    fake_response = SimpleNamespace(text=json.dumps(payload))
    fake_client = SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kwargs: fake_response))
    fake_genai = SimpleNamespace(Client=lambda **kwargs: fake_client)
    monkeypatch.setitem(sys.modules, "google", SimpleNamespace(genai=fake_genai))

    extracted = decision_extractor.extract_decision("What if I learn AI for 6 months?", months=12)

    assert extracted.horizon_months == 6
