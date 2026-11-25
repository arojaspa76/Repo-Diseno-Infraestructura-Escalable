#!/usr/bin/env python3
"""Lab 5 — Cache de embeddings + batching: cuánto se ahorra.

Tres estrategias para obtener los embeddings de un corpus donde muchos textos se repiten
(p. ej. preguntas frecuentes, fragmentos de documentos re-indexados):

  A) Ingenua      : una llamada HTTP por texto, sin cache.
  B) Por lotes    : una sola llamada con todos los textos, sin cache.
  C) Cache + lote : se consulta la cache y SOLO los textos nuevos (sin duplicados) se envían en un lote.

Se ejecutan varias rondas; en C las rondas siguientes deberían ser casi gratis (alto hit rate).

Uso:
  python labs/lab05_cache_embeddings/embedding_cache_bench.py --model nomic-embed-text --size 200 --repeat-ratio 0.5
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "labs"))
sys.path.insert(0, str(ROOT / "app" / "backend"))  # reutiliza la MISMA cache que usa la API
from _common import DEFAULT_BASE_URL, fmt, make_client, save_result  # noqa: E402
from app.services.cache import EmbeddingCache  # noqa: E402


def build_corpus(size: int, repeat_ratio: float, seed: int = 11) -> list[str]:
    rng = random.Random(seed)
    n_unique = max(1, int(size * (1 - repeat_ratio)))
    unique = [f"Fragmento {i}: el servicio de inferencia debe cumplir un SLO de latencia p95 inferior a {500 + i} ms." for i in range(n_unique)]
    return [rng.choice(unique) if i >= n_unique else unique[i] for i in range(size)]


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--model", default="nomic-embed-text")
    ap.add_argument("--size", type=int, default=200)
    ap.add_argument("--repeat-ratio", type=float, default=0.5, help="Fracción de textos repetidos (0–0.95)")
    ap.add_argument("--rounds", type=int, default=3)
    a = ap.parse_args()

    corpus = build_corpus(a.size, a.repeat_ratio)
    print(f"Corpus: {len(corpus)} textos, {len(set(corpus))} únicos | modelo {a.model} | {a.rounds} rondas")
    cache = EmbeddingCache(":memory:")
    rows = []
    async with make_client(a.base_url) as c:
        async def embed(batch: list[str]) -> list[list[float]]:
            r = await c.post("/api/embed", json={"model": a.model, "input": batch})
            r.raise_for_status()
            return r.json()["embeddings"]

        await embed(["calentamiento"])  # carga el modelo
        for rnd in range(1, a.rounds + 1):
            t = time.perf_counter()
            for text in corpus:
                await embed([text])
            ta = (time.perf_counter() - t) * 1000

            t = time.perf_counter()
            await embed(corpus)
            tb = (time.perf_counter() - t) * 1000

            t = time.perf_counter()
            cached = cache.get_many(a.model, corpus)
            miss = sorted({corpus[i] for i in range(len(corpus)) if i not in cached})
            if miss:
                cache.put_many(a.model, miss, await embed(miss))
            tc = (time.perf_counter() - t) * 1000
            st = cache.stats()
            rows.append({"round": rnd, "A_ingenua_ms": ta, "B_lote_ms": tb, "C_cache_lote_ms": tc, "textos_enviados_en_C": len(miss), "cache": st})
            print(f"ronda {rnd}: A={ta:8.0f} ms | B={tb:7.0f} ms | C={tc:7.0f} ms ({len(miss)} textos enviados) | hit rate acumulado {st['hit_rate']:.0%}")

    last = rows[-1]
    print(f"\nRonda {a.rounds}: lote vs ingenua = {last['A_ingenua_ms'] / last['B_lote_ms']:.1f}x | cache+lote vs ingenua = {last['A_ingenua_ms'] / max(last['C_cache_lote_ms'], 0.01):.0f}x")
    print(f"Guardado en {save_result('embedding_cache', {'model': a.model, 'size': a.size, 'unique': len(set(corpus)), 'rounds': rows}, a.base_url)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
