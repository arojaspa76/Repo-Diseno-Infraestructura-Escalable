"""Limpieza: elimina el agente creado por create_prompt_agent.py."""

import os
import sys

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

AGENT_NAME = "finops-advisor-s06"

if __name__ == "__main__":
    load_dotenv()
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT") or sys.exit("Falta FOUNDRY_PROJECT_ENDPOINT")
    with AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential()) as project:
        project.agents.delete(agent_name=AGENT_NAME)
        print(f"Agente '{AGENT_NAME}' eliminado.")
