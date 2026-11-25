"""Utilidades compartidas por los laboratorios (solo httpx + librería estándar).

Se mantiene a propósito simple y legible: así el estudiante ve exactamente cómo se
mide el TTFT y el TPOT, sin cajas negras.
"""

from __future__ import annotations

import json
import os
import platform
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

DEFAULT_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    import math

    return ordered[max(1, math.ceil(p / 100 * len(ordered))) - 1]


def ns_to_ms(v: Any) -> float | None:
    return float(v) / 1e6 if isinstance(v, (int, float)) and v > 0 else None


async def timed_chat(
    client: httpx.AsyncClient,
    model: str,
    prompt: str,
    *,
    system: str | None = None,
    num_predict: int = 128,
    num_ctx: int | None = None,
    temperature: float = 0.0,
    keep_alive: str | int | None = None,
) -> dict[str, Any]:
    """Una inferencia en streaming con medición de TTFT, TPOT y estadísticas de Ollama."""
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    options: dict[str, Any] = {"temperature": temperature, "num_predict": num_predict, "seed": 42}
    if num_ctx:
        options["num_ctx"] = num_ctx
    payload: dict[str, Any] = {"model": model, "messages": messages, "stream": True, "options": options}
    if keep_alive is not None:
        payload["keep_alive"] = keep_alive

    t0 = time.perf_counter()
    t_first = t_last = None
    n_chunks = 0
    text: list[str] = []
    final: dict[str, Any] = {}
    async with client.stream("POST", "/api/chat", json=payload) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line:
                continue
            data = json.loads(line)
            if "error" in data:
                raise RuntimeError(data["error"])
            piece = data.get("message", {}).get("content", "")
            if piece:
                now = time.perf_counter()
                t_first = t_first or now
                t_last = now
                n_chunks += 1
                text.append(piece)
            if data.get("done"):
                final = data
    t_end = time.perf_counter()
    completion = int(final.get("eval_count") or n_chunks)
    eval_ms = ns_to_ms(final.get("eval_duration"))
    tpot = ((t_last - t_first) * 1000 / (completion - 1)) if (t_first and t_last and completion > 1) else None
    return {
        "ttft_ms": (t_first - t0) * 1000 if t_first else None,
        "tpot_ms": tpot,
        "total_ms": (t_end - t0) * 1000,
        "prompt_tokens": int(final.get("prompt_eval_count") or 0),
        "completion_tokens": completion,
        "decode_tok_s": (completion / (eval_ms / 1000)) if eval_ms else None,
        "prompt_eval_ms": ns_to_ms(final.get("prompt_eval_duration")),
        "load_ms": ns_to_ms(final.get("load_duration")),
        "text": "".join(text),
    }


async def unload_model(client: httpx.AsyncClient, model: str) -> None:
    """Descarga el modelo de memoria (keep_alive=0) para forzar un arranque en frío."""
    await client.post("/api/generate", json={"model": model, "keep_alive": 0})


async def ollama_ps(client: httpx.AsyncClient) -> list[dict[str, Any]]:
    resp = await client.get("/api/ps")
    resp.raise_for_status()
    return list(resp.json().get("models", []))


def summarize(values: list[float | None]) -> dict[str, float | None]:
    vals = [v for v in values if v is not None]
    if not vals:
        return {"mean": None, "p50": None, "p95": None, "min": None, "max": None}
    return {
        "mean": statistics.fmean(vals),
        "p50": percentile(vals, 50),
        "p95": percentile(vals, 95),
        "min": min(vals),
        "max": max(vals),
    }


def environment_info(base_url: str) -> dict[str, Any]:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "cpu_count": os.cpu_count(),
        "base_url": base_url,
    }


def save_result(kind: str, payload: dict[str, Any], base_url: str) -> Path:
    """Guarda JSON en results/ con metadatos del entorno (reproducibilidad)."""
    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{kind}_{stamp}.json"
    doc = {"kind": kind, "environment": environment_info(base_url), **payload}
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def fmt(v: float | None, nd: int = 1) -> str:
    return "—" if v is None else f"{v:.{nd}f}"


def make_client(base_url: str, timeout: float = 300.0) -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=base_url, timeout=httpx.Timeout(timeout, connect=5.0))


def filler_text(approx_tokens: int) -> str:
    """Texto de relleno determinista (≈ 1 token por palabra corta) para controlar el tamaño del prompt."""
    base = (
        "La arquitectura de referencia separa el plano de control del plano de datos, "
        "aísla la inferencia en una red privada y mide cada petición con trazas y métricas. "
    )
    words = base.split()
    out: list[str] = []
    while len(out) < approx_tokens:
        out.extend(words)
    return " ".join(out[:approx_tokens])
