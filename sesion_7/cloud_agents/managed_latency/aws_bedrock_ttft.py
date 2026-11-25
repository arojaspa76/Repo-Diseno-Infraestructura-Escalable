"""Mide TTFT y tokens/s de un modelo en Amazon Bedrock con la API Converse (streaming).

    export AWS_REGION=us-east-1 BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
    python aws_bedrock_ttft.py --runs 5
"""

from __future__ import annotations

import argparse
import os
import statistics
import time

import boto3

PROMPT = "Explica en 120 palabras qué es el KV cache en un LLM."


def run_once(client, model_id: str) -> dict:
    t0 = time.perf_counter()
    first = None
    out_tokens = 0
    resp = client.converse_stream(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": PROMPT}]}],
        inferenceConfig={"maxTokens": 256, "temperature": 0.0},
    )
    for ev in resp["stream"]:
        if "contentBlockDelta" in ev and first is None:
            first = time.perf_counter()
        if "metadata" in ev:
            out_tokens = ev["metadata"].get("usage", {}).get("outputTokens", 0)
    end = time.perf_counter()
    ttft = ((first or end) - t0) * 1000
    return {"ttft_ms": ttft, "total_ms": (end - t0) * 1000, "tok_s": out_tokens / max(end - (first or t0), 1e-6)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=5)
    a = ap.parse_args()
    client = boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    model = os.environ["BEDROCK_MODEL_ID"]
    rows = [run_once(client, model) for _ in range(a.runs)]
    for k in ("ttft_ms", "total_ms", "tok_s"):
        v = [r[k] for r in rows]
        print(f"{k:>9}: mediana {statistics.median(v):8.1f} | min {min(v):8.1f} | max {max(v):8.1f}")
