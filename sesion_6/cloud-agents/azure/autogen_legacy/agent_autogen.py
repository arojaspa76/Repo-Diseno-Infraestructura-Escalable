"""Agente FinOps con AutoGen 0.7 (AgentChat). ESTADO: LEGADO (ver README).

AutoGen fue sucedido por Microsoft Agent Framework; su repositorio está en
mantenimiento/archivado. Este ejemplo existe para que el estudiante pueda LEER
código AutoGen y migrarlo (tabla de equivalencias en el README). No lo use en
proyectos nuevos.
"""

import asyncio
import os
import sys

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

from finops_tools import INSTRUCTIONS, TOOLS


def build_agent() -> AssistantAgent:
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    deployment = os.environ.get("FOUNDRY_MODEL_DEPLOYMENT")
    base_model = os.environ.get("AZURE_OPENAI_BASE_MODEL")  # p. ej. el modelo base del deployment
    if not endpoint or not deployment or not base_model:
        sys.exit("Defina AZURE_OPENAI_ENDPOINT, FOUNDRY_MODEL_DEPLOYMENT y AZURE_OPENAI_BASE_MODEL.")
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    client = AzureOpenAIChatCompletionClient(
        azure_deployment=deployment,
        model=base_model,
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,
    )
    return AssistantAgent(
        name="finops_advisor",
        model_client=client,
        tools=TOOLS,
        system_message=INSTRUCTIONS,
        reflect_on_tool_use=True,  # el modelo redacta la respuesta final con el resultado de la herramienta
    )


async def main() -> None:
    load_dotenv()
    agent = build_agent()
    question = " ".join(sys.argv[1:]) or "Compara on-demand, compromiso y spot para 2 instancias de 1.00 USD/h con 30% y 65% de descuento."
    result = await agent.run(task=question)
    print(result.messages[-1].content)


if __name__ == "__main__":
    asyncio.run(main())
