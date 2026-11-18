"""Agente FinOps con Microsoft Agent Framework (MAF) 1.x sobre un modelo de Microsoft Foundry.

MAF es el sucesor unificado de Semantic Kernel y AutoGen (GA 1.0 en abril de 2026).
Autenticación: Microsoft Entra ID vía `az login` (sin API keys).

  python agent_maf.py "Estima el costo de 200000 solicitudes/mes con 800 tokens de entrada y 300 de salida a 1 y 4 USD por Mtok."
"""

import asyncio
import os
import sys

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

from finops_tools import INSTRUCTIONS, TOOLS


def build_agent() -> Agent:
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
    model = os.environ.get("FOUNDRY_MODEL_DEPLOYMENT")
    if not endpoint or not model:
        sys.exit("Defina FOUNDRY_PROJECT_ENDPOINT y FOUNDRY_MODEL_DEPLOYMENT (ver .env.example).")
    client = FoundryChatClient(
        project_endpoint=endpoint, model=model, credential=AzureCliCredential()
    )
    return Agent(client=client, name="finops-advisor", instructions=INSTRUCTIONS, tools=TOOLS)


async def main() -> None:
    load_dotenv()
    agent = build_agent()
    question = " ".join(sys.argv[1:]) or "Compara on-demand, compromiso y spot para 2 instancias de 1.00 USD/h con 30% y 65% de descuento."
    result = await agent.run(question)
    print(result.text)


if __name__ == "__main__":
    asyncio.run(main())
