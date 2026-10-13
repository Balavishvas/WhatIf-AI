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


def test_baseline_branch_keeps_values_unchanged():
    scenarios = run_simulation(
        initial_state={"revenue": 10000, "customers": 100},
        branches=["continue current path"],
        months=2,
        decision="What if I invest more in marketing?",
    )
    assert scenarios[0].timeline[0].values == {"revenue": 10000, "customers": 100}
    assert scenarios[0].timeline[1].values == {"revenue": 10000, "customers": 100}


def test_scenario_wording_changes_monthly_rate_and_explains_it():
    scenarios = run_simulation(
        initial_state={"revenue": 10000},
        branches=[
            "continue current path",
            "increase marketing investment optimistically",
            "reduce marketing spend to limit risk",
        ],
        months=1,
        decision="What if I increase marketing spend?",
    )
    baseline, growth, cautious = [s.timeline[0] for s in scenarios]
    assert baseline.values["revenue"] == 10000
    assert growth.values["revenue"] > 10000
    assert cautious.values["revenue"] < 10000
    assert "starter rate" in growth.events[0]
    assert "starter rate" in cautious.events[0]


def test_career_decision_uses_career_metrics():
    scenarios = run_simulation(
        initial_state={"savings": 20000, "monthly_expenses": 2500},
        branches=["continue current path", "transition gradually with a balanced approach"],
        months=1,
        decision="What if I quit my job to build an AI startup?",
    )
    baseline, balanced = [s.timeline[0].values for s in scenarios]
    assert baseline == {"savings": 20000, "monthly_expenses": 2500}
    assert balanced["savings"] > 20000
    assert balanced["monthly_expenses"] > 2500
