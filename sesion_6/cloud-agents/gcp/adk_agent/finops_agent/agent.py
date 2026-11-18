"""Agente FinOps con Google Agent Development Kit (ADK).

ADK descubre `root_agent` en este paquete. Se ejecuta con `adk web` (UI de
desarrollo), `adk run` (terminal) o `python run_local.py` (programático).
Autenticación a Vertex AI: Application Default Credentials (sin API keys).
"""

import os

from google.adk.agents import Agent

from .finops_tools import INSTRUCTIONS, TOOLS

# El nombre del modelo cambia con frecuencia: se lee de GEMINI_MODEL.
# `gemini-flash-latest` es el valor que genera `adk create` por defecto;
# para producción fije un modelo estable concreto (los alias no se pueden anclar).
MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")

root_agent = Agent(
    name="finops_advisor",
    model=MODEL,
    description="Asesor FinOps que estima costos de inferencia y compara opciones de compra de cómputo.",
    instruction=INSTRUCTIONS,
    tools=TOOLS,  # ADK convierte funciones Python (firma + docstring) en herramientas
)
