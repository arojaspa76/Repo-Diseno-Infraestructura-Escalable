"""Agente FinOps con Semantic Kernel (SK). ESTADO: modo mantenimiento (ver README).

Se incluye porque hay muchísimo código SK en producción y el estudiante debe saber
leerlo y migrarlo a Microsoft Agent Framework. Para proyectos nuevos use MAF.

Auth: Entra ID (DefaultAzureCredential). El endpoint es el de Azure OpenAI del
mismo recurso Foundry: https://<recurso>.openai.azure.com/
"""

import asyncio
import os
import sys
from typing import Annotated

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function

import finops_tools as ft
from finops_tools import INSTRUCTIONS


class FinOpsPlugin:
    """En SK las herramientas son *plugins*: clases con métodos @kernel_function."""

    @kernel_function(name="estimate_monthly_inference_cost", description="Estima el costo mensual de una API de LLM administrada (pago por token).")
    def estimate_monthly_inference_cost(
        self,
        requests_per_month: Annotated[int, "Solicitudes por mes"],
        avg_input_tokens: Annotated[int, "Tokens de entrada promedio por solicitud"],
        avg_output_tokens: Annotated[int, "Tokens de salida promedio por solicitud"],
        price_input_per_mtok_usd: Annotated[float, "USD por millón de tokens de entrada"],
        price_output_per_mtok_usd: Annotated[float, "USD por millón de tokens de salida"],
    ) -> dict:
        return ft.estimate_monthly_inference_cost(
            requests_per_month, avg_input_tokens, avg_output_tokens,
            price_input_per_mtok_usd, price_output_per_mtok_usd,
        )

    @kernel_function(name="compare_compute_purchase_options", description="Compara costo mensual on-demand vs compromiso vs spot de una flota always-on.")
    def compare_compute_purchase_options(
        self,
        on_demand_hourly_usd: Annotated[float, "Precio por hora on-demand de una instancia"],
        instances: Annotated[int, "Número de instancias siempre activas"],
        commitment_discount: Annotated[float, "Fracción de descuento por compromiso (0.30 = 30%)"],
        spot_discount: Annotated[float, "Fracción de descuento spot (0.65 = 65%)"],
        spot_overhead: Annotated[float, "Sobrecosto por interrupciones (0.10 = 10%)"] = 0.10,
    ) -> dict:
        return ft.compare_compute_purchase_options(
            on_demand_hourly_usd, instances, commitment_discount, spot_discount, spot_overhead
        )


def build_agent() -> ChatCompletionAgent:
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    deployment = os.environ.get("FOUNDRY_MODEL_DEPLOYMENT")
    if not endpoint or not deployment:
        sys.exit("Defina AZURE_OPENAI_ENDPOINT y FOUNDRY_MODEL_DEPLOYMENT (ver .env.example).")
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    service = AzureChatCompletion(
        deployment_name=deployment, endpoint=endpoint, ad_token_provider=token_provider
    )
    return ChatCompletionAgent(
        service=service, name="FinOpsAdvisor", instructions=INSTRUCTIONS, plugins=[FinOpsPlugin()]
    )


async def main() -> None:
    load_dotenv()
    agent = build_agent()
    question = " ".join(sys.argv[1:]) or "Estima el costo de 200000 solicitudes/mes, 800 tokens de entrada, 300 de salida, a 1 y 4 USD por Mtok."
    response = await agent.get_response(messages=question)
    print(response.message.content)


if __name__ == "__main__":
    asyncio.run(main())
