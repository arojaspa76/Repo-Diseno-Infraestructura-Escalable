"""Prueba offline: el agente se construye y expone las herramientas (sin llamar a Google)."""

import os

os.environ.setdefault("GEMINI_MODEL", "gemini-flash-latest")


def test_agent_builds_with_tools():
    from finops_agent.agent import root_agent

    assert root_agent.name == "finops_advisor"
    assert len(root_agent.tools) == 2
    assert "FinOps" in root_agent.instruction


def test_runner_can_be_created():
    from google.adk.runners import InMemoryRunner

    from finops_agent.agent import root_agent

    assert InMemoryRunner(agent=root_agent, app_name="t") is not None
