import pytest

from finops_tools import compare_compute_purchase_options, estimate_monthly_inference_cost


def test_inference_cost_hand_checked():
    r = estimate_monthly_inference_cost(200_000, 800, 300, 1.0, 4.0)
    assert r["input_cost_usd"] == 160.0 and r["output_cost_usd"] == 240.0
    assert r["total_monthly_usd"] == 400.0 and r["cost_per_request_usd"] == 0.002


def test_inference_cost_zero_requests():
    assert estimate_monthly_inference_cost(0, 10, 10, 1, 1)["cost_per_request_usd"] == 0.0


@pytest.mark.parametrize("bad", [-1, -0.5])
def test_negative_rejected(bad):
    with pytest.raises(ValueError):
        estimate_monthly_inference_cost(bad, 1, 1, 1, 1)


def test_purchase_options():
    r = compare_compute_purchase_options(1.0, 2, 0.30, 0.65, 0.10)
    assert r["on_demand_monthly_usd"] == 1460.0
    assert r["commitment_monthly_usd"] == 1022.0
    assert r["spot_monthly_usd"] == pytest.approx(562.1, abs=0.05)


def test_purchase_options_validation():
    with pytest.raises(ValueError):
        compare_compute_purchase_options(1.0, 0, 0.3, 0.6)
    with pytest.raises(ValueError):
        compare_compute_purchase_options(1.0, 1, 1.0, 0.6)
