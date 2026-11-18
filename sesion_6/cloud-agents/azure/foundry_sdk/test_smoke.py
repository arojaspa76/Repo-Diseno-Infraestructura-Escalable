from azure.ai.projects.models import PromptAgentDefinition


def test_definition_builds():
    d = PromptAgentDefinition(model="mi-deployment", instructions="hola")
    assert d.model == "mi-deployment" and d.kind == "prompt"


def test_script_imports():
    import create_prompt_agent, delete_agent  # noqa: F401, E401
