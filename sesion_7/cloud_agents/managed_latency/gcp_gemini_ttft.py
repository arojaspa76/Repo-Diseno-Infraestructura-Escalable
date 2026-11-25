"""Mide TTFT y tokens/s de Gemini en Vertex AI con streaming (SDK google-genai).

    gcloud auth application-default login
    export GOOGLE_CLOUD_PROJECT=<proyecto> GOOGLE_CLOUD_LOCATION=us-central1 GEMINI_MODEL=gemini-flash-latest
    python gcp_gemini_ttft.py --runs 5
"""

from __future__ import annotations

import argparse
import os
import statistics
import time

from google import genai

PROMPT = "Explica en 120 palabras qué es el KV cache en un LLM."


def run_once(client: genai.Client, model: str) -> dict:
    t0 = time.perf_counter()
    first = None
    tokens = 0
    for chunk in client.models.generate_content_stream(model=model, contents=PROMPT):
        if chunk.text and first is None:
            first = time.perf_counter()
        if chunk.usage_metadata and chunk.usage_metadata.candidates_token_count:
            tokens = chunk.usage_metadata.candidates_token_count
    end = time.perf_counter()
    return {"ttft_ms": ((first or end) - t0) * 1000, "total_ms": (end - t0) * 1000, "tok_s": tokens / max(end - (first or t0), 1e-6)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    a = ap.parse_args()
    client = genai.Client(vertexai=True, project=os.environ["GOOGLE_CLOUD_PROJECT"], location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"))
    model = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
    rows = [run_once(client, model) for _ in range(a.runs)]
    for k in ("ttft_ms", "total_ms", "tok_s"):
        v = [r[k] for r in rows]
        print(f"{k:>9}: mediana {statistics.median(v):8.1f} | min {min(v):8.1f} | max {max(v):8.1f}")
