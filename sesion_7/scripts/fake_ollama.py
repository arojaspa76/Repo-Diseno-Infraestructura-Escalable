"""Servidor Ollama SIMULADO (solo para pruebas del repositorio y para quien no tiene hardware).

*** NO es un modelo real. Los números que produce son sintéticos: sirven para verificar que
los scripts funcionan, NO para sacar conclusiones de rendimiento. ***

Simula: prefill proporcional al tamaño del prompt, decode con ralentización al aumentar la
concurrencia (batching sub-lineal), carga en frío del modelo y embeddings en lote.

Uso:  python scripts/fake_ollama.py --port 11435
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import time

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

app = FastAPI(title="fake-ollama")
STATE = {"loaded": set(), "active": 0, "decode_ms": 8.0, "prefill_ms_per_100_chars": 6.0, "cold_ms": 900.0}
WORDS = "Un modelo de lenguaje genera texto token a token reutilizando el KV cache de los tokens previos".split()
_last_prefix: dict[str, str] = {}


@app.get("/api/version")
async def version():
    return {"version": "fake-0.0"}


@app.get("/api/tags")
async def tags():
    return {"models": [{"name": m, "size": 1_300_000_000} for m in sorted(STATE["loaded"]) or ["llama3.2:1b"]]}


@app.get("/api/ps")
async def ps():
    return {"models": [{"name": m, "size": 1_500_000_000, "size_vram": 0} for m in sorted(STATE["loaded"])]}


@app.post("/api/generate")
async def generate(request: Request):
    body = await request.json()
    if body.get("keep_alive") in (0, "0"):
        STATE["loaded"].discard(body.get("model"))
    else:
        STATE["loaded"].add(body.get("model"))
    return {"done": True}


@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    model = body["model"]
    msgs = body["messages"]
    prompt = "".join(m["content"] for m in msgs)
    n_predict = int(body.get("options", {}).get("num_predict", 64))
    cold = model not in STATE["loaded"]
    # Simula reutilización de prefijo: si el prompt comparte el comienzo con el anterior, el prefill cuesta menos.
    prev = _last_prefix.get(model, "")
    common = 0
    for a, b in zip(prompt, prev):
        if a != b:
            break
        common += 1
    _last_prefix[model] = prompt
    effective_chars = max(1, len(prompt) - int(common * 0.9))

    async def gen():
        t_load = 0.0
        if cold:
            await asyncio.sleep(STATE["cold_ms"] / 1000)
            t_load = STATE["cold_ms"]
            STATE["loaded"].add(model)
        prefill = STATE["prefill_ms_per_100_chars"] * effective_chars / 100
        await asyncio.sleep(prefill / 1000)
        STATE["active"] += 1
        try:
            t0 = time.perf_counter()
            for i in range(n_predict):
                per_tok = STATE["decode_ms"] * (1 + 0.18 * (STATE["active"] - 1))
                await asyncio.sleep(per_tok / 1000)
                yield json.dumps({"message": {"role": "assistant", "content": WORDS[i % len(WORDS)] + " "}, "done": False}) + "\n"
            dec = time.perf_counter() - t0
        finally:
            STATE["active"] -= 1
        yield json.dumps({
            "done": True, "message": {"role": "assistant", "content": ""},
            "load_duration": int(t_load * 1e6), "prompt_eval_count": max(1, len(prompt) // 4),
            "prompt_eval_duration": int(prefill * 1e6), "eval_count": n_predict, "eval_duration": int(dec * 1e9),
        }) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")


@app.post("/api/embed")
async def embed(request: Request):
    body = await request.json()
    inputs = body["input"] if isinstance(body["input"], list) else [body["input"]]
    await asyncio.sleep((20 + 3 * len(inputs)) / 1000)  # coste fijo + coste por elemento => el lote compensa
    vecs = []
    for t in inputs:
        h = hashlib.sha256(t.encode()).digest()
        vecs.append([b / 255 for b in h[:8]])
    return JSONResponse({"model": body.get("model"), "embeddings": vecs})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=11435)
    uvicorn.run(app, host="127.0.0.1", port=ap.parse_args().port, log_level="warning")
