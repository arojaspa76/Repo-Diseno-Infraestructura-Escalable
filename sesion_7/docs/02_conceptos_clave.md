# Conceptos clave de la sesión (explicados desde cero)

Lea este documento **antes** de la clase. No necesita conocimientos previos de inferencia de modelos.

## 1. ¿Qué pasa cuando le pregunta algo a un LLM?

Un LLM genera la respuesta **un token a la vez** (un token es un trozo de palabra, aprox. ¾ de palabra en inglés; en español suele ser algo más corto).
Para generar cada token necesita "recordar" todo lo anterior. El proceso tiene **dos fases** con comportamientos muy distintos:

| Fase | Qué hace | Analogía | Cuello de botella típico |
|---|---|---|---|
| **Prefill** | Lee todo el prompt de una vez y prepara la memoria interna | Leer la pregunta completa antes de responder | **Cómputo** (la GPU hace muchas operaciones en paralelo) |
| **Decode** | Genera la respuesta token por token | Escribir la respuesta palabra a palabra | **Ancho de banda de memoria** (cada token obliga a leer todos los pesos del modelo) |

> **Consecuencia práctica:** un prompt largo aumenta el *prefill* (tarda más en aparecer el primer token); una respuesta larga aumenta el *decode*.
> Por eso se optimizan por separado.

## 2. Las métricas que usaremos

| Métrica | Significado | Qué percibe el usuario | Cómo se mide en el repositorio |
|---|---|---|---|
| **TTFT** (Time To First Token) | Tiempo hasta el primer token | "¿Ya empezó a responder?" | `ttft_ms` (backend y labs) |
| **TPOT** (Time Per Output Token) | Tiempo medio entre tokens en el decode | Fluidez de la escritura | `tpot_ms` |
| **Latencia extremo a extremo** | TTFT + TPOT × (tokens − 1) | Tiempo total de espera | `total_ms` |
| **Throughput** | Tokens/segundo (de un usuario o de todo el sistema) | — (lo siente el *costo* y la capacidad) | `decode_tok_s`, `aggregate_tok_s` |
| **Percentiles p50/p95/p99** | El p95 es el valor que el 95 % de las peticiones no supera | La "cola" de malas experiencias | Panel *Métricas del servidor* |

**Latencia vs throughput:** son objetivos en tensión. Agrupar más peticiones en un *batch* aumenta el throughput total (más tokens por segundo
en el sistema) pero cada usuario espera un poco más. El diseño consiste en elegir el punto de operación según el SLO.

## 3. KV cache: la "memoria de trabajo" del modelo

Al generar un token, el modelo calcula para cada token anterior unos vectores llamados **K (keys)** y **V (values)**. Si los volviera a calcular en cada paso,
el costo crecería sin control. Se **guardan** (KV cache) y se reutilizan.

- **Ventaja:** el decode evita recalcular todo el pasado.
- **Costo:** ocupa memoria de GPU y **crece linealmente** con el contexto y con el número de conversaciones.

**Fórmula (por conversación):**

```
bytes_KV = 2 (K y V) × capas × cabezas_KV × dimensión_de_cabeza × tokens × bytes_por_elemento
```

**Ejemplo (Llama 3.1 8B, valores del `config.json` público):** 32 capas, 8 cabezas KV, dimensión 128, FP16 (2 bytes):
`2 × 32 × 8 × 128 × 2 = 131 072 bytes = 128 KiB por token` → **8 192 tokens ≈ 1 GiB por conversación**.
Con 8 conversaciones simultáneas son 8 GiB solo de KV cache, *además* de los ≈ 15 GiB de pesos en FP16.
Compruébelo con `python labs/lab03_batching_kvcache/kv_cache_calculator.py --preset llama-3.1-8b`.

**GQA/MQA:** muchos modelos modernos comparten cabezas K/V (Grouped-Query Attention) justamente para reducir este costo (Llama 3.1 8B: 32 cabezas de consulta, 8 de KV → 4× menos KV cache).

**Reuso de prefijo (prefix caching):** si muchas peticiones comparten el mismo comienzo (p. ej. un prompt de sistema largo), el servidor puede reutilizar el KV cache de ese prefijo y
evitar repetir el prefill. Lab 3c lo mide.

**PagedAttention (vLLM):** gestiona el KV cache en bloques de tamaño fijo, como la memoria virtual de un sistema operativo, reduciendo el desperdicio por fragmentación y
permitiendo batches más grandes (Kwon et al., 2023).

## 4. Batching: agrupar para ser eficiente

La GPU es muy eficiente cuando hace muchas cosas a la vez. En el decode, leer los pesos del modelo para **un** token es igual de caro que para **varios** tokens de distintos usuarios.

| Tipo | Cómo funciona | Problema / ventaja |
|---|---|---|
| **Sin batching** | Una petición a la vez | GPU subutilizada |
| **Batching estático** | Se forma un grupo y se espera a que termine la petición más larga | Huecos ociosos: las cortas esperan a la larga |
| **Batching continuo** (*continuous / in-flight*) | Cuando una petición termina, otra ocupa su lugar de inmediato | Mejor utilización y throughput (Yu et al., Orca, 2022; vLLM) |

Compruébelo sin GPU: `python labs/lab03_batching_kvcache/batching_simulator.py` (simulación pedagógica).

## 5. Cuantización: menos bits por peso

Los pesos se guardan normalmente en 16 bits (FP16/BF16). **Cuantizar** es representarlos con menos bits (8, 4…).

| Formato | Bits aprox. por peso | Memoria de un modelo 8B | Observación |
|---|---:|---:|---|
| FP16 | 16 | ≈ 15 GB | Referencia |
| Q8_0 | 8.5 | ≈ 8 GB | Pérdida de calidad normalmente muy pequeña |
| Q4_K_M | 4.85 | ≈ 4.5 GB | Muy popular; pérdida moderada |
| Q2_K | 2.96 | ≈ 2.8 GB | Degradación notable |

*(Bits efectivos aproximados de GGUF/llama.cpp; ver `labs/lab04_quantizacion/quant_estimator.py`.)*

**Por qué también acelera:** el decode está limitado por el ancho de banda de memoria; pesos más pequeños ⇒ menos bytes que leer por token.
**Por qué importa la evaluación:** menos bits puede degradar calidad; hay que medirla en *su* tarea (el Lab 4 incluye una sonda mínima y explica sus límites).

## 6. Cache de embeddings

Un *embedding* convierte un texto en un vector numérico (para búsqueda semántica/RAG). Es una función **determinista**: mismo modelo + mismo texto = mismo vector.
Si un texto se repite (preguntas frecuentes, documentos re-indexados), recalcularlo es desperdicio. Se guarda en una cache con clave `hash(modelo, texto)`.
Además, enviar muchos textos en **una sola llamada** (batching) cuesta mucho menos que una llamada por texto. Lab 5 mide ambos efectos.

## 7. Profiling: medir antes de optimizar

Optimizar sin medir es adivinar. Se mide en cuatro frentes:

| Recurso | Qué mirar | Herramientas |
|---|---|---|
| **GPU** | Utilización, VRAM usada, qué parte del modelo cabe en GPU | `nvidia-smi`, `ollama ps` |
| **CPU** | Uso por núcleo, si el *tokenizer*/servidor es cuello de botella | `htop`, `psutil` |
| **RAM** | Si el modelo se "derrama" a memoria del sistema (muy lento) | `free -h` |
| **Red** | Latencia al servidor, tamaño de respuestas, buffering de proxies | `curl -w`, `ping` |

## 8. Glosario rápido

- **Token:** unidad de texto que procesa el modelo.
- **Contexto (ventana):** máximo de tokens (prompt + respuesta) que el modelo puede considerar.
- **Cold start:** primera petición tras cargar el modelo en memoria (incluye `load_duration`).
- **SLI / SLO / SLA:** indicador medible / objetivo interno sobre ese indicador / compromiso contractual.
- **Throughput agregado:** tokens/s sumando todos los usuarios simultáneos.
- **Autoscaling:** aumentar/disminuir réplicas según una métrica (en LLMs suelen preferirse métricas como cola de peticiones o utilización de KV cache, no solo CPU).
- **Speculative decoding:** un modelo pequeño propone varios tokens y el grande los verifica en una sola pasada (acelera el decode sin cambiar la salida).
- **Chunked prefill / desagregación prefill-decode:** técnicas de servidores avanzados para que los prefill largos no bloqueen a los decode de otros usuarios.

## Preguntas de autoevaluación

1. ¿Por qué un prompt de 8 000 tokens afecta más al TTFT que al TPOT?
2. Calcule el KV cache de Llama 3.1 70B (80 capas, 8 cabezas KV, dim. 128, FP16) para 4 096 tokens y 10 conversaciones. *(Respuesta: ≈ 12.5 GiB — verifíquelo con la calculadora.)*
3. ¿Por qué el batching continuo mejora la utilización respecto al estático?
4. Si el p50 de TTFT es 300 ms y el p99 es 4 s, ¿qué le dice eso del sistema?
5. Mencione una situación donde cuantizar a 4 bits sería una mala decisión.
