# Proyectos del Curso — Diseño de Infraestructura Escalable para LLMs

**Curso:** Diseño de Infraestructura Escalable BSG Institute  
**Profesor:** Msc, PgP, Andrés Felipe Rojas Parra  
**Nivel:** Avanzado

---

Este directorio contiene los 7 proyectos finales del curso. Cada proyecto propone una arquitectura LLM de producción diferente, con 12 pasos formales, KPIs medibles y entregables definidos.

---

## Proyectos

### Proyecto 1 — RAG Serverless Multinube
**Archivo:** `Proyecto1_RAG_Serverless_Multinube.md`

Plataforma RAG distribuida en Azure + AWS y/o GCP, 100% serverless. La web app vive en Azure App Service, los documentos en AWS S3, el vector store en GCP (AlloyDB pgvector o Vertex AI Search) y la inferencia en Azure OpenAI o AWS Bedrock. El reto central es minimizar la latencia cross-cloud y el costo de egress, evaluando la calidad del RAG con RAGAS.

---

### Proyecto 2 — LLM Autoscalable sobre Kubernetes
**Archivo:** `Proyecto2_LLM_Autoscalable_Kubernetes.md`

Despliegue de modelos open-source (Llama 3, Gemma, Mistral, Qwen) sobre AKS, EKS o GKE con GPU autoscaling. Incluye HPA, VPA, NVIDIA GPU Operator, Pod Anti-Affinity y canary deployments. Los KPIs clave son tokens/s por pod, latencia P50/P90/P99 y GPU utilization.

---

### Proyecto 3 — Arquitectura de Agentes con Serverless y Tools
**Archivo:** `Proyecto3_Agentes_Serverless_Tools.md`

Diseño y construcción de un agente inteligente que razona, decide acciones, invoca herramientas serverless y ejecuta workflows complejos. Casos de uso: soporte de TI, procesos administrativos, logística o agentes financieros/médicos simulados. KPIs: Task Success Rate, Tool-Call Success Rate y latencia de resolución.

---

### Proyecto 4 — Cost-Optimized LLM Router
**Archivo:** `Proyecto4_Cost_Optimized_LLM_Router.md`

Router inteligente y autoscalable que selecciona el modelo LLM óptimo según complejidad y costo: modelo barato para consultas simples, mediano para generación y premium (GPT-4o / Claude 3.5 / Gemini Ultra) para razonamiento complejo. KPIs: routing accuracy, ahorro de costo (%) y latencia por tipo de consulta.

---

### Proyecto 5 — Distributed RAG con Sharding
**Archivo:** `Proyecto5_Distributed_RAG_Shards.md`

Arquitectura RAG distribuida con sharding por dominio (Legal, HSE, Técnico, Operaciones), multi-index, replicación multi-región, query rewriting y re-ranking avanzado. Diseñada para grandes repositorios empresariales con SLA diferenciado por dominio. KPIs: retrieval accuracy por shard y latencia cross-region.

---

### Proyecto 6 — LLM Pipeline para Enterprise Search
**Archivo:** `Proyecto6_Enterprise_Search_LLM.md`

Motor de búsqueda empresarial semántico con indexación distribuida, RAG multi-modal (texto, imágenes, tablas, PDFs complejos), caching de embeddings y document scoring avanzado. Aplica a búsqueda interna corporativa, bases de conocimiento y manuales técnicos. KPIs: Recall@K, Precision@K, MRR y latencia de búsqueda.

---

### Proyecto 7 — LLM Data Engineering Pipeline
**Archivo:** `Proyecto7_LLM_Data_Engineering_Pipeline.md`

Pipeline completo de ingeniería de datos para LLMs: ingesta y normalización de PDFs, Word y HTML; chunking estratégico; generación de embeddings; indexación cloud y versionamiento. Volumen mínimo de 300–1000 documentos. KPIs: tiempo total del pipeline, calidad del chunking (RAGAS), cobertura de metadatos y costo total.

---

## Estructura de cada proyecto

Todos los proyectos siguen los mismos **12 pasos formales**:

1. Definición del caso de uso y KPIs
2. Decisión de arquitectura y justificación
3. Diseño del componente de inferencia
4. Diseño del componente de recuperación / routing / agente
5. Gestión de secretos e identidad (sin claves en código)
6. Seguridad y control de acceso
7. Observabilidad (trazas, métricas, logs)
8. Escalabilidad y manejo de carga
9. Alta disponibilidad y disaster recovery
10. Optimización de costos
11. Pruebas (unitarias, de integración, de carga)
12. Entregable y rúbrica de evaluación
