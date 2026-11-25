# ADR-001 — Ollama como motor de inferencia del laboratorio local

- **Estado:** Aceptada · **Contexto:** Sesión 7 (laboratorio reproducible en computadores de estudiantes)

## Contexto
Los estudiantes tienen hardware heterogéneo (portátiles sin GPU, algunos con GPU NVIDIA). El laboratorio necesita un motor de inferencia
que se instale con un comando, sirva una API HTTP estable y permita medir TTFT, TPOT y throughput.

## Alternativas consideradas
| Alternativa | A favor | En contra |
|---|---|---|
| **Ollama** | Instalación de un comando, modelos cuantizados (GGUF) listos, API simple, funciona en CPU, estadísticas de tiempos en cada respuesta | Menos control de batching/KV cache que vLLM; no es el estándar de producción multi-GPU |
| vLLM | PagedAttention, batching continuo, alto throughput | Requiere GPU NVIDIA (o configuración específica); instalación más pesada |
| llama.cpp (server) | Máximo control, base de Ollama | Más configuración manual |
| Solo APIs administradas | Cero infraestructura | No permite estudiar el comportamiento del servidor; requiere cuentas y costos |

## Decisión
Usar **Ollama** en el laboratorio y **explicar vLLM teóricamente** (y como ruta de producción en Kubernetes con GPU).

## Consecuencias
- (+) Todos los estudiantes pueden reproducir los laboratorios.
- (−) Los números de Ollama **no se extrapolan** a vLLM ni a endpoints administrados; el material lo advierte explícitamente.
- (−) Los experimentos de batching dependen de `OLLAMA_NUM_PARALLEL` y de la memoria disponible.
