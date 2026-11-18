# Estado de validación (qué se probó y qué no)

Fecha de preparación: 2026-11-17. Entorno: Linux, Python 3.12.

## Probado (automatizado, ejecutado)
| Componente | Prueba | Resultado |
|---|---|---|
| Gateway FastAPI (`backend/`) | 33 pruebas Pytest (API, seguridad, FinOps, proveedor Ollama con respuestas simuladas) | Pasan |
| Arranque del gateway | `uvicorn app.main:build_default_app --factory` en un entorno limpio con solo `backend/requirements.txt`; `/health` y `/metrics` responden | OK |
| Comportamiento de lab 5 y 7 | Inyección → 400; PII redactada antes del modelo; entrada enorme → 413; presupuesto agotado → 429 tras la primera solicitud | Verificado con proveedor simulado |
| Simulador FinOps (`finops/`) | 15 pruebas; salidas del lab 3 y 4 reproducidas | Pasan |
| Generador de carga (`loadtest/`) | 4 pruebas con servidor simulado | Pasan |
| Frontend React 18 / Vite 6 | `tsc`, 4 pruebas Vitest, `vite build` | OK |
| Herramientas compartidas | 6 pruebas; copias idénticas (`scripts/sync_tools.py --check`) | OK |
| Ejemplos cloud (A2, A4–A8, A10) | Pruebas de humo **offline**: el agente se construye con el SDK real y las herramientas se ejecutan | Pasan |

## NO probado (pendiente)
- Ejecución real contra **Vertex AI/Gemini, Microsoft Foundry y Amazon Bedrock/AgentCore** (requiere cuentas, créditos y modelos habilitados).
- Guías de consola A1, A3, A9 (basadas en documentación; etiquetas de UI pueden variar).
- Despliegues (`adk deploy`, AgentCore Runtime).
- **Docker Compose y los Dockerfiles** (escritos, no construidos).
- Mediciones reales de tokens/s, TTFT y p95 con Ollama: dependen del hardware de cada quien; este material **no incluye cifras de rendimiento**.
- Precios: el catálogo es **ilustrativo**; no hay precios reales de ningún proveedor.

## Versiones usadas en la validación
google-adk 2.14.1 · azure-ai-projects 2.11.0 · agent-framework-core 1.26.0 / agent-framework-foundry 1.16.2 · semantic-kernel 1.36.0 · autogen-agentchat 0.7.5 · langgraph 1.2.22 / langchain-azure-ai 1.2.3 · strands-agents 1.65.0 / bedrock-agentcore 1.26.0 · boto3 1.44.5.
