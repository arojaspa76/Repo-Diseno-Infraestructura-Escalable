"""Ejecuta el agente ADK desde Python (sin la UI), útil para pruebas y para integrarlo en FastAPI.

Uso (desde cloud_agents/gcp/adk_agent):
    python run_programmatic.py "¿Cabe Llama 3.1 8B en FP16 en una GPU de 24 GB con 8 conversaciones de 8192 tokens?"
"""

from __future__ import annotations

import asyncio
import sys

from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types

load_dotenv("capacity_advisor/.env")
from capacity_advisor.agent import root_agent  # noqa: E402

DEFAULT_Q = "¿Cabe Llama 3.1 8B en FP16 en una GPU de 24 GB con 8 conversaciones de 8192 tokens? Si no, ¿qué recomiendas?"


async def main(question: str) -> None:
    runner = InMemoryRunner(agent=root_agent, app_name="capacity_advisor_app")
    session = await runner.session_service.create_session(app_name="capacity_advisor_app", user_id="alumno")
    message = types.Content(role="user", parts=[types.Part(text=question)])
    async for event in runner.run_async(user_id="alumno", session_id=session.id, new_message=message):
        if event.is_final_response() and event.content and event.content.parts:
            print(event.content.parts[0].text)


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or DEFAULT_Q))
