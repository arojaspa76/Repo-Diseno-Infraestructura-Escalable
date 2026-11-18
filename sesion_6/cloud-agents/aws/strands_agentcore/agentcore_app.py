"""El mismo agente Strands empaquetado para Amazon Bedrock AgentCore Runtime.

`BedrockAgentCoreApp` levanta un servidor HTTP con los endpoints que exige
AgentCore (/invocations y /ping, puerto 8080). Local:

    python agentcore_app.py
    curl -X POST http://localhost:8080/invocations -H "Content-Type: application/json" \
         -d '{"prompt": "Compara on-demand, compromiso y spot para 2 instancias de 1 USD/h"}'
"""

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from dotenv import load_dotenv

from agent_strands import build_agent

load_dotenv()
app = BedrockAgentCoreApp()
_agent = None  # se crea en la primera invocación (arranque rápido y errores claros)


@app.entrypoint
def invoke(payload: dict) -> dict:
    global _agent
    if _agent is None:
        _agent = build_agent()
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        return {"error": "Falta el campo 'prompt'."}
    if len(prompt) > 4000:  # control de consumo (OWASP LLM06) también en el borde del agente
        return {"error": "Prompt demasiado largo."}
    result = _agent(prompt)
    return {"result": str(result)}


if __name__ == "__main__":
    app.run()
