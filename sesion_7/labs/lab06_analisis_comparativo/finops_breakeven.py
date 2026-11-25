#!/usr/bin/env python3
"""Lab 6b — Costo por millón de tokens autogestionado vs precio de una API (calculadora de punto de equilibrio).

Todos los precios son DATOS DE ENTRADA que usted debe tomar de las calculadoras oficiales vigentes.
Los valores por defecto son HIPOTÉTICOS (solo ilustran el método).

    USD/1M tokens = (USD/h de GPU) / (tok/s agregados × 3600 × utilización) × 1e6

Uso:
  python labs/lab06_analisis_comparativo/finops_breakeven.py --gpu-usd-h 2 --tok-s 1500 --api-usd-per-m 0.60
"""

from __future__ import annotations

import argparse


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gpu-usd-h", type=float, default=2.0, help="Costo por hora de la GPU (hipotético por defecto)")
    ap.add_argument("--tok-s", type=float, default=1500.0, help="Throughput agregado medido (use SU resultado del Lab 3)")
    ap.add_argument("--api-usd-per-m", type=float, default=0.60, help="Precio de la API por millón de tokens (hipotético)")
    a = ap.parse_args()

    print(f"GPU {a.gpu_usd_h} USD/h · {a.tok_s:.0f} tok/s agregados · API {a.api_usd_per_m} USD/M tokens  (valores de ejemplo)\n")
    print(f"{'Utilización':>12} | {'USD / 1M tokens':>16} | {'¿Más barato que la API?':>24}")
    for util in (0.05, 0.10, 0.25, 0.40, 0.60, 0.80, 1.00):
        cost = a.gpu_usd_h / (a.tok_s * 3600 * util) * 1e6
        print(f"{util:>12.0%} | {cost:>16.2f} | {'SÍ' if cost < a.api_usd_per_m else 'no':>24}")
    breakeven = a.gpu_usd_h / (a.tok_s * 3600 * a.api_usd_per_m) * 1e6
    if breakeven <= 1:
        print(f"\nPunto de equilibrio: utilización ≈ {breakeven:.0%} (por debajo conviene la API; por encima, la GPU propia).")
    else:
        print("\nCon estos datos la GPU propia no iguala a la API ni al 100 % de utilización.")


if __name__ == "__main__":
    main()
