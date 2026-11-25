#!/usr/bin/env python3
"""Lab 3a — Concurrencia vs throughput y latencia (batching en acción).

Idea: al subir el número de peticiones simultáneas el servidor las agrupa en batch.
  * El THROUGHPUT AGREGADO (tokens/s de todo el sistema) suele subir...
  * ...pero la LATENCIA de cada usuario (TTFT, TPOT) también sube.
Ese compromiso latencia↔throughput es el corazón de la sesión.

Para que Ollama atienda peticiones en paralelo, inícielo con OLLAMA_NUM_PARALLEL>1
(ver README del laboratorio).

Uso:
  python labs/lab03_batching_kvcache/bench_concurrency.py --model llama3.2:1b --levels 1,2,4,8
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import DEFAULT_BASE_URL, fmt, make_client, save_result, summarize, timed_chat  # noqa: E402

PROMPTS = [
    "Explica en un párrafo qué es el batching continuo en servidores de LLM.",
    "Describe con una analogía qué es el KV cache.",
    "¿Qué diferencia hay entre la fase prefill y la fase decode?",
    "Menciona tres técnicas para reducir la latencia de un LLM.",
]


async def run_level(base_url: str, model: str, concurrency: int, total: int, num_predict: int) -> dict:
    sem = asyncio.Semaphore(concurrency)
    async with make_client(base_url) as client:
        async def one(i: int) -> dict:
            async with sem:
                return await timed_chat(client, model, PROMPTS[i % len(PROMPTS)], num_predict=num_predict)

        t0 = time.perf_counter()
        results = await asyncio.gather(*(one(i) for i in range(total)))
        wall = time.perf_counter() - t0

    tokens = sum(r["completion_tokens"] for r in results)
    return {
        "concurrency": concurrency,
        "requests": total,
        "wall_s": wall,
        "aggregate_tok_s": tokens / wall,
        "ttft_ms": summarize([r["ttft_ms"] for r in results]),
        "tpot_ms": summarize([r["tpot_ms"] for r in results]),
        "total_ms": summarize([r["total_ms"] for r in results]),
        "per_request_decode_tok_s": summarize([r["decode_tok_s"] for r in results]),
    }


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--model", default="llama3.2:1b")
    ap.add_argument("--levels", default="1,2,4,8", help="Niveles de concurrencia separados por coma")
    ap.add_argument("--requests-per-level", type=int, default=8)
    ap.add_argument("--num-predict", type=int, default=64)
    args = ap.parse_args()
    levels = [int(x) for x in args.levels.split(",")]

    print(f"== Lab 3a: {args.model} @ {args.base_url} · niveles {levels} ==")
    async with make_client(args.base_url) as c:  # calentamiento: carga el modelo y evita contaminar el nivel 1
        await timed_chat(c, args.model, "Hola", num_predict=8)

    rows = []
    for lvl in levels:
        row = await run_level(args.base_url, args.model, lvl, max(args.requests_per_level, lvl), args.num_predict)
        rows.append(row)
        print(f"  concurrencia {lvl:>2}: {row['aggregate_tok_s']:7.1f} tok/s agregados | "
              f"TTFT p50 {fmt(row['ttft_ms']['p50'])} ms, p95 {fmt(row['ttft_ms']['p95'])} ms | "
              f"TPOT p50 {fmt(row['tpot_ms']['p50'], 2)} ms | total p95 {fmt(row['total_ms']['p95'])} ms")

    base = rows[0]["aggregate_tok_s"]
    print("\nConcurrencia | tok/s agregados | speedup vs 1 | TTFT p95 (ms) | total p95 (ms)")
    for r in rows:
        print(f"{r['concurrency']:>12} | {r['aggregate_tok_s']:>15.1f} | {r['aggregate_tok_s'] / base:>11.2f}x | "
              f"{fmt(r['ttft_ms']['p95']):>13} | {fmt(r['total_ms']['p95']):>14}")
    path = save_result("concurrency", {"model": args.model, "num_predict": args.num_predict, "levels": rows}, args.base_url)
    print(f"\nGuardado en {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
