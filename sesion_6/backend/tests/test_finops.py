from datetime import date, timedelta

import pytest

from app.finops import BudgetTracker, selfhosted_cost, shadow_api_cost


def test_shadow_cost_formula():
    # 1M tokens de entrada a $1 + 1M de salida a $4 = $5
    assert shadow_api_cost(1_000_000, 1_000_000, 1.0, 4.0) == pytest.approx(5.0)
    assert shadow_api_cost(0, 0, 1.0, 4.0) == 0.0


def test_selfhosted_cost_formula():
    assert selfhosted_cost(3600, 2.5) == pytest.approx(2.5)
    assert selfhosted_cost(1800, 2.0) == pytest.approx(1.0)


def test_negative_inputs_rejected():
    with pytest.raises(ValueError):
        shadow_api_cost(-1, 0, 1, 1)
    with pytest.raises(ValueError):
        selfhosted_cost(-1, 1)


def test_budget_alerts_fire_once_per_level():
    bt = BudgetTracker(limit_usd=1.0, alert_levels=[50, 80, 100])
    assert bt.record("c", 0.4, 10).new_alert is None
    s = bt.record("c", 0.2, 10)  # 60 %
    assert s.new_alert == 50 and not s.blocked
    assert bt.record("c", 0.05, 1).new_alert is None  # 65 %: sin alerta nueva
    s = bt.record("c", 0.2, 1)  # 85 %
    assert s.new_alert == 80
    s = bt.record("c", 0.2, 1)  # 105 %
    assert s.new_alert == 100 and s.blocked


def test_budget_resets_next_day():
    bt = BudgetTracker(limit_usd=1.0)
    today = date(2026, 1, 1)
    bt.record("c", 1.5, 1, today=today)
    assert bt.check("c", today=today).blocked
    assert not bt.check("c", today=today + timedelta(days=1)).blocked


def test_budget_isolated_per_client():
    bt = BudgetTracker(limit_usd=1.0)
    bt.record("a", 2.0, 1)
    assert bt.check("a").blocked and not bt.check("b").blocked
