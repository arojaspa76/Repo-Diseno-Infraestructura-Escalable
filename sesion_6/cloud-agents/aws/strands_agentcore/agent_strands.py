"""Agente FinOps con Strands Agents SDK sobre Amazon Bedrock (ejecución local).

Credenciales: cadena estándar de AWS (perfil SSO / variables). Sin claves en código.
El MISMO `agent` se despliega en AgentCore Runtime con `agentcore_app.py`.
"""

import os
import sys

from dotenv import load_dotenv
from strands import Agent, tool
from strands.models import BedrockModel

from finops_tools import INSTRUCTIONS, TOOLS

# `tool(fn)` convierte una función Python tipada y documentada en herramienta Strands.
STRANDS_TOOLS = [tool(fn) for fn in TOOLS]


def build_agent() -> Agent:
    model_id = os.environ.get("BEDROCK_MODEL_ID")
    if not model_id:
        sys.exit(
            "Defina BEDROCK_MODEL_ID (ID o perfil de inferencia habilitado en su cuenta/región; "
            "cópielo de la consola de Bedrock > Model catalog). Ver .env.example."
        )
    model = BedrockModel(model_id=model_id, region_name=os.environ.get("AWS_REGION", "us-east-1"))
    return Agent(model=model, system_prompt=INSTRUCTIONS, tools=STRANDS_TOOLS)


def main() -> None:
    load_dotenv()
    agent = build_agent()
    question = " ".join(sys.argv[1:]) or "Compara on-demand, compromiso y spot para 2 instancias de 1.00 USD/h con 30% y 65% de descuento."
    result = agent(question)
    print(result)


if __name__ == "__main__":
    main()
