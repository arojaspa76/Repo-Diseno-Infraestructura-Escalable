# A6 · Semantic Kernel (modo mantenimiento)

**Estado:** validado offline (semantic-kernel 1.36.0). **Ejecución real: pendiente.** Framework en mantenimiento: para proyectos nuevos use MAF (A5).

## Equivalencias SK → MAF
| Semantic Kernel | Agent Framework |
|---|---|
| `ChatCompletionAgent` | `Agent` |
| Plugin con `@kernel_function` | Función Python tipada pasada en `tools=[...]` |
| `AzureChatCompletion` | `FoundryChatClient` |

## Ejecución
```bash
cd cloud-agents/azure/semantic_kernel
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
az login && python agent_sk.py
```
El endpoint es el de **Azure OpenAI del mismo recurso** (`https://<recurso>.openai.azure.com/`), no el *project endpoint*.

## Pruebas offline / Seguridad / Costos
`pytest -q test_smoke.py` (incluye cálculo 1,460 USD on-demand). Entra ID con token provider. Costos: tokens.

## Problemas
`ModuleNotFoundError: httpx`: SK no lo declara; ya está en `requirements.txt`. Aviso de Pydantic: inofensivo.

## Limpieza / Reflexión
Sin recursos persistentes. ¿Cuánto costaría migrar 50 plugins de SK a funciones de MAF y cómo lo probaría?
