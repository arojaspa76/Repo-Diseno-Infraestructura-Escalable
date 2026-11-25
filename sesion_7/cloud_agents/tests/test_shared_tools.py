"""Pruebas de las herramientas compartidas y de que las copias por ejemplo estén sincronizadas."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "shared"))
import capacity_tools as ct  # noqa: E402

COPIES = [
    "gcp/adk_agent/capacity_advisor/capacity_tools.py",
    "azure/agent_framework/capacity_tools.py",
    "azure/semantic_kernel/capacity_tools.py",
    "azure/autogen/capacity_tools.py",
    "azure/langgraph/capacity_tools.py",
    "aws/strands_agentcore/capacity_tools.py",
]


def test_known_values():
    # Llama 3.1 8B, contexto 8192, KV FP16 => 1 GiB por conversación (128 KiB/token).
    r = ct.estimate_gpu_fit("llama-3.1-8b", "fp16", 8192, 1, 24)
    assert r["kv_cache_per_sequence_gb"] == pytest.approx(1.0)
    assert r["weights_gb"] == pytest.approx(14.96, abs=0.01)


def test_scenario_used_in_slides_and_labs():
    # 24 GB, 8 conversaciones de 8192: FP16 NO cabe (≈24.5 GB), Q8_0 SÍ cabe (≈17.5 GB).
    fp16 = ct.estimate_gpu_fit("llama-3.1-8b", "fp16", 8192, 8, 24)
    q8 = ct.estimate_gpu_fit("llama-3.1-8b", "q8_0", 8192, 8, 24)
    assert fp16["fits"] is False and fp16["total_gb"] == pytest.approx(24.46, abs=0.02)
    assert q8["fits"] is True and q8["total_gb"] == pytest.approx(17.45, abs=0.02)


def test_errors_are_returned_not_raised():
    assert "error" in ct.estimate_gpu_fit("gpt-x", "fp16", 1, 1, 1)
    assert "error" in ct.estimate_gpu_fit("llama-3.1-8b", "fp99", 1, 1, 1)
    assert "error" in ct.estimate_gpu_fit("llama-3.1-8b", "fp16", 0, 1, 1)


@pytest.mark.parametrize("rel", COPIES)
def test_copies_are_in_sync(rel: str):
    copy = HERE / rel
    assert copy.exists(), f"Falta {rel}: ejecute `make sync-tools`"
    assert copy.read_text() == (HERE / "shared/capacity_tools.py").read_text(), f"{rel} desincronizado: `make sync-tools`"
