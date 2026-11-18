import os

os.environ.update(
    AZURE_OPENAI_ENDPOINT="https://demo.openai.azure.com/",
    FOUNDRY_MODEL_DEPLOYMENT="demo",
    AZURE_OPENAI_BASE_MODEL="gpt-4o-mini",
)


def test_agent_builds_offline():
    from agent_autogen import build_agent

    assert build_agent().name == "finops_advisor"
