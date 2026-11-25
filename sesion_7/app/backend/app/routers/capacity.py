"""Calculadora de memoria (pesos + KV cache)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas import CapacityRequest, CapacityResponse
from app.services import capacity as cap

router = APIRouter(prefix="/api/capacity", tags=["capacidad"])


@router.get("/presets")
async def presets() -> dict[str, object]:
    return {
        "models": {k: vars(v) for k, v in cap.PRESETS.items()},
        "quantizations": cap.QUANT_BITS,
    }


@router.post("/estimate", response_model=CapacityResponse)
async def estimate(req: CapacityRequest) -> CapacityResponse:
    try:
        spec = cap.resolve_spec(req.preset, req.params_billion, req.n_layers, req.n_kv_heads, req.head_dim)
        result = cap.estimate(
            spec,
            req.quant,
            req.context_tokens,
            req.concurrent_sequences,
            req.kv_dtype_bytes,
            req.gpu_memory_gb,
            req.overhead_gb,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return CapacityResponse(**result)  # type: ignore[arg-type]
