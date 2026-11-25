#!/usr/bin/env python3
"""Lab 3b — Calculadora de KV cache y de capacidad de GPU (sin dependencias).

    bytes_KV = 2 (K y V) × capas × cabezas_KV × dim_cabeza × tokens × bytes_por_elemento × secuencias

Ejemplos:
  python labs/lab03_batching_kvcache/kv_cache_calculator.py --preset llama-3.1-8b --quant q4_k_m --gpu-gb 16
  python labs/lab03_batching_kvcache/kv_cache_calculator.py --layers 32 --kv-heads 8 --head-dim 128 --params-b 8 --gpu-gb 24

Nota: esta copia es independiente de app/backend/app/services/capacity.py (mismas fórmulas) para que el
laboratorio se pueda ejecutar sin instalar nada. Los valores de los presets salen de los config.json públicos.
"""

from __future__ import annotations

import argparse

GIB = 1024**3
PRESETS = {  # params(B), capas, cabezas KV, dim cabeza
    "llama-3.2-1b": (1.24, 16, 8, 64),
    "llama-3.2-3b": (3.21, 28, 8, 128),
    "llama-3.1-8b": (8.03, 32, 8, 128),
    "llama-3.1-70b": (70.6, 80, 8, 128),
}
QUANT_BITS = {"fp16": 16.0, "q8_0": 8.5, "q6_k": 6.56, "q5_k_m": 5.7, "q4_k_m": 4.85, "q4_0": 4.5, "q3_k_m": 3.9, "q2_k": 2.96}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preset", choices=sorted(PRESETS))
    ap.add_argument("--params-b", type=float)
    ap.add_argument("--layers", type=int)
    ap.add_argument("--kv-heads", type=int)
    ap.add_argument("--head-dim", type=int)
    ap.add_argument("--quant", default="fp16", choices=sorted(QUANT_BITS))
    ap.add_argument("--kv-bytes", type=float, default=2.0, help="2=FP16 (defecto), 1=INT8/FP8 KV")
    ap.add_argument("--gpu-gb", type=float, default=24.0)
    ap.add_argument("--overhead-gb", type=float, default=1.5)
    a = ap.parse_args()

    if a.preset:
        params, layers, kvh, hd = PRESETS[a.preset]
    elif None not in (a.params_b, a.layers, a.kv_heads, a.head_dim):
        params, layers, kvh, hd = a.params_b, a.layers, a.kv_heads, a.head_dim
    else:
        ap.error("Indique --preset o bien --params-b --layers --kv-heads --head-dim")

    weights = params * 1e9 * QUANT_BITS[a.quant] / 8 / GIB
    per_token = 2 * layers * kvh * hd * a.kv_bytes
    print(f"Modelo: {a.preset or 'personalizado'} | cuantización {a.quant} | GPU {a.gpu_gb} GB | overhead {a.overhead_gb} GB")
    print(f"Pesos: {weights:.2f} GB | KV cache por token: {per_token / 1024:.1f} KiB\n")
    free = a.gpu_gb - weights - a.overhead_gb
    print(f"Memoria libre para KV cache: {max(free, 0):.2f} GB\n")
    print("Contexto | KV por conversación | Máx. conversaciones simultáneas en esta GPU")
    for ctx in (2048, 4096, 8192, 16384, 32768, 131072):
        kv = per_token * ctx / GIB
        n = max(0, int(free // kv)) if free > 0 else 0
        print(f"{ctx:>8} | {kv:>16.2f} GB | {n:>6}")
    if free <= 0:
        print("\n⚠ Los pesos no caben en esta GPU: cuantice más o use más memoria/GPUs.")


if __name__ == "__main__":
    main()
