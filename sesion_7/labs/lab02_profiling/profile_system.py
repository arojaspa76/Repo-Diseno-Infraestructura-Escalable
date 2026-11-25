#!/usr/bin/env python3
"""Lab 2 — Profiling de CPU, RAM, GPU y red durante una inferencia.

Qué hace:
  1. Mide la latencia de red hacia el servidor de inferencia (conexión TCP + petición HTTP mínima).
  2. (Opcional --cold) Descarga el modelo para forzar un arranque en frío y mide cuánto cuesta cargarlo.
  3. Ejecuta una inferencia mientras un hilo muestrea CPU, RAM, GPU (si hay NVIDIA) y tráfico de red.
  4. Pregunta a Ollama cuánto del modelo quedó en GPU (size_vram) frente a RAM del sistema.

Uso:
  python labs/lab02_profiling/profile_system.py --model llama3.2:1b --cold
"""

from __future__ import annotations

import argparse
import asyncio
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
import psutil

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _common import (DEFAULT_BASE_URL, filler_text, fmt, make_client, ollama_ps, percentile,  # noqa: E402
                     save_result, timed_chat, unload_model)


def gpu_sample() -> dict[str, float] | None:
    if not shutil.which("nvidia-smi"):
        return None
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3, check=True,
        ).stdout.strip().splitlines()[0]
        util, used, total = (float(x) for x in out.split(","))
        return {"gpu_util_pct": util, "gpu_mem_used_mb": used, "gpu_mem_total_mb": total}
    except (subprocess.SubprocessError, ValueError, IndexError):
        return None


class Sampler(threading.Thread):
    def __init__(self, interval: float) -> None:
        super().__init__(daemon=True)
        self.interval = interval
        self.stop_event = threading.Event()
        self.samples: list[dict[str, float]] = []

    def run(self) -> None:
        psutil.cpu_percent(None)  # inicializa el contador
        net0 = psutil.net_io_counters()
        while not self.stop_event.is_set():
            time.sleep(self.interval)
            s: dict[str, float] = {
                "cpu_pct": psutil.cpu_percent(None),
                "ram_used_mb": psutil.virtual_memory().used / 1e6,
            }
            net = psutil.net_io_counters()
            s["net_sent_mb"] = (net.bytes_sent - net0.bytes_sent) / 1e6
            s["net_recv_mb"] = (net.bytes_recv - net0.bytes_recv) / 1e6
            g = gpu_sample()
            if g:
                s.update(g)
            self.samples.append(s)

    def stop(self) -> None:
        self.stop_event.set()
        self.join(timeout=5)


def network_rtt(base_url: str, n: int = 10) -> dict[str, float | None]:
    u = urlparse(base_url)
    host, port = u.hostname or "localhost", u.port or (443 if u.scheme == "https" else 80)
    connects, https = [], []
    for _ in range(n):
        t = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=3):
                connects.append((time.perf_counter() - t) * 1000)
        except OSError:
            pass
        t = time.perf_counter()
        try:
            httpx.get(f"{base_url}/api/version", timeout=3)
            https.append((time.perf_counter() - t) * 1000)
        except httpx.HTTPError:
            pass
    return {
        "tcp_connect_p50_ms": percentile(connects, 50),
        "http_request_p50_ms": percentile(https, 50),
        "http_request_p95_ms": percentile(https, 95),
    }


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--model", default="llama3.2:1b")
    ap.add_argument("--prompt-tokens", type=int, default=400, help="Tamaño aproximado del prompt (afecta al prefill)")
    ap.add_argument("--num-predict", type=int, default=128)
    ap.add_argument("--interval", type=float, default=0.25)
    ap.add_argument("--cold", action="store_true", help="Fuerza arranque en frío descargando el modelo antes")
    args = ap.parse_args()

    print(f"== Lab 2: profiling contra {args.base_url} con {args.model} ==")
    rtt = network_rtt(args.base_url)
    print(f"Red · TCP connect p50: {fmt(rtt['tcp_connect_p50_ms'], 2)} ms · HTTP p50: {fmt(rtt['http_request_p50_ms'], 2)} ms")

    async with make_client(args.base_url) as client:
        if args.cold:
            await unload_model(client, args.model)
            await asyncio.sleep(1.0)
        prompt = "Resume el siguiente texto en una frase:\n" + filler_text(args.prompt_tokens)
        sampler = Sampler(args.interval)
        sampler.start()
        try:
            res = await timed_chat(client, args.model, prompt, num_predict=args.num_predict)
        finally:
            sampler.stop()
        ps = await ollama_ps(client)

    smp = sampler.samples
    def peak(key: str) -> float | None:
        vals = [s[key] for s in smp if key in s]
        return max(vals) if vals else None
    def avg(key: str) -> float | None:
        vals = [s[key] for s in smp if key in s]
        return sum(vals) / len(vals) if vals else None

    model_ps = next((m for m in ps if m.get("name", "").startswith(args.model.split(":")[0])), None)
    gpu_share = None
    if model_ps and model_ps.get("size"):
        gpu_share = 100 * model_ps.get("size_vram", 0) / model_ps["size"]

    print("\n--- Resultados ---")
    print(f"TTFT: {fmt(res['ttft_ms'])} ms | prefill (prompt_eval): {fmt(res['prompt_eval_ms'])} ms | carga del modelo: {fmt(res['load_ms'])} ms")
    print(f"TPOT: {fmt(res['tpot_ms'], 2)} ms/token | decode: {fmt(res['decode_tok_s'])} tok/s | total: {fmt(res['total_ms'])} ms")
    print(f"CPU media/pico: {fmt(avg('cpu_pct'))}% / {fmt(peak('cpu_pct'))}% | RAM pico: {fmt(peak('ram_used_mb'), 0)} MB")
    if peak("gpu_util_pct") is not None:
        print(f"GPU util pico: {fmt(peak('gpu_util_pct'))}% | VRAM pico: {fmt(peak('gpu_mem_used_mb'), 0)} / {fmt(peak('gpu_mem_total_mb'), 0)} MB")
    else:
        print("GPU: no se detectó nvidia-smi (ejecución solo en CPU o GPU no NVIDIA)")
    print(f"Red durante la inferencia: ↑{fmt(smp[-1]['net_sent_mb'] if smp else None, 3)} MB ↓{fmt(smp[-1]['net_recv_mb'] if smp else None, 3)} MB")
    if gpu_share is not None:
        print(f"Ollama /api/ps: {gpu_share:.0f}% del modelo está en GPU")

    res.pop("text", None)
    path = save_result("profiling", {
        "model": args.model, "cold": args.cold, "prompt_tokens_target": args.prompt_tokens,
        "network": rtt, "inference": res, "samples": smp, "gpu_share_pct": gpu_share,
    }, args.base_url)
    print(f"\nGuardado en {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
