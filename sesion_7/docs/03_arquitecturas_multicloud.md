# Arquitecturas y servicios por nube (estado verificado el 24-nov-2026)

> Los nombres comerciales cambian con rapidez. Esta tabla recoge lo **verificado en documentación oficial durante la preparación de la sesión**;
> antes de usarlo en un proyecto real, confirme el estado vigente (enlaces en `docs/06_referencias.md`).

## Resumen comparativo

| Aspecto | Google Cloud | Microsoft Azure | AWS |
|---|---|---|---|
| Plataforma de IA | **Gemini Enterprise Agent Platform** (la documentación la describe como evolución de Vertex AI) | **Microsoft Foundry** (antes Azure AI Foundry) | **Amazon Bedrock** |
| Creación de agentes sin código | **Agent Studio** (antes *Agent Designer*, vista previa): lienzo visual, chat de prueba y botón *Get code* | **Foundry portal → Agents**: *prompt agents* (sin código) y *workflow agents* (vista previa) | **Bedrock console → Agents**: agente + *action groups* (Lambda / OpenAPI) + alias |
| Framework de código | **ADK** (Agent Development Kit, Apache 2.0): Python, Java, Go | **Microsoft Agent Framework (MAF)**, sucesor de Semantic Kernel y AutoGen (v1.0 en abril de 2026); también LangGraph y otros | **Strands Agents SDK** (open source) + **AgentCore** para operar cualquier framework |
| Runtime administrado de agentes | **Agent Runtime / Vertex AI Agent Engine** | **Foundry Agent Service** (incluye *hosted agents*, vista previa) | **Bedrock AgentCore Runtime** (serverless; contrato `/invocations` + `/ping`) |
| Identidad del agente | IAM / cuentas de servicio | Microsoft Entra ID, roles *Foundry User/Owner…* | IAM, AgentCore Identity |
| Observabilidad de agentes | Cloud Trace / Monitoring | Foundry Control Plane (trazas), Application Insights, OpenTelemetry | AgentCore Observability (CloudWatch) |
| Despliegue en contenedor | Cloud Run, GKE | Container Apps, AKS | ECS/Fargate, EKS |

## Qué framework usar en Azure (los "4 frameworks" del curso)

| Framework | Estado en la documentación consultada | Cuándo usarlo en este curso |
|---|---|---|
| **Microsoft Agent Framework** | Recomendado para proyectos nuevos; v1.0 (abr-2026); unifica SK + AutoGen | **Opción principal** |
| **Semantic Kernel** | Vigente, con guía de migración hacia MAF | Para leer/mantener código existente |
| **AutoGen** | Sucedido por MAF (migración documentada) | Investigación y código heredado |
| **LangGraph** (+ LangChain) | Independiente de Microsoft; funciona con modelos de Azure OpenAI | Cuando el equipo ya usa el ecosistema LangChain |

Código de los cuatro en [`cloud_agents/azure/`](../cloud_agents/azure/) — misma herramienta, mismo prompt, cuatro frameworks.

## Inferencia administrada vs autogestionada (resumen de decisión)

| Criterio | Administrada (Foundry / Gemini / Bedrock) | Autogestionada (vLLM/Ollama en GPU propia) |
|---|---|---|
| Time-to-market | Minutos | Semanas |
| Costo a bajo volumen | Pago por token: económico | GPU ociosa: caro |
| Costo a volumen alto y estable | Puede encarecerse | Puede ser más barato si la GPU se usa bien (ver `docs/05_costos_finops.md`) |
| Control (latencia, batching, cuantización, modelo) | Limitado | Total |
| Privacidad / residencia de datos | Depende de contrato y región | Control total (dentro de su red) |
| Carga operativa | Baja | Alta (drivers, escalado, parches, observabilidad) |

**Regla práctica para el caso universitario (5 000 usuarios, 100 concurrentes — hipótesis de clase):** empezar con **inferencia administrada** y mover a
autogestionada solo si los datos o el costo lo justifican con mediciones reales.

## Patrones de diseño para LLMs en la nube

1. **API Gateway + backend sin estado** delante del modelo (autenticación, cuotas, guardrails, métricas).
2. **Streaming** extremo a extremo (SSE) para latencia percibida.
3. **Cache** por capas: embeddings, respuestas frecuentes (con cuidado de privacidad), prefijos (KV).
4. **Cola + *autoscaling* por saturación** (profundidad de cola / uso de KV cache) en lugar de solo CPU.
5. **Fallback multi-modelo / multi-región** con *circuit breaker* y *timeouts* explícitos.
6. **Enrutamiento por complejidad**: modelo pequeño para casos simples, grande para difíciles.
7. **Agentes con herramientas de mínimo privilegio** y registro de auditoría de cada llamada.
