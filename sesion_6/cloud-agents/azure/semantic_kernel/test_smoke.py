import os

os.environ["AZURE_OPENAI_ENDPOINT"] = "https://demo.openai.azure.com/"
os.environ["FOUNDRY_MODEL_DEPLOYMENT"] = "demo"


def test_agent_builds_offline():
    from agent_sk import FinOpsPlugin, build_agent

    agent = build_agent()
    assert agent.name == "FinOpsAdvisor"
    r = FinOpsPlugin().compare_compute_purchase_options(1.0, 2, 0.3, 0.65)
    assert r["on_demand_monthly_usd"] == 1460.0
