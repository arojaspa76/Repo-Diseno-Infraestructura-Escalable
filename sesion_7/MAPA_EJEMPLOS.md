# Mapa de ejemplos: de la presentación al código

En la presentación cada ejemplo aparece con una **etiqueta** (por ejemplo `E03a`). Esta tabla le dice **dónde está** y **cómo ejecutarlo**.
Todas las rutas son relativas a la carpeta `sesion_07/`.

## A · Laboratorio local (Ollama + Python + FastAPI + React)

| Etiqueta | Qué es | Ruta | Comando para ejecutarlo | Cap. de la presentación |
|---|---|---|---|---|
| **E01** | Ollama local: instalar, descargar, probar | `labs/lab01_ollama_local/` | `bash labs/lab01_ollama_local/install_and_pull.sh` | Demo 1 |
| **E02** | Profiling de CPU/RAM/GPU/red | `labs/lab02_profiling/profile_system.py` | `python labs/lab02_profiling/profile_system.py --cold` | Bloque 2 |
| **E03a** | Concurrencia vs throughput | `labs/lab03_batching_kvcache/bench_concurrency.py` | `python labs/lab03_batching_kvcache/bench_concurrency.py --levels 1,2,4,8` | Bloque 3 |
| **E03b** | Calculadora de KV cache | `labs/lab03_batching_kvcache/kv_cache_calculator.py` | `python labs/lab03_batching_kvcache/kv_cache_calculator.py --preset llama-3.1-8b --gpu-gb 24` | Bloque 3 |
| **E03c** | Reuso de prefijo | `labs/lab03_batching_kvcache/prefix_cache_experiment.py` | `python labs/lab03_batching_kvcache/prefix_cache_experiment.py` | Bloque 3 |
| **E03d** | Simulador de batching estático vs continuo | `labs/lab03_batching_kvcache/batching_simulator.py` | `python labs/lab03_batching_kvcache/batching_simulator.py` | Bloque 3 |
| **E04a** | Estimador de cuantización | `labs/lab04_quantizacion/quant_estimator.py` | `python labs/lab04_quantizacion/quant_estimator.py --params-b 8.03` | Bloque 4 |
| **E04b** | Comparación de cuantizaciones | `labs/lab04_quantizacion/quant_compare.py` | ver `labs/lab04_quantizacion/README.md` | Bloque 4 |
| **E05** | Cache de embeddings + batching | `labs/lab05_cache_embeddings/embedding_cache_bench.py` | `python labs/lab05_cache_embeddings/embedding_cache_bench.py` | Bloque 4 |
| **E06a** | Reporte comparativo | `labs/lab06_analisis_comparativo/compare_results.py` | `python labs/lab06_analisis_comparativo/compare_results.py` | Bloque 5 |
| **E06b** | Punto de equilibrio FinOps | `labs/lab06_analisis_comparativo/finops_breakeven.py` | `python labs/lab06_analisis_comparativo/finops_breakeven.py` | Bloque 5 |
| **E07** | **Aplicación completa**: backend FastAPI + frontend React | `app/` | `make backend` y `make frontend`, o `cd app && docker compose up --build` | Demo 2 |
| **E08** | Guardrails (inyección, PII) | `app/backend/app/services/security.py` + pestaña *Guardrails* | Abrir `http://localhost:5173` → pestaña 4 | Bloque 6 |
| **E09** | Calculadora de memoria en la web | `app/backend/app/routers/capacity.py` + pestaña *Calculadora* | Pestaña 3 del frontend | Bloque 3 |
| **E10** | Prueba de carga con Locust | `loadtest/locustfile.py` | `locust -f loadtest/locustfile.py --host http://localhost:8000` | Bloque 5 |

## B · Agentes en la nube (consola + código)

El agente de ejemplo es siempre el mismo: **Asesor de capacidad** (`cloud_agents/shared/capacity_tools.py`).

| Etiqueta | Nube | Qué es | Ruta | Cómo ejecutarlo |
|---|---|---|---|---|
| **G1** | Google Cloud | Agente desde la **consola** (Agent Studio) | `cloud_agents/gcp/README.md` (Parte 1) | Seguir los pasos de la guía |
| **G2** | Google Cloud | Agente con **ADK** | `cloud_agents/gcp/adk_agent/capacity_advisor/agent.py` | `adk run capacity_advisor` |
| **G2b** | Google Cloud | ADK desde Python / despliegue | `.../adk_agent/run_programmatic.py`, `deploy_agent_engine.sh` | ver README |
| **A1** | Azure | Agente desde el **portal de Foundry** | `cloud_agents/azure/README.md` (Parte 1) | Seguir los pasos de la guía |
| **A2** | Azure | **Microsoft Agent Framework** | `cloud_agents/azure/agent_framework/agent.py` | `python agent.py` |
| **A3** | Azure | **Semantic Kernel** | `cloud_agents/azure/semantic_kernel/agent.py` | `python agent.py` |
| **A4** | Azure | **AutoGen** | `cloud_agents/azure/autogen/agent.py` | `python agent.py` |
| **A5** | Azure | **LangGraph** | `cloud_agents/azure/langgraph/agent.py` | `python agent.py` |
| **W1** | AWS | Agente desde la **consola de Bedrock** | `cloud_agents/aws/README.md` (Parte 1) | Seguir los pasos de la guía |
| **W1b** | AWS | Invocar ese agente con boto3 | `cloud_agents/aws/bedrock_agents_boto3/invoke_agent.py` | `python invoke_agent.py "..."` |
| **W2** | AWS | **Strands Agents + AgentCore Runtime** | `cloud_agents/aws/strands_agentcore/agent.py` | `python agent.py` (+ `deploy.sh`) |
| **L1–L3** | Las tres | **TTFT** del modelo administrado de cada nube | `cloud_agents/managed_latency/` | ver README de cada nube |

## C · Documentación

| Documento | Para qué |
|---|---|
| `docs/00_guia_instalacion_ubuntu.md` | Preparar el computador |
| `docs/01_arquitectura.md` | Diagramas, requisitos y mapa a la nube |
| `docs/02_conceptos_clave.md` | **Léalo antes de clase**: TTFT, KV cache, batching, cuantización |
| `docs/03_arquitecturas_multicloud.md` | Comparación Azure / GCP / AWS |
| `docs/04_seguridad_llm.md` | OWASP LLM Top 10 y controles del repositorio |
| `docs/05_costos_finops.md` | Costos por token vs por GPU |
| `docs/06_referencias.md` | Bibliografía y documentación oficial |
| `docs/07_guia_estudiante.md` | Actividades y autoevaluación |
| `docs/adr/` | Decisiones de arquitectura (ADR) |
