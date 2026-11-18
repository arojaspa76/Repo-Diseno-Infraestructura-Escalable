# A4 · Agente con el SDK de Microsoft Foundry (`azure-ai-projects` 2.x)

**Estado:** validado offline (2 pruebas con azure-ai-projects 2.11.0). **Ejecución real: pendiente.**

> El SDK 2.x apunta a la API «Foundry projects (new)». Tutoriales anteriores (SDK 1.x, *Assistants*/«classic agents») usan otra API y no son compatibles.

## Objetivo
Crear un agente versionado por código y conversar con él mediante la Responses API.

## Arquitectura
`AIProjectClient` → `agents.create_version(PromptAgentDefinition)` → `get_openai_client().responses.create(… agent_reference …)`.

## Prerrequisitos
Proyecto Foundry + deployment (ver `../console`), `az login`, rol **Azure AI User**.

## Ejecución
```bash
cd cloud-agents/azure/foundry_sdk
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env     # complete endpoint y deployment
python create_prompt_agent.py "¿Cuándo conviene un compromiso de 1 año frente a on-demand?"
python delete_agent.py                                       # limpieza
```
Resultado esperado: «Agente creado: finops-advisor-s06 (versión N)», la respuesta y el conteo de tokens.

## Pruebas offline
`pip install pytest && pytest -q test_smoke.py`

## Seguridad
`DefaultAzureCredential` (Entra ID), sin claves. Este agente **no tiene herramientas**; para herramientas de código use A5/A8.

## Costos
Tokens del modelo desplegado. Cuentas de prueba: ver avisos en `../console`.

## Problemas
- `401/403`: falta el rol Azure AI User o `az login` expiró.
- `DeploymentNotFound`: `FOUNDRY_MODEL_DEPLOYMENT` debe ser el **nombre del deployment**, no del modelo base.

## Limpieza
`python delete_agent.py`; elimine el deployment si ya no lo usa.

## Reflexión
¿Qué significa que el agente sea *versionado* (`create_version`) y cómo apoyaría el control de cambios y el rollback?
