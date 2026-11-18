# A7 · AutoGen 0.7 (LEGADO)

**Estado:** validado offline (autogen-agentchat 0.7.5). **Ejecución real: pendiente.** AutoGen fue sucedido por Microsoft Agent Framework; el repositorio está en mantenimiento/archivado. **No lo use en proyectos nuevos**; está aquí para leer y migrar código existente.

## Equivalencias AutoGen → MAF
| AutoGen | Agent Framework |
|---|---|
| `AssistantAgent` | `Agent` |
| `AzureOpenAIChatCompletionClient` | `FoundryChatClient` |
| `reflect_on_tool_use=True` | comportamiento por defecto de redactar la respuesta final tras la herramienta (verifique en su versión) |

## Ejecución
```bash
cd cloud-agents/azure/autogen_legacy
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
az login && python agent_autogen.py
```
Requiere además `AZURE_OPENAI_BASE_MODEL` (AutoGen necesita conocer las capacidades del modelo).

## Pruebas offline / Seguridad / Costos / Limpieza
`pytest -q test_smoke.py`. Entra ID con token provider. Costos: tokens. Sin recursos persistentes.

## Reflexión
¿Qué riesgos de seguridad y operación implica depender de un framework sin mantenimiento activo (parches, CVE, compatibilidad)? (OWASP LLM04: cadena de suministro.)
