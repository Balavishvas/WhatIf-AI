from fastapi.testclient import TestClient

from app.engine.domains import classify_domain, domain_metadata
from app.engine.simulation import run_simulation
from app.main import app

client = TestClient(app)


def test_domain_router_distinguishes_stock_learning_from_generic_learning():
    assert classify_domain("What if I spend six months learning stock marketing?") == "stock_learning"
    assert classify_domain("What if I learn AI and build projects?") == "learning"


def test_domain_router_recognizes_vehicle_and_insurance_domains():
    assert classify_domain("What if I buy a 600 cc bike?") == "vehicle"
    assert classify_domain("What if I buy life insurance?") == "life_insurance"
    assert classify_domain("What if I choose health insurance with a lower premium?") == "health_insurance"


def test_domain_metadata_has_relevant_metrics():
    metadata = domain_metadata("What if I learn stock trading?")
    keys = {metric["key"] for metric in metadata["metrics"]}
    assert "paper_trading_sessions" in keys
    assert "strategies_tested" in keys
    assert "revenue" not in keys


def test_stock_learning_paths_only_track_learning_not_profit():
    scenarios = run_simulation(
        initial_state={"study_hours_per_week": 0, "learning_cost_inr": 0},
        branches=[
            "Build a consistent stock-market learning routine while keeping real money out of the process",
            "Follow a structured financial-analysis course and practice concepts with a paper portfolio",
            "Combine study with paper trading and review a learning journal before considering real-money risk",
        ],
        months=6,
        decision="What if I spend six months learning stock marketing?",
    )
    assert len(scenarios) == 3
    for scenario in scenarios:
        final = scenario.timeline[-1].values
        assert "paper_trading_sessions" in final
        assert "strategies_tested" in final
        assert "revenue" not in final
        assert any("No trading profits" in event for event in scenario.timeline[0].events)


def test_vehicle_calculator_sums_only_supplied_cost_inputs():
    scenarios = run_simulation(
        initial_state={
            "down_payment_inr": 50000,
            "monthly_emi_inr": 8000,
            "monthly_fuel_cost_inr": 2500,
            "monthly_maintenance_cost_inr": 1000,
            "annual_insurance_cost_inr": 12000,
        },
        branches=["Buy now and budget for full ownership costs"],
        months=3,
        decision="What if I buy a 600 cc motorcycle?",
    )
    final = scenarios[0].timeline[-1].values
    assert final["monthly_ownership_cost_inr"] == 11500
    assert final["cumulative_ownership_cost_inr"] == 84500


def test_insurance_calculator_uses_supplied_premium_and_coverage_only():
    scenarios = run_simulation(
        initial_state={"monthly_premium_inr": 1500, "coverage_amount_inr": 10000000},
        branches=["Compare affordable term-life cover"],
        months=6,
        decision="What if I buy life insurance?",
    )
    final = scenarios[0].timeline[-1].values
    assert final["annual_premium_inr"] == 18000
    assert final["coverage_amount_inr"] == 10000000
    assert final["cumulative_premium_paid_inr"] == 9000


def test_domains_endpoint_exposes_metric_catalog():
    response = client.get("/domains")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["domains"]}
    assert {"stock_learning", "vehicle", "life_insurance", "health_insurance", "education_career"} <= ids


def test_simulation_response_contains_domain_and_metric_metadata(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post("/simulate", json={
        "decision": "What if I spend six months learning stock marketing?",
        "months": 6,
        "initial_state": {},
    })
    assert response.status_code == 200
    data = response.json()
    assert data["domain"] == "stock_learning"
    assert data["domain_label"] == "Stock-market learning"
    assert any(metric["key"] == "paper_trading_sessions" for metric in data["metrics"])
    assert all("revenue" not in scenario["timeline"][-1]["values"] for scenario in data["scenarios"])
