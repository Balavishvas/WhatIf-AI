from fastapi.testclient import TestClient

from app.ai.scenario_generator import generate_branches
from app.main import app

client = TestClient(app)


def test_generates_job_and_startup_branches_offline():
    branches = generate_branches("What if I quit my job to build a startup?")

    assert len(branches) >= 3
    assert any("current path" in branch for branch in branches)
    assert any("gradually" in branch or "balanced" in branch for branch in branches)
    assert any("aggressively" in branch or "risk" in branch for branch in branches)


def test_generates_marketing_branches_offline():
    branches = generate_branches("What if I increase marketing spend?")

    assert len(branches) >= 3
    assert any("marketing" in branch for branch in branches)


def test_simulate_automatically_generates_branches_when_omitted():
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
    assert any("generated locally" in assumption for assumption in payload["assumptions"])


def test_user_supplied_branches_are_preserved():
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
    assert [scenario["assumption"] for scenario in response.json()["scenarios"]] == [
        "custom scenario A",
        "custom scenario B",
    ]
