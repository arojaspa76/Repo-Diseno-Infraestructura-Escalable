# Guía del estudiante · Sesión 7

## Antes de la clase (30 min)
1. Instale el entorno: [`00_guia_instalacion_ubuntu.md`](00_guia_instalacion_ubuntu.md).
2. Lea [`02_conceptos_clave.md`](02_conceptos_clave.md) completo.
3. Ejecute `bash labs/lab01_ollama_local/install_and_pull.sh` y `bash labs/lab01_ollama_local/smoke_test.sh`.

## Durante la clase
Tenga abierto `MAPA_EJEMPLOS.md`: cuando el docente nombre un ejemplo (E03a, A2…), ubíquelo allí y siga en su máquina.

## Después de la clase — actividades

| # | Actividad | Entregable | Tiempo |
|---|---|---|---|
| 1 | Complete la tabla de profiling del Lab 2 | Tabla con SUS mediciones | 30 min |
| 2 | Ejecute el Lab 3a con 3 repeticiones | Tabla + gráfica (Lab 6) | 40 min |
| 3 | Calcule capacidad para su GPU (o una de 24 GB) con `kv_cache_calculator.py` | Respuesta a "¿cuántas conversaciones caben?" | 20 min |
| 4 | Compare dos cuantizaciones (Lab 4b) | Tabla + 5 líneas de interpretación con salvedades | 40 min |
| 5 | Intente evadir los guardrails (`docs/04_seguridad_llm.md`, ejercicio) | Lista de intentos y resultado | 30 min |
| 6 | Cree el agente de **una** nube desde la consola y desde código | Capturas + 1 párrafo comparando ambas formas | 60 min |
| 7 | **Informe final** con `labs/lab06_analisis_comparativo/report_template.md` | Informe ≤ 2 páginas | 60 min |

## Autoevaluación (responda sin mirar el material)

1. Defina TTFT y TPOT y diga cuál de las dos fases (prefill / decode) domina cada una.
2. Un servicio tiene TTFT p50 = 250 ms y p99 = 6 s. ¿Qué problema sospecha y cómo lo investigaría?
3. Calcule el KV cache por conversación de un modelo con 40 capas, 8 cabezas KV, dimensión de cabeza 128, FP16, contexto 4 096.
4. ¿Por qué aumentar la concurrencia mejora el throughput total pero empeora la latencia individual?
5. Explique con sus palabras la diferencia entre batching estático y continuo.
6. Mencione dos ventajas y dos riesgos de cuantizar un modelo a 4 bits.
7. ¿Por qué la cache de embeddings usa el *modelo* como parte de la clave?
8. ¿Qué es una inyección de prompt **indirecta** y por qué las reglas de texto no la detienen?
9. Compare inferencia administrada vs autogestionada para 100 usuarios concurrentes con tráfico muy variable.
10. ¿Qué mínimos privilegios daría a un agente cuya herramienta consulta una base de datos de notas?

## Lecturas complementarias
Ver [`06_referencias.md`](06_referencias.md). Comience por el artículo de vLLM/PagedAttention (arXiv:2309.06180) y la documentación del proveedor que usará en su proyecto.
