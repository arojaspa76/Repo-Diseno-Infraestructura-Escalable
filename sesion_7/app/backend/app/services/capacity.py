"""Estimador de memoria: pesos del modelo + KV cache.

Fórmula del KV cache (por secuencia):

    bytes = 2 (K y V) * n_layers * n_kv_heads * head_dim * context_tokens * bytes_por_elemento

Los valores de arquitectura de los presets provienen de los config.json públicos de
cada modelo; verifíquelos en la model card antes de usarlos en un diseño real.
Los "bits por peso" de la cuantización GGUF son aproximaciones comunes de llama.cpp.
"""

from __future__ import annotations

from dataclasses import dataclass

GIB = 1024**3


@dataclass(frozen=True)
class ModelSpec:
    params_billion: float
    n_layers: int
    n_kv_heads: int
    head_dim: int


PRESETS: dict[str, ModelSpec] = {
    "llama-3.2-1b": ModelSpec(1.24, 16, 8, 64),
    "llama-3.2-3b": ModelSpec(3.21, 28, 8, 128),
    "llama-3.1-8b": ModelSpec(8.03, 32, 8, 128),
    "llama-3.1-70b": ModelSpec(70.6, 80, 8, 128),
}

# Bits efectivos aproximados por peso.
QUANT_BITS: dict[str, float] = {
    "fp32": 32.0,
    "fp16": 16.0,
    "bf16": 16.0,
    "q8_0": 8.5,
    "q6_k": 6.56,
    "q5_k_m": 5.7,
    "q4_k_m": 4.85,
    "q4_0": 4.5,
    "q3_k_m": 3.9,
    "q2_k": 2.96,
}


def weights_gb(params_billion: float, quant: str) -> float:
    bits = QUANT_BITS.get(quant.lower())
    if bits is None:
        raise ValueError(f"Cuantización desconocida: {quant!r}. Opciones: {sorted(QUANT_BITS)}")
    return params_billion * 1e9 * bits / 8 / GIB


def kv_cache_gb(
    spec: ModelSpec, context_tokens: int, concurrent_sequences: int = 1, kv_dtype_bytes: float = 2.0
) -> float:
    per_token = 2 * spec.n_layers * spec.n_kv_heads * spec.head_dim * kv_dtype_bytes
    return per_token * context_tokens * concurrent_sequences / GIB


def resolve_spec(
    preset: str | None,
    params_billion: float | None,
    n_layers: int | None,
    n_kv_heads: int | None,
    head_dim: int | None,
) -> ModelSpec:
    if preset:
        try:
            return PRESETS[preset.lower()]
        except KeyError as exc:
            raise ValueError(f"Preset desconocido: {preset!r}. Opciones: {sorted(PRESETS)}") from exc
    if None in (params_billion, n_layers, n_kv_heads, head_dim):
        raise ValueError("Indique 'preset' o bien params_billion, n_layers, n_kv_heads y head_dim")
    return ModelSpec(params_billion, n_layers, n_kv_heads, head_dim)  # type: ignore[arg-type]


def estimate(
    spec: ModelSpec,
    quant: str,
    context_tokens: int,
    concurrent_sequences: int,
    kv_dtype_bytes: float = 2.0,
    gpu_memory_gb: float | None = None,
    overhead_gb: float = 1.5,
) -> dict[str, object]:
    w = weights_gb(spec.params_billion, quant)
    kv_one = kv_cache_gb(spec, context_tokens, 1, kv_dtype_bytes)
    kv_all = kv_one * concurrent_sequences
    total = w + kv_all + overhead_gb
    notes = [
        "Estimación teórica: no incluye fragmentación, activaciones temporales ni la implementación del servidor.",
        "Valide siempre con nvidia-smi / ollama ps sobre su hardware real.",
    ]
    fits: bool | None = None
    max_seq: int | None = None
    if gpu_memory_gb is not None:
        fits = total <= gpu_memory_gb
        free_for_kv = gpu_memory_gb - w - overhead_gb
        max_seq = max(0, int(free_for_kv // kv_one)) if kv_one > 0 else None
        if free_for_kv <= 0:
            notes.append("Los pesos ya no caben en la GPU indicada: considere cuantizar o usar más GPUs.")
    return {
        "weights_gb": round(w, 3),
        "kv_cache_gb": round(kv_all, 3),
        "kv_cache_per_sequence_gb": round(kv_one, 3),
        "overhead_gb": overhead_gb,
        "total_gb": round(total, 3),
        "fits_in_gpu": fits,
        "max_sequences_that_fit": max_seq,
        "notes": notes,
    }
