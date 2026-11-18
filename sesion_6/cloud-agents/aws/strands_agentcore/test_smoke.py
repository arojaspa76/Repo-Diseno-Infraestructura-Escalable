import os

os.environ["BEDROCK_MODEL_ID"] = "demo-model-id"
os.environ["AWS_REGION"] = "us-east-1"


def test_agent_builds_offline():
    from agent_strands import build_agent

    agent = build_agent()
    assert len(agent.tool_names) == 2


def test_agentcore_app_defines_entrypoint():
    import agentcore_app

    out = agentcore_app.invoke({"prompt": ""})
    assert "error" in out
    assert "error" in agentcore_app.invoke({"prompt": "x" * 5000})
