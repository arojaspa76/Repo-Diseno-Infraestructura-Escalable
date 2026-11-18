"""Ejecuta el agente ADK programáticamente (sin la UI web).

  cd cloud-agents/gcp/adk_agent
  gcloud auth application-default login
  cp finops_agent/.env.example finops_agent/.env   # y edite proyecto/región
  python run_local.py "Estima el costo mensual de 200000 solicitudes con 800 tokens de entrada, 300 de salida, a 1 y 4 USD por millón."
"""

import asyncio
import sys

from dotenv import load_dotenv

load_dotenv("finops_agent/.env")

from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

from finops_agent.agent import root_agent  # noqa: E402

APP, USER = "finops_s06", "estudiante"


async def ask(prompt: str) -> str:
    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    session = await runner.session_service.create_session(app_name=APP, user_id=USER)
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    answer = ""
    async for event in runner.run_async(user_id=USER, session_id=session.id, new_message=message):
        if event.is_final_response() and event.content and event.content.parts:
            answer = "".join(p.text or "" for p in event.content.parts)
    return answer


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Compara on-demand, compromiso y spot para 2 instancias de 1.00 USD/hora, con 30% y 65% de descuento."
    print(asyncio.run(ask(question)))
