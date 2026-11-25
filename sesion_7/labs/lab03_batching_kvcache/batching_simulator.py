#!/usr/bin/env python3
"""Lab 3d — Simulador: batching ESTÁTICO vs batching CONTINUO (sin modelo, sin GPU).

Cada "paso de decode" genera 1 token para todas las peticiones activas del batch.
  * Estático:  se forma un batch de B peticiones y se espera a que TERMINE LA MÁS LARGA.
               Las que terminan antes dejan "huecos" (slots ociosos).
  * Continuo:  apenas una petición termina, su slot se rellena con la siguiente en cola.

Es una SIMULACIÓN pedagógica (longitudes de salida aleatorias con semilla fija), no una medición.

Uso:  python labs/lab03_batching_kvcache/batching_simulator.py --requests 64 --batch 8
"""

from __future__ import annotations

import argparse
import random
from collections import deque


def static_batching(lengths: list[int], batch: int) -> tuple[int, int]:
    steps = used = 0
    for i in range(0, len(lengths), batch):
        group = lengths[i : i + batch]
        steps += max(group)       # el grupo dura lo que dure la petición más larga
        used += sum(group)        # tokens realmente útiles
    return steps, used


def continuous_batching(lengths: list[int], batch: int) -> tuple[int, int]:
    queue = deque(lengths)
    active: list[int] = []
    steps = used = 0
    while queue or active:
        while queue and len(active) < batch:   # rellena huecos de inmediato
            active.append(queue.popleft())
        steps += 1
        used += len(active)
        active = [r - 1 for r in active if r - 1 > 0]
    return steps, used


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--requests", type=int, default=64)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--min-len", type=int, default=10)
    ap.add_argument("--max-len", type=int, default=400)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    rng = random.Random(a.seed)
    lengths = [rng.randint(a.min_len, a.max_len) for _ in range(a.requests)]
    s_steps, s_used = static_batching(lengths, a.batch)
    c_steps, c_used = continuous_batching(lengths, a.batch)
    assert s_used == c_used == sum(lengths)
    print(f"{a.requests} peticiones, batch={a.batch}, longitudes de salida {a.min_len}–{a.max_len} tokens (semilla {a.seed})")
    print(f"Batching estático : {s_steps:>6} pasos | utilización de slots {100 * s_used / (s_steps * a.batch):5.1f}%")
    print(f"Batching continuo : {c_steps:>6} pasos | utilización de slots {100 * c_used / (c_steps * a.batch):5.1f}%")
    print(f"Mejora de throughput (tokens por paso): {s_steps / c_steps:.2f}x")


if __name__ == "__main__":
    main()
