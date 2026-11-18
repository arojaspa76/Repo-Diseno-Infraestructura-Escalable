"""Agente FinOps con LangGraph sobre un modelo de Microsoft Foundry.

El grafo es EXPLÍCITO (estado -> nodos -> aristas), a diferencia de los
"agentes prefabricados": es la mejor forma de entender qué hace un agente:
    START -> agent --(¿pidió herramienta?)--> tools -> agent -> ... -> END
"""

import os
import sys

from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from langchain_azure_ai.chat_models import AzureAIOpenAIApiChatModel
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from finops_tools import INSTRUCTIONS, TOOLS

# Las funciones de `finops_tools` se envuelven como herramientas de LangChain
# (usa la firma y el docstring para describir la herramienta al modelo).
LC_TOOLS = [tool(fn) for fn in TOOLS]


def build_graph():
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
    deployment = os.environ.get("FOUNDRY_MODEL_DEPLOYMENT")
    if not endpoint or not deployment:
        sys.exit("Defina FOUNDRY_PROJECT_ENDPOINT y FOUNDRY_MODEL_DEPLOYMENT (ver .env.example).")
    model = AzureAIOpenAIApiChatModel(
        project_endpoint=endpoint, credential=DefaultAzureCredential(), model=deployment
    )
    model_with_tools = model.bind_tools(LC_TOOLS)

    def call_model(state: MessagesState) -> dict:
        reply = model_with_tools.invoke([SystemMessage(content=INSTRUCTIONS), *state["messages"]])
        return {"messages": [reply]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(LC_TOOLS))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile()


def main() -> None:
    load_dotenv()
    app = build_graph()
    question = " ".join(sys.argv[1:]) or "Estima el costo de 200000 solicitudes/mes, 800 tokens de entrada, 300 de salida, a 1 y 4 USD por Mtok."
    result = app.invoke({"messages": [("user", question)]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
