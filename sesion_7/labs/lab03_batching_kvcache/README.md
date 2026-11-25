# Lab 3 · Batching y KV cache

**Duración:** 45 min · **Prerrequisitos:** Lab 1 (con `OLLAMA_NUM_PARALLEL` ≥ 4 para 3a).

Cuatro experimentos cortos que muestran las ideas centrales de la sesión.

| Script | Qué demuestra | ¿Necesita modelo? |
|---|---|---|
| `bench_concurrency.py` (3a) | Más concurrencia ⇒ más throughput total, pero más latencia por usuario | Sí |
| `kv_cache_calculator.py` (3b) | Cuánta memoria consume el KV cache y cuántas conversaciones caben en su GPU | No |
| `prefix_cache_experiment.py` (3c) | Reutilizar un prefijo largo reduce el prefill | Sí |
| `batching_simulator.py` (3d) | Batching estático vs continuo (simulación) | No |

## 3a · Concurrencia vs throughput
```bash
python labs/lab03_batching_kvcache/bench_concurrency.py --model llama3.2:1b --levels 1,2,4,8 --requests-per-level 8
```
**Qué observar:** la columna *tok/s agregados* debería crecer con la concurrencia (con rendimientos decrecientes), mientras *TTFT p95* y *total p95* también crecen.
Ese es el **compromiso latencia ↔ throughput**. Si `OLLAMA_NUM_PARALLEL=1`, verá que casi no hay mejora: las peticiones se encolan.

## 3b · Calculadora de KV cache
```bash
python labs/lab03_batching_kvcache/kv_cache_calculator.py --preset llama-3.1-8b --quant q4_k_m --gpu-gb 16
python labs/lab03_batching_kvcache/kv_cache_calculator.py --preset llama-3.1-70b --quant q4_k_m --gpu-gb 80
```
**Ejercicio:** ¿cuántas conversaciones de 8 192 tokens caben en una GPU de 24 GB con Llama 3.1 8B en FP16? ¿Y en Q8_0? (Compare con `cloud_agents/shared/capacity_tools.py`: es la misma fórmula.)

## 3c · Reuso de prefijo
```bash
python labs/lab03_batching_kvcache/prefix_cache_experiment.py --model llama3.2:1b --prefix-tokens 800
```
Compara 6 peticiones con el **mismo** prefijo largo contra 6 con prefijos **distintos**.
**Tendencia esperada:** en el caso A el *prefill* baja tras la primera petición. Es una tendencia, no una garantía: **reporte lo que mida**, aunque contradiga la teoría, y propóngase una explicación.

## 3d · Simulador de batching
```bash
python labs/lab03_batching_kvcache/batching_simulator.py --requests 64 --batch 8
```
Con la semilla por defecto, el continuo usa ≈ 90 % de los slots frente a ≈ 56 % del estático (simulación, no medición real).

## Entregable
Una tabla con sus resultados de 3a y un párrafo (máx. 150 palabras) explicando **en qué punto de concurrencia operaría usted** si el SLO fuera *TTFT p95 ≤ 1 s* y por qué.

## Solución de problemas
| Problema | Solución |
|---|---|
| Sin mejora al subir concurrencia | `OLLAMA_NUM_PARALLEL=1`; ejecute `configure_parallel.sh` (Lab 1) |
| Se agota la RAM | Reduzca `--levels` o use un modelo más pequeño |
| Resultados muy variables | Cierre otras aplicaciones; repita 3 veces y reporte la mediana |
