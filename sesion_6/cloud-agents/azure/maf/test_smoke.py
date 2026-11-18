import os

os.environ["FOUNDRY_PROJECT_ENDPOINT"] = "https://demo.services.ai.azure.com/api/projects/demo"
os.environ["FOUNDRY_MODEL_DEPLOYMENT"] = "demo-deployment"


def test_agent_builds_offline():
    from agent_maf import build_agent

    agent = build_agent()
    assert agent.name == "finops-advisor"
