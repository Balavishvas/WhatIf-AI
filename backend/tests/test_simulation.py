from app.engine.simulation import run_simulation


def test_scenarios_have_distinct_first_month_outcomes():
    scenarios = run_simulation(
        initial_state={"revenue": 10_000, "customers": 100, "cost": 3_000},
        branches=["optimistic", "realistic", "pessimistic"],
        months=3,
        decision="What if I invest more money in marketing?",
    )

    assert len(scenarios) == 3
    first_months = [scenario.timeline[0].values for scenario in scenarios]
    assert len({tuple(sorted(values.items())) for values in first_months}) == 3


def test_monthly_progression_uses_previous_month_state():
    scenarios = run_simulation(
        initial_state={"revenue": 10_000, "customers": 100, "cost": 3_000},
        branches=["optimistic"],
        months=3,
        decision="What if I invest more money in marketing?",
    )

    timeline = scenarios[0].timeline
    assert len(timeline) == 3
    assert [snapshot.month for snapshot in timeline] == [1, 2, 3]
    assert timeline[0].values["revenue"] == 11_200
    assert timeline[1].values["revenue"] == 12_544
    assert timeline[0].values["customers"] == 115
    assert timeline[1].values["customers"] == 132.25


def test_marketing_changes_cost_and_revenue():
    scenarios = run_simulation(
        initial_state={"revenue": 10_000, "cost": 3_000},
        branches=["optimistic"],
        months=1,
        decision="What if I invest more money in marketing?",
    )

    values = scenarios[0].timeline[0].values
    assert values["revenue"] > 10_000
    assert values["cost"] > 3_000


def test_zero_months_returns_empty_timeline():
    scenarios = run_simulation(
        initial_state={"revenue": 10_000},
        branches=["optimistic"],
        months=0,
        decision="What if I invest more money in marketing?",
    )

    assert scenarios[0].timeline == []
