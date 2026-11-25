#!/usr/bin/env python3
"""Lab 3c — Efecto de reutilizar un prefijo largo (reuso de KV cache entre peticiones).

Escenario típico de empresa: TODAS las peticiones comienzan con el mismo prompt de sistema largo
(políticas, instrucciones, documentación). Si el servidor reutiliza el KV cache de ese prefijo,
el *prefill* de las peticiones siguientes debería costar mucho menos.

Experimento (peticiones secuenciales, mismo modelo y mismo num_ctx):
  A) MISMO prefijo largo + pregunta distinta  → se espera prefill decreciente tras la 1ª petición.
  B) prefijo largo DIFERENTE en cada petición  → no hay prefijo reutilizable → prefill alto siempre.

Ojo: es una TENDENCIA esperada, no una garantía; depende de la versión del servidor y de su configuración.
Compare sus propios números y repórtelos tal como salen.

Uso:
  python labs/lab03_batching_kvcache/prefix_cache_experiment.py --model llama3.2:1b --prefix-tokens 800
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import DEFAULT_BASE_URL, filler_text, fmt, make_client, save_result, summarize, timed_chat  # noqa: E402

QUESTIONS = ["¿Qué es el prefill?", "¿Qué es el decode?", "¿Qué es el TTFT?", "¿Qué es el TPOT?", "¿Qué es un batch?", "¿Qué es PagedAttention?"]


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--model", default="llama3.2:1b")
    ap.add_argument("--prefix-tokens", type=int, default=800)
    ap.add_argument("--num-ctx", type=int, default=4096)
    ap.add_argument("--num-predict", type=int, default=16, help="Salida corta: aislamos el costo del prefill")
    args = ap.parse_args()

    shared = "Política institucional (leer con atención):\n" + filler_text(args.prefix_tokens)
    out: dict[str, list[dict]] = {"A_prefijo_compartido": [], "B_prefijo_distinto": []}
    async with make_client(args.base_url) as c:
        await timed_chat(c, args.model, "Hola", num_predict=4, num_ctx=args.num_ctx)  # carga el modelo
        for i, q in enumerate(QUESTIONS):
            r = await timed_chat(c, args.model, q, system=shared, num_predict=args.num_predict, num_ctx=args.num_ctx)
            r.pop("text"); out["A_prefijo_compartido"].append(r)
        for i, q in enumerate(QUESTIONS):
            unique = f"[doc-{i}-{'x' * (i + 1)}] " + shared  # el prefijo cambia desde el primer carácter
            r = await timed_chat(c, args.model, q, system=unique, num_predict=args.num_predict, num_ctx=args.num_ctx)
            r.pop("text"); out["B_prefijo_distinto"].append(r)

    print(f"{'#':>2} | {'A prefill ms':>12} | {'A TTFT ms':>10} | {'B prefill ms':>12} | {'B TTFT ms':>10}")
    for i in range(len(QUESTIONS)):
        a, b = out["A_prefijo_compartido"][i], out["B_prefijo_distinto"][i]
        print(f"{i + 1:>2} | {fmt(a['prompt_eval_ms']):>12} | {fmt(a['ttft_ms']):>10} | {fmt(b['prompt_eval_ms']):>12} | {fmt(b['ttft_ms']):>10}")
    for k, v in out.items():
        s = summarize([x["ttft_ms"] for x in v[1:]])
        print(f"{k}: TTFT medio (excluyendo la 1ª) = {fmt(s['mean'])} ms")
    print(f"\nGuardado en {save_result('prefix_cache', {'model': args.model, 'prefix_tokens': args.prefix_tokens, 'runs': out}, args.base_url)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
