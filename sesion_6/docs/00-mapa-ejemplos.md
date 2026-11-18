# Mapa de ejemplos (índice 3.3)

Cada ejemplo mostrado en la presentación (`Sesion6-FinOps-Seguridad-LLM.pptx`) tiene un **ID**, una **ruta en este repositorio** y la **diapositiva** donde se usa. Si el profesor dice «ejercicio E3», aquí encuentra dónde está.

> Estado: «Validado offline» = la prueba automatizada se ejecutó con el SDK real instalado, **sin llamar a ninguna nube**. «Pendiente en nube» = requiere cuenta/créditos; el procedimiento está documentado, pero **no se ejecutó** contra el servicio real. Detalle en `08-estado-validacion.md`.

## A. Laboratorios locales (Ollama + FastAPI + React)

| ID | Qué se hace | Ruta | Diapositiva | Estado |
|----|-------------|------|-------------|--------|
| E1 | Comparar on-demand / compromiso / spot con el simulador | `labs/lab3-simulador-compras/` · código `finops/` | 16–17 | Validado (15 pruebas) |
| E2 | Rightsizing con p95 y punto de equilibrio API vs autogestionado | `labs/lab4-rightsizing-breakeven/` · `finops/` | 22–23 | Validado |
| E3 | Presupuesto por cliente, alertas 50/80/100 % y bloqueo | `labs/lab5-presupuestos/` · `backend/app/finops/` | 27–28 | Validado (33 pruebas del gateway) |
| E4 | Seguridad: inyección de prompt, PII, límites de entrada | `labs/lab7-seguridad/` · `backend/app/security/` | 35, 37 | Validado |
| E5 | Ollama local + gateway + dashboard | `labs/lab1-ollama/`, `labs/lab2-gateway/` · `backend/`, `frontend/` | 43 | Gateway y front validados; Ollama real **pendiente** de medir en su equipo |
| E6 | Prueba de carga (TTFT, p95, disponibilidad vs SLO) | `labs/lab6-carga/` · `loadtest/` | 20, 43 | Lógica validada con servidor simulado; mediciones reales **pendientes** |

## B. Agentes en la nube

Todos usan las **mismas dos herramientas FinOps** (`cloud-agents/common/finops_tools.py`) para que la comparación entre frameworks sea justa: cambia el framework, no la lógica.

| ID | Nube | Tipo | Ruta | Diapositiva | Estado |
|----|------|------|------|-------------|--------|
| A1 | Google | Consola (3.1): Agent Designer | `cloud-agents/gcp/console/` | 41–42 | Guía; **pendiente en nube** |
| A2 | Google | Código (3.2): ADK | `cloud-agents/gcp/adk_agent/` | 41–42 | Validado offline (construcción + herramienta) |
| A3 | Azure | Consola (3.1): portal Foundry | `cloud-agents/azure/console/` | 40, 42 | Guía; **pendiente en nube** |
| A4 | Azure | Código: SDK Foundry (`azure-ai-projects` 2.x) | `cloud-agents/azure/foundry_sdk/` | 40, 42 | Validado offline |
| A5 | Azure | Código: Microsoft Agent Framework (recomendado) | `cloud-agents/azure/maf/` | 40, 42 | Validado offline |
| A6 | Azure | Código: Semantic Kernel (mantenimiento) | `cloud-agents/azure/semantic_kernel/` | 40 | Validado offline |
| A7 | Azure | Código: AutoGen (legado) | `cloud-agents/azure/autogen_legacy/` | 40 | Validado offline |
| A8 | Azure | Código: LangGraph | `cloud-agents/azure/langgraph_agent/` | 40, 42 | Validado offline |
| A9 | AWS | Consola (3.1): AgentCore (harness) | `cloud-agents/aws/console/` | 41–42 | Guía; **pendiente en nube** |
| A10 | AWS | Código (3.2): Strands + AgentCore Runtime | `cloud-agents/aws/strands_agentcore/` | 41–42 | Validado offline |

**Orden recomendado para la demostración en vivo:** Azure primero (A3 → A5), luego Google (A1 → A2) y AWS (A9 → A10). Los estudiantes con cuenta de prueba pueden hacer A3/A4/A5 sin pasar a pago por uso; revise los avisos de costo de cada carpeta.

## C. Documentación de apoyo

| Documento | Para qué sirve | Diapositivas |
|-----------|----------------|--------------|
| `01-arquitecturas-y-patrones.md` | Arquitectura base, patrones (gateway, router, caché, cola, circuit breaker, RAG), diagramas | 30–32 |
| `03-seguridad-llm.md` | OWASP LLM Top 10 2026 → controles del código | 34–37 |
| `04-finops-llm.md` | Teoría FinOps, fórmulas, calculadoras oficiales | 6–28 |
| `05-guia-estudiante.md` | Glosario, ejercicios, autoevaluación | todas |
| `adr/` | Decisiones de arquitectura (ADR) | 27 |
| `07-solucion-de-problemas.md` | Errores frecuentes | — |
| `08-estado-validacion.md` | Qué se probó y qué falta | — |
| `09-referencias.md` | Fuentes con fecha de consulta | 46 |
