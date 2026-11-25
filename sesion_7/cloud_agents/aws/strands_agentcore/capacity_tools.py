"""Herramientas (tools) COMPARTIDAS por todos los agentes de la sesión.

Misma capacidad en las tres nubes => se compara el FRAMEWORK, no la lógica de negocio.
Son funciones puras, de solo lectura y sin red: principio de mínimo privilegio para tools de agentes.

Este archivo es la fuente única. `scripts/sync_tools.sh` lo copia dentro de cada carpeta de ejemplo
para que cada una pueda desplegarse de forma independiente (Agent Engine, AgentCore, etc.).
NO edite las copias: edite este archivo y ejecute `make sync-tools`.
"""

from __future__ import annotations

GIB = 1024**3

# (parámetros en miles de millones, capas, cabezas KV, dimensión de cabeza) — config.json públicos de cada modelo.
MODELS: dict[str, tuple[float, int, int, int]] = {
    "llama-3.2-1b": (1.24, 16, 8, 64),
    "llama-3.2-3b": (3.21, 28, 8, 128),
    "llama-3.1-8b": (8.03, 32, 8, 128),
    "llama-3.1-70b": (70.6, 80, 8, 128),
}

# Bits efectivos aproximados por peso (GGUF / llama.cpp).
QUANT_BITS: dict[str, float] = {
    "fp16": 16.0, "q8_0": 8.5, "q6_k": 6.56, "q5_k_m": 5.7, "q4_k_m": 4.85, "q4_0": 4.5, "q3_k_m": 3.9, "q2_k": 2.96,
}


def list_supported_models() -> dict:
    """Lista los modelos y las cuantizaciones que la calculadora de capacidad conoce.

    Returns:
        Un diccionario con las claves 'models' y 'quantizations'.
    """
    return {"models": sorted(MODELS), "quantizations": sorted(QUANT_BITS)}


def estimate_gpu_fit(
    model: str,
    quantization: str,
    context_tokens: int,
    concurrent_sequences: int,
    gpu_memory_gb: float,
) -> dict:
    """Estima si un LLM cabe en una GPU (pesos + KV cache + overhead de 1.5 GB).

    Args:
        model: Nombre del modelo, p. ej. 'llama-3.1-8b'. Use list_supported_models para ver las opciones.
        quantization: Cuantización de los pesos, p. ej. 'fp16' o 'q4_k_m'.
        context_tokens: Tokens de contexto por conversación (prompt + salida).
        concurrent_sequences: Número de conversaciones simultáneas.
        gpu_memory_gb: Memoria de la GPU en GB.

    Returns:
        Desglose de memoria en GB, si cabe en la GPU y cuántas conversaciones caben como máximo.
    """
    if model not in MODELS:
        return {"error": f"Modelo desconocido: {model}", "supported": sorted(MODELS)}
    if quantization.lower() not in QUANT_BITS:
        return {"error": f"Cuantización desconocida: {quantization}", "supported": sorted(QUANT_BITS)}
    if min(context_tokens, concurrent_sequences) <= 0 or gpu_memory_gb <= 0:
        return {"error": "context_tokens, concurrent_sequences y gpu_memory_gb deben ser positivos"}

    params_b, layers, kv_heads, head_dim = MODELS[model]
    weights = params_b * 1e9 * QUANT_BITS[quantization.lower()] / 8 / GIB
    kv_one = 2 * layers * kv_heads * head_dim * 2.0 * context_tokens / GIB  # KV en FP16 (2 bytes)
    overhead = 1.5
    total = weights + kv_one * concurrent_sequences + overhead
    free_for_kv = gpu_memory_gb - weights - overhead
    return {
        "model": model,
        "quantization": quantization.lower(),
        "weights_gb": round(weights, 2),
        "kv_cache_per_sequence_gb": round(kv_one, 2),
        "kv_cache_total_gb": round(kv_one * concurrent_sequences, 2),
        "overhead_gb": overhead,
        "total_gb": round(total, 2),
        "gpu_memory_gb": gpu_memory_gb,
        "fits": total <= gpu_memory_gb,
        "max_concurrent_sequences": max(0, int(free_for_kv // kv_one)),
        "note": "Estimación teórica; valide con nvidia-smi sobre el hardware real.",
    }
