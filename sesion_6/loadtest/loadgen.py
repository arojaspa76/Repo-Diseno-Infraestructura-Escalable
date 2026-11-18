"""Generador de carga y verificación de SLO para el gateway (sin dependencias extra).

Mide lo que importa en inferencia LLM:
  * TTFT  (Time To First Token): percepción de "respuesta inmediata".
  * TPOT  (Time Per Output Token): fluidez del texto durante la generación.
  * Latencia end-to-end p50/p95/p99.
  * Throughput en tokens/s y solicitudes/s.
  * Tasa de error y consumo del *error budget* de un SLO de disponibilidad.
  * Costo sombra acumulado (para convertir carga en dinero: FinOps).

Uso:
  python loadgen.py --url http://localhost:8000 --users 4 --requests 20 \
      --slo-p95-s 20 --slo-ttft-s 5 --slo-availability 0.99
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
import time
from dataclasses import asdict, dataclass, field

import httpx

DEFAULT_PROMPTS = [
    "Explica en dos frases qué es el rightsizing en la nube.",
    "Dame tres ideas para reducir el costo de inferencia de un LLM.",
    "¿Qué diferencia hay entre instancias spot y reservadas?",
    "Resume qué es un presupuesto (budget) en FinOps.",
]


@dataclass
class Sample:
    ok: bool
    status: int
    total_s: float
    ttft_s: float | None = None
    completion_tokens: int = 0
    prompt_tokens: int = 0
    shadow_usd: float = 0.0
    error: str | None = None


@dataclass
class Report:
    users: int
    requests: int
    wall_s: float
    success: int
    errors: int
    error_rate: float
    status_counts: dict[str, int]
    latency_p50_s: float | None
    latency_p95_s: float | None
    latency_p99_s: float | None
    ttft_p50_s: float | None
    ttft_p95_s: float | None
    tpot_mean_s: float | None
    requests_per_s: float
    output_tokens_per_s: float
    shadow_cost_usd: float
    slo: dict[str, dict] = field(default_factory=dict)


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * pct / 100.0
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


async def _one(client: httpx.AsyncClient, prompt: str, headers: dict, max_tokens: int) -> Sample:
    body = {"messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
    t0 = time.perf_counter()
    first: float | None = None
    try:
        async with client.stream("POST", "/v1/chat/stream", json=body, headers=headers) as r:
            if r.status_code != 200:
                await r.aread()
                return Sample(False, r.status_code, time.perf_counter() - t0, error=f"HTTP {r.status_code}")
            done: dict | None = None
            async for line in r.aiter_lines():
                if not line.strip():
                    continue
                ev = json.loads(line)
                if ev["type"] == "token" and first is None:
                    first = time.perf_counter() - t0
                elif ev["type"] == "done":
                    done = ev
                elif ev["type"] == "error":
                    return Sample(False, 502, time.perf_counter() - t0, first, error=ev.get("code"))
            total = time.perf_counter() - t0
            if done is None:
                return Sample(False, 200, total, first, error="stream sin evento final")
            return Sample(
                True, 200, total, first,
                completion_tokens=done["usage"]["completion_tokens"],
                prompt_tokens=done["usage"]["prompt_tokens"],
                shadow_usd=done["cost"]["shadow_api_usd"],
            )
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        return Sample(False, 0, time.perf_counter() - t0, error=type(exc).__name__)


async def run_load(
    client: httpx.AsyncClient,
    users: int,
    requests: int,
    prompts: list[str] | None = None,
    api_key: str | None = None,
    max_tokens: int = 128,
    slo_p95_s: float | None = None,
    slo_ttft_s: float | None = None,
    slo_availability: float | None = None,
) -> tuple[Report, list[Sample]]:
    if users < 1 or requests < 1:
        raise ValueError("users y requests deben ser >= 1")
    prompts = prompts or DEFAULT_PROMPTS
    headers = {"X-API-Key": api_key} if api_key else {}
    queue: asyncio.Queue[int] = asyncio.Queue()
    for i in range(requests):
        queue.put_nowait(i)
    samples: list[Sample] = []

    async def worker() -> None:
        while True:
            try:
                i = queue.get_nowait()
            except asyncio.QueueEmpty:
                return
            samples.append(await _one(client, prompts[i % len(prompts)], headers, max_tokens))

    t0 = time.perf_counter()
    await asyncio.gather(*(worker() for _ in range(min(users, requests))))
    wall = time.perf_counter() - t0
    return build_report(samples, users, wall, slo_p95_s, slo_ttft_s, slo_availability), samples


def build_report(
    samples: list[Sample],
    users: int,
    wall_s: float,
    slo_p95_s: float | None = None,
    slo_ttft_s: float | None = None,
    slo_availability: float | None = None,
) -> Report:
    oks = [s for s in samples if s.ok]
    lat = [s.total_s for s in oks]
    ttft = [s.ttft_s for s in oks if s.ttft_s is not None]
    tpots = [
        (s.total_s - s.ttft_s) / (s.completion_tokens - 1)
        for s in oks
        if s.ttft_s is not None and s.completion_tokens > 1
    ]
    status: dict[str, int] = {}
    for s in samples:
        status[str(s.status)] = status.get(str(s.status), 0) + 1
    n = len(samples)
    errors = n - len(oks)
    rep = Report(
        users=users,
        requests=n,
        wall_s=round(wall_s, 3),
        success=len(oks),
        errors=errors,
        error_rate=errors / n if n else 0.0,
        status_counts=status,
        latency_p50_s=percentile(lat, 50),
        latency_p95_s=percentile(lat, 95),
        latency_p99_s=percentile(lat, 99),
        ttft_p50_s=percentile(ttft, 50),
        ttft_p95_s=percentile(ttft, 95),
        tpot_mean_s=(sum(tpots) / len(tpots)) if tpots else None,
        requests_per_s=n / wall_s if wall_s > 0 else 0.0,
        output_tokens_per_s=sum(s.completion_tokens for s in oks) / wall_s if wall_s > 0 else 0.0,
        shadow_cost_usd=sum(s.shadow_usd for s in oks),
    )
    if slo_p95_s is not None:
        rep.slo["latency_p95"] = {
            "target_s": slo_p95_s,
            "observed_s": rep.latency_p95_s,
            "pass": rep.latency_p95_s is not None and rep.latency_p95_s <= slo_p95_s,
        }
    if slo_ttft_s is not None:
        rep.slo["ttft_p95"] = {
            "target_s": slo_ttft_s,
            "observed_s": rep.ttft_p95_s,
            "pass": rep.ttft_p95_s is not None and rep.ttft_p95_s <= slo_ttft_s,
        }
    if slo_availability is not None:
        allowed = 1.0 - slo_availability  # error budget
        rep.slo["availability"] = {
            "target": slo_availability,
            "observed": 1.0 - rep.error_rate,
            "error_budget_consumed_pct": (rep.error_rate / allowed * 100.0) if allowed > 0 else None,
            "pass": (1.0 - rep.error_rate) >= slo_availability,
        }
    return rep


def format_report(rep: Report) -> str:
    def f(x: float | None, unit: str = "s") -> str:
        return "n/d" if x is None else f"{x:.3f}{unit}"

    lines = [
        f"Usuarios concurrentes : {rep.users}   Solicitudes: {rep.requests}   Duración: {rep.wall_s}s",
        f"Éxito / Error         : {rep.success} / {rep.errors}  (tasa de error {rep.error_rate:.2%})  códigos={rep.status_counts}",
        f"Latencia p50/p95/p99  : {f(rep.latency_p50_s)} / {f(rep.latency_p95_s)} / {f(rep.latency_p99_s)}",
        f"TTFT p50/p95          : {f(rep.ttft_p50_s)} / {f(rep.ttft_p95_s)}",
        f"TPOT medio            : {f(rep.tpot_mean_s)}",
        f"Throughput            : {rep.requests_per_s:.2f} req/s | {rep.output_tokens_per_s:.1f} tokens/s de salida",
        f"Costo sombra total    : ${rep.shadow_cost_usd:.6f}",
    ]
    for name, d in rep.slo.items():
        lines.append(f"SLO {name:<12}: {'CUMPLE' if d['pass'] else 'NO CUMPLE'}  {d}")
    return "\n".join(lines)


async def _amain(a: argparse.Namespace) -> int:
    async with httpx.AsyncClient(base_url=a.url, timeout=a.timeout) as client:
        rep, _ = await run_load(
            client, a.users, a.requests, api_key=a.api_key, max_tokens=a.max_tokens,
            slo_p95_s=a.slo_p95_s, slo_ttft_s=a.slo_ttft_s, slo_availability=a.slo_availability,
        )
    print(format_report(rep))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(asdict(rep), fh, indent=2, ensure_ascii=False)
        print(f"\nReporte JSON: {a.out}")
    return 0 if all(d["pass"] for d in rep.slo.values()) else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", default="http://localhost:8000")
    p.add_argument("--api-key")
    p.add_argument("--users", type=int, default=4)
    p.add_argument("--requests", type=int, default=20)
    p.add_argument("--max-tokens", type=int, default=128)
    p.add_argument("--timeout", type=float, default=180.0)
    p.add_argument("--slo-p95-s", type=float)
    p.add_argument("--slo-ttft-s", type=float)
    p.add_argument("--slo-availability", type=float)
    p.add_argument("--out", help="Ruta del reporte JSON.")
    return asyncio.run(_amain(p.parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())
