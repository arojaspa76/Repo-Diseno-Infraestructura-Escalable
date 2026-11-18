"""Cálculo de costos de una inferencia.

Dos modelos de costo, porque en la nube conviven ambos:

* Costo por token (APIs administradas: Vertex AI/Gemini, Foundry, Bedrock):
  costo = tokens_entrada * precio_in / 1e6 + tokens_salida * precio_out / 1e6
* Costo por tiempo de cómputo (autogestionado: VM/GPU, Kubernetes, Ollama):
  costo = horas_de_cómputo * precio_por_hora
"""

from __future__ import annotations


def shadow_api_cost(
    prompt_tokens: int,
    completion_tokens: int,
    price_in_per_mtok: float,
    price_out_per_mtok: float,
) -> float:
    if min(prompt_tokens, completion_tokens) < 0:
        raise ValueError("El número de tokens no puede ser negativo.")
    return (
        prompt_tokens * price_in_per_mtok + completion_tokens * price_out_per_mtok
    ) / 1_000_000


def selfhosted_cost(compute_seconds: float, infra_usd_per_hour: float) -> float:
    if compute_seconds < 0 or infra_usd_per_hour < 0:
        raise ValueError("Tiempo y precio no pueden ser negativos.")
    return compute_seconds / 3600.0 * infra_usd_per_hour
