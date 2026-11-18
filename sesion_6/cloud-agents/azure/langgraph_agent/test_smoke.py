import os

os.environ["FOUNDRY_PROJECT_ENDPOINT"] = "https://demo.services.ai.azure.com/api/projects/demo"
os.environ["FOUNDRY_MODEL_DEPLOYMENT"] = "demo"


def test_graph_compiles_offline():
    from agent_langgraph import build_graph

    g = build_graph()
    nodes = set(g.get_graph().nodes)
    assert {"agent", "tools"} <= nodes
