"""Ejemplo 1.AWS-código — Invocar con boto3 el agente que usted creó desde la CONSOLA de Bedrock (Agents).

Mide también el tiempo hasta el primer fragmento de respuesta (aprox. TTFT del agente completo).

Uso:
    export AWS_REGION=us-east-1 BEDROCK_AGENT_ID=XXXXXXXXXX BEDROCK_AGENT_ALIAS_ID=YYYYYYYYYY
    python invoke_agent.py "¿Qué es el KV cache?"
"""

from __future__ import annotations

import os
import sys
import time
import uuid

import boto3


def main(prompt: str) -> None:
    client = boto3.client("bedrock-agent-runtime", region_name=os.environ.get("AWS_REGION", "us-east-1"))
    t0 = time.perf_counter()
    resp = client.invoke_agent(
        agentId=os.environ["BEDROCK_AGENT_ID"],
        agentAliasId=os.environ["BEDROCK_AGENT_ALIAS_ID"],
        sessionId=str(uuid.uuid4()),
        inputText=prompt,
    )
    first: float | None = None
    parts: list[str] = []
    for event in resp["completion"]:  # flujo de eventos
        chunk = event.get("chunk")
        if chunk:
            first = first or time.perf_counter()
            parts.append(chunk["bytes"].decode("utf-8"))
    total = time.perf_counter() - t0
    print("".join(parts))
    print(f"\n[primer fragmento: {((first or t0) - t0) * 1000:.0f} ms | total: {total * 1000:.0f} ms]")


if __name__ == "__main__":
    main(" ".join(sys.argv[1:]) or "¿Qué es el KV cache?")
