"""Mide TTFT y tokens/s de un despliegue de Azure OpenAI (Foundry) con streaming y autenticación Entra ID.

    az login
    export AZURE_OPENAI_ENDPOINT=https://<recurso>.openai.azure.com/ AZURE_OPENAI_DEPLOYMENT=<despliegue>
    python azure_openai_ttft.py --runs 5
"""

from __future__ import annotations

import argparse
import os
import statistics
import time

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

PROMPT = "Explica en 120 palabras qué es el KV cache en un LLM."


def run_once(client: AzureOpenAI, deployment: str) -> dict:
    t0 = time.perf_counter()
    first = None
    tokens = 0
    stream = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": PROMPT}],
        max_tokens=256,
        temperature=0,
        stream=True,
        stream_options={"include_usage": True},
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content and first is None:
            first = time.perf_counter()
        if chunk.usage:
            tokens = chunk.usage.completion_tokens
    end = time.perf_counter()
    return {"ttft_ms": ((first or end) - t0) * 1000, "total_ms": (end - t0) * 1000, "tok_s": tokens / max(end - (first or t0), 1e-6)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    a = ap.parse_args()
    provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
    client = AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        azure_ad_token_provider=provider,
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )
    rows = [run_once(client, os.environ["AZURE_OPENAI_DEPLOYMENT"]) for _ in range(a.runs)]
    for k in ("ttft_ms", "total_ms", "tok_s"):
        v = [r[k] for r in rows]
        print(f"{k:>9}: mediana {statistics.median(v):8.1f} | min {min(v):8.1f} | max {max(v):8.1f}")
