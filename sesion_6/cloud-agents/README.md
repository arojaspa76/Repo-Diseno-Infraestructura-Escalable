# Agentes en la nube: un mismo agente, tres nubes, siete frameworks

**Qué es un agente (versión corta):** un modelo de lenguaje al que se le entregan *instrucciones* y *herramientas* (funciones que puede pedir que se ejecuten) y que decide, paso a paso, si responde o llama una herramienta.

**Nuestro agente:** «asesor FinOps». Tiene dos herramientas de **solo cálculo** (sin acceso a datos, archivos ni red), definidas una única vez en `common/finops_tools.py`:
1. `estimate_monthly_inference_cost`: costo mensual de una API de LLM pagada por token.
2. `compare_compute_purchase_options`: on-demand vs compromiso vs spot para una flota siempre activa.

Como la lógica es idéntica, lo que cambia entre carpetas es **el framework y la nube**, que es lo que se quiere comparar.

| Nube | 3.1 Consola | 3.2 Código |
|------|-------------|------------|
| Google | `gcp/console/` (A1) | `gcp/adk_agent/` (A2) |
| Azure | `azure/console/` (A3) | `azure/foundry_sdk/` (A4), `azure/maf/` (A5), `azure/semantic_kernel/` (A6), `azure/autogen_legacy/` (A7), `azure/langgraph_agent/` (A8) |
| AWS | `aws/console/` (A9) | `aws/strands_agentcore/` (A10) |

## Reglas que cumplen todos los ejemplos
- **Sin claves en el código:** Entra ID (`az login`), ADC de Google (`gcloud auth application-default login`) o la cadena de credenciales de AWS.
- **Nombres de modelo por variable de entorno:** los identificadores cambian con frecuencia; copie el vigente desde la consola de su nube.
- **`build_agent()` separado de `main()`:** permite construir el agente sin red y probarlo (`test_smoke.py` en cada carpeta).
- **Un entorno virtual por ejemplo:** cada framework fija versiones propias que pueden chocar entre sí.

## Cómo ejecutar las pruebas offline de un ejemplo
```bash
cd cloud-agents/azure/maf
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt pytest
pytest -q test_smoke.py
```
Estas pruebas **no** llaman a la nube; demuestran que el código es coherente con el SDK instalado. La ejecución real está **pendiente de validación** en cada proveedor.

## Actualizar las herramientas compartidas
Edite solo `common/finops_tools.py` y ejecute `python scripts/sync_tools.py` (desde la raíz). `python scripts/sync_tools.py --check` falla si alguna copia está desactualizada (lo corre la integración continua).

## Estado de los frameworks (consultado el 2026-11-17; verifique antes de clase)
- **Microsoft Agent Framework 1.x** es el sucesor unificado de Semantic Kernel y AutoGen. **Use MAF en proyectos nuevos.**
- **Semantic Kernel** y **AutoGen** están en mantenimiento/legado: se incluyen para leer y migrar código existente.
- **Bedrock Agents «clásico»** dejó de aceptar clientes nuevos; el camino actual en AWS es **AgentCore**.
- **Vertex AI** aparece ahora bajo la marca «Gemini Enterprise Agent Platform»; ADK y Agent Engine siguen siendo el camino de código.
