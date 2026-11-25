#!/usr/bin/env python3
"""Lab 4b — Comparación empírica de variantes cuantizadas del MISMO modelo.

Para cada etiqueta de modelo mide: memoria cargada (/api/ps), TTFT, velocidad de decode y una
"sonda de calidad" muy pequeña (8 preguntas con respuesta verificable por palabras clave).

IMPORTANTE: la sonda de calidad es un indicador burdo con muestra diminuta. NO es un benchmark
académico (para eso: lm-evaluation-harness, MMLU, etc.). Sirve para discutir el método, no para concluir.

Etiquetas de ejemplo (verifique que existan en https://ollama.com/library/llama3.2/tags):
  llama3.2:1b-instruct-q4_K_M   llama3.2:1b-instruct-q8_0   llama3.2:1b-instruct-fp16

Uso:
  ollama pull llama3.2:1b-instruct-q4_K_M && ollama pull llama3.2:1b-instruct-q8_0
  python labs/lab04_quantizacion/quant_compare.py --models llama3.2:1b-instruct-q4_K_M,llama3.2:1b-instruct-q8_0
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import DEFAULT_BASE_URL, fmt, make_client, ollama_ps, save_result, summarize, timed_chat, unload_model  # noqa: E402

PROBES: list[tuple[str, list[str]]] = [
    ("¿Cuál es la capital de Colombia? Responde con una palabra.", ["bogota"]),
    ("¿Cuánto es 15 multiplicado por 12? Responde solo con el número.", ["180"]),
    ("¿Cuál es el símbolo químico del agua?", ["h2o"]),
    ("¿Cuántos días tiene una semana? Responde solo con el número.", ["7", "siete"]),
    ("¿Qué planeta es conocido como el planeta rojo?", ["marte"]),
    ("Completa: el opuesto de 'caliente' es...", ["frio"]),
    ("¿Cuánto es 100 dividido entre 4? Responde solo con el número.", ["25"]),
    ("¿En qué continente está Egipto?", ["africa"]),
]


def norm(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


async def evaluate(base_url: str, model: str, runs: int, num_predict: int) -> dict:
    async with make_client(base_url) as c:
        await unload_model(c, model)
        cold = await timed_chat(c, model, "Hola", num_predict=4)
        perf = [await timed_chat(c, model, "Explica qué es la cuantización de un modelo de lenguaje.", num_predict=num_predict) for _ in range(runs)]
        ps = await ollama_ps(c)
        hits = 0
        for q, keys in PROBES:
            r = await timed_chat(c, model, q, num_predict=24, temperature=0.0)
            hits += any(k in norm(r["text"]) for k in keys)
        mem = next((m for m in ps if m.get("name") == model), None)
        await unload_model(c, model)
    return {
        "model": model,
        "cold_load_ms": cold["load_ms"],
        "memory_mb": (mem["size"] / 1e6) if mem else None,
        "ttft_ms": summarize([r["ttft_ms"] for r in perf]),
        "decode_tok_s": summarize([r["decode_tok_s"] for r in perf]),
        "quality_probe": {"correct": hits, "total": len(PROBES), "pct": 100 * hits / len(PROBES)},
    }


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--models", required=True, help="Etiquetas separadas por coma")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--num-predict", type=int, default=96)
    a = ap.parse_args()

    rows = []
    for m in a.models.split(","):
        print(f"Evaluando {m} …")
        rows.append(await evaluate(a.base_url, m.strip(), a.runs, a.num_predict))

    print(f"\n{'Modelo':<34}{'Mem (MB)':>10}{'Carga ms':>10}{'TTFT p50':>10}{'tok/s':>9}{'Calidad':>10}")
    for r in rows:
        print(f"{r['model']:<34}{fmt(r['memory_mb'], 0):>10}{fmt(r['cold_load_ms'], 0):>10}{fmt(r['ttft_ms']['p50']):>10}"
              f"{fmt(r['decode_tok_s']['mean']):>9}{r['quality_probe']['correct']:>6}/{r['quality_probe']['total']}")
    print(f"\nGuardado en {save_result('quantization', {'runs': rows}, a.base_url)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
