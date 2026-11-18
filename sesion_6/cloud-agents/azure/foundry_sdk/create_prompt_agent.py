"""Crea un agente (prompt agent) en Microsoft Foundry con el SDK `azure-ai-projects` 2.x
y conversa con él mediante la Responses API.

Prerrequisitos:  az login  +  un proyecto Foundry con un modelo desplegado.
Permisos mínimos: rol "Azure AI User" sobre el proyecto (ver README).

  python create_prompt_agent.py "¿Cuándo conviene un compromiso de 1 año frente a on-demand?"
"""

import os
import sys

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

INSTRUCTIONS = (
    "Eres un asesor FinOps para el equipo de plataforma de una universidad que opera un "
    "asistente institucional basado en LLM. Responde en español, breve y con criterios claros. "
    "No inventes precios: si faltan datos, pídelos."
)
AGENT_NAME = "finops-advisor-s06"


def require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"Falta la variable de entorno {name} (ver .env.example).")
    return value


def main() -> None:
    load_dotenv()
    endpoint = require("FOUNDRY_PROJECT_ENDPOINT")
    model = require("FOUNDRY_MODEL_DEPLOYMENT")
    prompt = " ".join(sys.argv[1:]) or "Explica en tres puntos qué es rightsizing."

    with AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential()) as project:
        agent = project.agents.create_version(
            agent_name=AGENT_NAME,
            definition=PromptAgentDefinition(model=model, instructions=INSTRUCTIONS),
        )
        print(f"Agente creado: {agent.name} (versión {agent.version})")

        openai = project.get_openai_client()
        conversation = openai.conversations.create()
        response = openai.responses.create(
            conversation=conversation.id,
            input=prompt,
            extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        )
        print("\n--- Respuesta ---")
        print(response.output_text)
        print(f"\nTokens: {response.usage.input_tokens} entrada / {response.usage.output_tokens} salida")


if __name__ == "__main__":
    main()
