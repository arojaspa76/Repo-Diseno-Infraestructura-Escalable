# Guía docente · Capítulo 4 · Sesión 7
**Optimización de latencia y throughput en LLMs** · 3 h · *Material privado: no publicar en el repositorio del curso (va en `llm-infra-escalable-docente`).*

> Todas las cifras de esta guía son cálculos o valores **hipotéticos** salvo que se indique lo contrario. Ningún resultado de hardware real fue medido al preparar la sesión.

## 0. Antes de la clase (docente)
- [ ] Ejecutar `make test` y `make setup`; confirmar `ollama list` con `llama3.2:1b` y `nomic-embed-text`.
- [ ] Probar `bash labs/lab01_ollama_local/smoke_test.sh` y abrir `http://localhost:5173`.
- [ ] Plan B: `python scripts/fake_ollama.py --port 11435` (números **sintéticos**; decirlo en voz alta).
- [ ] Cuentas *trial* de Azure (primero), GCP y AWS con alerta de presupuesto. Verificar que los nombres de consola coinciden (Microsoft Foundry, Agent Studio, Bedrock Agents).
- [ ] Verificar vigencia de modelos (`ADK_MODEL`, `BEDROCK_MODEL_ID`, despliegue Azure) el día anterior.

## 1. Guion y tiempos
| Min | Bloque | Diapositivas | Idea que debe quedar |
|---|---|---|---|
| 0–5 | Apertura, objetivos, caso | 1–4 | Optimizar = medir primero; cifras del caso son hipotéticas |
| 5–25 | B1 Inferencia y métricas | 5–10 | Prefill (cómputo) vs decode (ancho de banda); TTFT/TPOT; percentiles |
| 25–45 | B2 Profiling | 11–14 | Metodología: línea base, una variable, repetir |
| 45–60 | Demo 1 | 15–16 | E01, E02, E03b: FP16 no cabe en 24 GB (≈24,5 GB), Q8_0 sí (≈17,5 GB) |
| 60–70 | Descanso | — | — |
| 70–90 | B3 Batching y KV cache | 17–24 | Fórmula KV; batching continuo; Little |
| 90–105 | B4 Cuantización y caches | 27–31 | Medir calidad; cache con aislamiento |
| 105–125 | Demo 2 | 25–26 | E03a, E03c, E07, E10 |
| 125–145 | B5 Arquitectura y FinOps | 32–40 | Red/almacenamiento/autoscaling; break-even |
| 145–160 | B6 Seguridad | 41–47 | Defensa en capas; agentes con mínimo privilegio |
| 160–170 | Demo 3 Agentes | 48–53 | Azure en vivo; GCP/AWS como práctica |
| 170–180 | Discusión y cierre | 54–59 | 2–3 preguntas; tarea; limpieza cloud |

*(Los números de diapositiva son orientativos: verifique contra el archivo final.)*

**Si va retrasado:** recortar diapositivas de patrones (B5) y de `Qué evaluar al cuantizar`; nunca seguridad ni discusión.

## 2. Respuestas esperadas
**Discusión (diap. 55)**
1. *GPU propia vs administrado:* depende de volumen sostenido, utilización, datos y costo de operación 24×7; punto de equilibrio (ej. hipotético ≈ 487 M tokens/mes); empezar administrado.
2. *SLO:* TTFT para percepción (streaming); TPOT para lectura fluida; tiempo total si la respuesta se consume completa (batch/API).
3. *Cuantización a 4 bits:* conjunto de evaluación propio (español, dominio), comparación contra Q8/FP16, medición de TTFT y tok/s por separado.
4. *Autoscaling:* concurrencia, cola o utilización de GPU; CPU engaña porque la inferencia está en GPU/memoria; mantener réplicas mínimas por cold start.
5. *Agente que consulta notas:* identidad propia, solo lectura, filtrado por usuario (RLS), aprobación humana si hay escritura, límites y auditoría.

**Autoevaluación del estudiante (`docs/07_guia_estudiante.md`)**
1. TTFT: primer token (domina prefill). TPOT: tiempo entre tokens (domina decode).
2. p50 250 ms y p99 6 s: colas largas (cold start, cola saturada, prompts largos); revisar `load_duration`, cola y distribución de longitudes.
3. 2 × 40 × 8 × 128 × 4096 × 2 B = **671.088.640 B ≈ 640 MiB** (0,625 GiB).
4. Más concurrencia reparte la lectura de pesos (throughput agregado sube) pero cada petición espera más (latencia individual sube).
5. Estático: el lote espera al más largo; continuo: la ranura libre se reasigna en el siguiente paso.
6. Ventajas: memoria, velocidad de decode. Riesgos: calidad dependiente de tarea, soporte de kernels.
7. Vectores de modelos distintos no son comparables.
8. Inyección indirecta: instrucciones dentro de datos recuperados; las reglas sobre el texto del usuario no ven esos canales.
9. Tráfico variable y 100 usuarios: administrado primero; autogestionado si hay volumen sostenido y break-even.
10. Mínimo privilegio: cuenta de solo lectura, vista restringida, sin red, auditoría.

**Comprobación de la diapositiva 13 (hipotético):** 1.000 GB/s ÷ 16 GB ≈ 62 tok/s; ÷ 4,9 GB ≈ 204 tok/s (techo, no medición).

## 3. Errores frecuentes de los estudiantes
- Medir sin calentar el modelo y llamar «lento» al cold start.
- Comparar dos cuantizaciones cambiando además el prompt o el contexto.
- Reportar una sola ejecución; presentar la media sin p95.
- Confundir throughput por solicitud con agregado.
- Suponer que el KV cache no depende de la concurrencia.
- Exponer `adk web` o el puerto 11434 a Internet.
- Olvidar la limpieza cloud (`az group delete`, borrar runtime/ECR, apagar instancias).
- Presentar los números del servidor simulado como mediciones reales.

## 4. Verificación honesta (decirlo a los estudiantes)
Verificado: pruebas del backend (21) y de herramientas (9), compilación del frontend, labs contra servidor simulado, construcción de agentes con los SDK. **Pendiente:** mediciones con Ollama real, ejecución contra nubes reales, build de Docker, Locust. Detalles OWASP 2026 por categoría no revisados; arXiv distintos de vLLM no verificados.

## 5. Rúbrica sugerida del informe (Lab 6)
| Criterio | Peso |
|---|---|
| Método y reproducibilidad (entorno, repeticiones) | 25 % |
| Análisis correcto de TTFT/TPOT/throughput y percentiles | 25 % |
| Dimensionamiento y costo (fórmulas, supuestos explícitos) | 20 % |
| Decisión de arquitectura justificada (trade-offs) | 20 % |
| Seguridad y distinción medido/supuesto | 10 % |
