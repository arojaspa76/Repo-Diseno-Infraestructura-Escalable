#!/usr/bin/env python3
"""Lab 4a — Cuánta memoria ahorra cada cuantización (cálculo teórico, sin dependencias).

Uso:  python labs/lab04_quantizacion/quant_estimator.py --params-b 8.03
"""

from __future__ import annotations

import argparse

GIB = 1024**3
QUANT_BITS = {"fp16": 16.0, "q8_0": 8.5, "q6_k": 6.56, "q5_k_m": 5.7, "q4_k_m": 4.85, "q4_0": 4.5, "q3_k_m": 3.9, "q2_k": 2.96}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--params-b", type=float, default=8.03, help="Parámetros en miles de millones (8B = 8.03)")
    a = ap.parse_args()
    base = a.params_b * 1e9 * 16 / 8 / GIB
    print(f"Modelo de {a.params_b} B parámetros (bits efectivos por peso: valores aproximados de GGUF/llama.cpp)\n")
    print(f"{'Cuantización':<13}{'bits/peso':>10}{'Pesos (GB)':>12}{'vs FP16':>10}")
    for q, bits in QUANT_BITS.items():
        gb = a.params_b * 1e9 * bits / 8 / GIB
        print(f"{q:<13}{bits:>10.2f}{gb:>12.2f}{gb / base:>9.0%}")
    print("\nMenos bits = menos memoria y (normalmente) menos ancho de banda por token, a cambio de cierta pérdida de calidad.")


if __name__ == "__main__":
    main()
