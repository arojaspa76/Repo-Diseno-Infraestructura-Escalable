import math

import pytest

from finops_sim.calc import (
    break_even_api_vs_selfhosted,
    compare_purchase_strategies,
    estimate_capacity,
    percentile,
    read_utilization_csv,
    recommend_rightsizing,
)
from finops_sim.catalog import DEFAULT_CATALOG, load_catalog

CAT = load_catalog()


def test_catalog_loads_and_has_notice():
    assert "ILUSTRATIVOS" in CAT.notice and "gpu-s" in CAT.instances


def test_capacity_formula_hand_checked():
    # tps=50, 200 tok de salida -> servicio 4 s; ciclo 6 s (think 2) ; λ = 60/6 = 10 req/s
    plan = estimate_capacity(60, 200, 2.0, 50.0, target_utilization=0.5, min_replicas_ha=2)
    assert plan.requests_per_s == pytest.approx(10.0)
    assert plan.needed_tokens_per_s == pytest.approx(2000.0)
    # útil por instancia = 25 tok/s -> 80 instancias; con HA N+1 = 81
    assert plan.instances_for_load == 80 and plan.instances_with_ha == 81


def test_capacity_minimum_two_replicas_for_ha():
    plan = estimate_capacity(1, 10, 60.0, 100.0)
    assert plan.instances_for_load == 1 and plan.instances_with_ha == 2


def test_capacity_validation():
    with pytest.raises(ValueError):
        estimate_capacity(0, 100, 1, 10)
    with pytest.raises(ValueError):
        estimate_capacity(10, 100, 1, 10, target_utilization=1.5)


def test_strategies_ordering_and_math():
    inst = CAT.instance("gpu-s")  # $1.00/h
    rows = {r.name: r.monthly_usd for r in compare_purchase_strategies(CAT, inst, 2, 2, 100, "1y")}
    h = CAT.hours_per_month
    assert rows["all_on_demand"] == pytest.approx(2 * 1.0 * h + 2 * 1.0 * 100)
    assert rows["commit_baseline"] == pytest.approx(2 * 0.7 * h + 2 * 1.0 * 100)
    spot_rate = 1.0 * (1 - 0.65) * 1.10
    assert rows["commit_spot"] == pytest.approx(2 * 0.7 * h + 2 * spot_rate * 100)
    assert rows["commit_spot"] < rows["commit_baseline"] < rows["all_on_demand"]


def test_committing_peak_is_worse_when_peak_is_rare():
    inst = CAT.instance("gpu-s")
    rows = {r.name: r.monthly_usd for r in compare_purchase_strategies(CAT, inst, 2, 6, 40, "1y")}
    # pico raro (40 h/mes): comprometerlo 24x7 cuesta más que cubrirlo on-demand
    assert rows["all_commit_peak"] > rows["commit_baseline"]


def test_strategies_validation():
    inst = CAT.instance("gpu-s")
    with pytest.raises(ValueError):
        compare_purchase_strategies(CAT, inst, 1, 1, 9999, "1y")
    with pytest.raises(ValueError):
        compare_purchase_strategies(CAT, inst, 1, 1, 10, "5y")


def test_breakeven_math():
    inst = CAT.instance("gpu-s")
    be = break_even_api_vs_selfhosted(CAT, inst, 2, 800, 300, 0.5)
    api_req = (800 * 1.0 + 300 * 4.0) / 1e6
    assert be.api_cost_per_request_usd == pytest.approx(api_req)
    assert be.selfhosted_monthly_usd == pytest.approx(2 * 1.0 * 730)
    assert be.breakeven_requests_per_month == pytest.approx(1460 / api_req)
    # $1/h / (45 tok/s * 3600 * 0.5) * 1e6
    assert be.selfhosted_cost_per_mtok_out_at_util_usd == pytest.approx(1.0 / (45 * 3600 * 0.5) * 1e6)


def test_utilization_lowers_selfhosted_unit_cost():
    inst = CAT.instance("gpu-s")
    low = break_even_api_vs_selfhosted(CAT, inst, 1, 100, 100, 0.1)
    high = break_even_api_vs_selfhosted(CAT, inst, 1, 100, 100, 0.8)
    assert low.selfhosted_cost_per_mtok_out_at_util_usd == pytest.approx(
        8 * high.selfhosted_cost_per_mtok_out_at_util_usd
    )


def test_percentile():
    assert percentile([1, 2, 3, 4, 5], 50) == 3
    assert percentile([10], 95) == 10
    assert math.isclose(percentile([0, 100], 95), 95.0)
    with pytest.raises(ValueError):
        percentile([], 50)


def test_rightsizing_recommends_smaller_for_underused_instance():
    series = read_utilization_csv(DEFAULT_CATALOG.parent / "utilizacion_ejemplo.csv")
    adv = recommend_rightsizing(CAT, "gpu-m", series)
    assert adv.recommended != "gpu-m" and adv.monthly_saving_usd > 0


def test_rightsizing_keeps_busy_instance():
    adv = recommend_rightsizing(CAT, "gpu-s", [85.0] * 50)
    assert adv.recommended == "gpu-s" and adv.monthly_saving_usd == 0
