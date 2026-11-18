"""Prueba la herramienta de carga contra el gateway real en memoria (proveedor falso)."""

import sys
from pathlib import Path

import httpx
import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.main import create_app  # noqa: E402
from tests.conftest import FakeProvider, make_settings  # noqa: E402

import loadgen  # noqa: E402


@pytest.mark.asyncio
async def test_load_against_in_memory_gateway():
    app = create_app(make_settings(daily_budget_usd_per_client=100.0), FakeProvider())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://gw") as client:
        rep, samples = await loadgen.run_load(
            client, users=3, requests=9, slo_p95_s=5.0, slo_ttft_s=5.0, slo_availability=0.999
        )
    assert rep.requests == 9 and rep.success == 9 and rep.errors == 0
    assert rep.output_tokens_per_s > 0 and rep.ttft_p95_s is not None
    assert rep.shadow_cost_usd == pytest.approx(9 * 0.0003)
    assert all(d["pass"] for d in rep.slo.values())


def test_error_budget_accounting():
    samples = [loadgen.Sample(True, 200, 1.0, 0.1, 10)] * 998 + [loadgen.Sample(False, 502, 1.0)] * 2
    rep = loadgen.build_report(samples, users=5, wall_s=10.0, slo_availability=0.999)
    # 2 errores de 1000 = 0,2 % -> consume 200 % de un presupuesto de error de 0,1 %
    assert rep.slo["availability"]["error_budget_consumed_pct"] == pytest.approx(200.0)
    assert rep.slo["availability"]["pass"] is False


def test_percentile_edges():
    assert loadgen.percentile([], 95) is None
    assert loadgen.percentile([3.0], 99) == 3.0


def test_invalid_args():
    with pytest.raises(ValueError):
        import asyncio
        asyncio.run(loadgen.run_load(None, users=0, requests=1))  # type: ignore[arg-type]
