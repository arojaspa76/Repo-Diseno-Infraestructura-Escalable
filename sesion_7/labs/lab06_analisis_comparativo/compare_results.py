#!/usr/bin/env python3
"""Lab 6 — Análisis comparativo: convierte los JSON de results/ en un reporte Markdown + gráficas.

Lee el resultado MÁS RECIENTE de cada tipo (concurrency, quantization, prefix_cache, embedding_cache,
profiling) y genera:
  results/REPORTE.md              tablas listas para pegar en su informe
  results/concurrencia.png        throughput agregado vs latencia p95 según concurrencia
  results/cuantizacion.png        memoria y velocidad por variante cuantizada

Uso:  python labs/lab06_analisis_comparativo/compare_results.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import RESULTS_DIR, fmt  # noqa: E402


def latest(kind: str) -> dict | None:
    files = sorted(RESULTS_DIR.glob(f"{kind}_*.json"))
    return json.loads(files[-1].read_text(encoding="utf-8")) if files else None


def main() -> int:
    md: list[str] = ["# Reporte comparativo — Sesión 7", ""]
    found = 0

    if d := latest("concurrency"):
        found += 1
        lv = d["levels"]
        base = lv[0]["aggregate_tok_s"]
        md += [f"## Concurrencia vs throughput ({d['model']})", "", f"Entorno: `{d['environment']['platform']}`, {d['environment']['cpu_count']} CPU, {d['environment']['timestamp_utc']}", "",
               "| Concurrencia | tok/s agregados | Speedup | TTFT p50 (ms) | TTFT p95 (ms) | TPOT p50 (ms) | Total p95 (ms) |", "|---:|---:|---:|---:|---:|---:|---:|"]
        for r in lv:
            md.append(f"| {r['concurrency']} | {r['aggregate_tok_s']:.1f} | {r['aggregate_tok_s'] / base:.2f}x | {fmt(r['ttft_ms']['p50'])} | {fmt(r['ttft_ms']['p95'])} | {fmt(r['tpot_ms']['p50'], 2)} | {fmt(r['total_ms']['p95'])} |")
        md.append("")
        fig, ax1 = plt.subplots(figsize=(7, 4))
        xs = [r["concurrency"] for r in lv]
        ax1.plot(xs, [r["aggregate_tok_s"] for r in lv], "o-", color="#0b5fff", label="Throughput agregado (tok/s)")
        ax1.set_xlabel("Peticiones concurrentes"); ax1.set_ylabel("tok/s", color="#0b5fff")
        ax2 = ax1.twinx()
        ax2.plot(xs, [r["total_ms"]["p95"] for r in lv], "s--", color="#d92d20", label="Latencia total p95 (ms)")
        ax2.set_ylabel("ms", color="#d92d20")
        ax1.set_title("Compromiso latencia ↔ throughput"); ax1.set_xscale("log", base=2); ax1.grid(alpha=.3)
        fig.tight_layout(); fig.savefig(RESULTS_DIR / "concurrencia.png", dpi=140); plt.close(fig)
        md += ["![concurrencia](concurrencia.png)", ""]

    if d := latest("quantization"):
        found += 1
        rows = d["runs"]
        md += ["## Cuantización", "", "| Modelo | Memoria (MB) | Carga en frío (ms) | TTFT p50 (ms) | Decode (tok/s) | Sonda de calidad |", "|---|---:|---:|---:|---:|---:|"]
        for r in rows:
            q = r["quality_probe"]
            md.append(f"| {r['model']} | {fmt(r['memory_mb'], 0)} | {fmt(r['cold_load_ms'], 0)} | {fmt(r['ttft_ms']['p50'])} | {fmt(r['decode_tok_s']['mean'])} | {q['correct']}/{q['total']} |")
        md += ["", "> La sonda de calidad (8 preguntas) es un indicador burdo; no sustituye un benchmark.", ""]
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
        names = [r["model"].split(":")[-1] for r in rows]
        ax[0].bar(names, [r["memory_mb"] or 0 for r in rows], color="#0b5fff"); ax[0].set_title("Memoria (MB)")
        ax[1].bar(names, [r["decode_tok_s"]["mean"] or 0 for r in rows], color="#f59e0b"); ax[1].set_title("Decode (tok/s)")
        for a in ax: a.tick_params(axis="x", rotation=20)
        fig.tight_layout(); fig.savefig(RESULTS_DIR / "cuantizacion.png", dpi=140); plt.close(fig)
        md += ["![cuantizacion](cuantizacion.png)", ""]

    if d := latest("prefix_cache"):
        found += 1
        a_, b_ = d["runs"]["A_prefijo_compartido"], d["runs"]["B_prefijo_distinto"]
        md += ["## Reuso de prefijo (KV cache)", "", "| # | A prefill (ms) | A TTFT (ms) | B prefill (ms) | B TTFT (ms) |", "|---:|---:|---:|---:|---:|"]
        for i, (x, y) in enumerate(zip(a_, b_), 1):
            md.append(f"| {i} | {fmt(x['prompt_eval_ms'])} | {fmt(x['ttft_ms'])} | {fmt(y['prompt_eval_ms'])} | {fmt(y['ttft_ms'])} |")
        md.append("")

    if d := latest("embedding_cache"):
        found += 1
        md += ["## Cache de embeddings", "", "| Ronda | A ingenua (ms) | B lote (ms) | C cache+lote (ms) | Textos enviados en C |", "|---:|---:|---:|---:|---:|"]
        for r in d["rounds"]:
            md.append(f"| {r['round']} | {r['A_ingenua_ms']:.0f} | {r['B_lote_ms']:.0f} | {r['C_cache_lote_ms']:.0f} | {r['textos_enviados_en_C']} |")
        md.append("")

    if d := latest("profiling"):
        found += 1
        i = d["inference"]
        md += ["## Profiling de una inferencia", "", f"- Arranque en frío: **{d['cold']}** · TTFT {fmt(i['ttft_ms'])} ms · prefill {fmt(i['prompt_eval_ms'])} ms · carga {fmt(i['load_ms'])} ms",
               f"- TPOT {fmt(i['tpot_ms'], 2)} ms/token · decode {fmt(i['decode_tok_s'])} tok/s",
               f"- Red (p50): TCP {fmt(d['network']['tcp_connect_p50_ms'], 2)} ms, HTTP {fmt(d['network']['http_request_p50_ms'], 2)} ms", ""]

    if not found:
        print("No hay resultados en results/. Ejecute antes los laboratorios 2–5.")
        return 1
    md += ["---", "*Generado por labs/lab06_analisis_comparativo/compare_results.py. Los números son de SU entorno: indíquelo siempre en su informe.*"]
    out = RESULTS_DIR / "REPORTE.md"
    out.write_text("\n".join(md), encoding="utf-8")
    print(f"Reporte generado: {out} ({found} secciones)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
