# Lab 2 · Profiling: ¿dónde se va el tiempo y los recursos?

**Duración:** 25 min · **Prerrequisito:** Lab 1.

## ¿Qué aprenderá?
Medir —y no adivinar— cuánto tardan la **red**, la **carga del modelo**, el **prefill** y el **decode**, y cuánta **CPU/RAM/GPU** consume una inferencia.

## Qué hace el script
`profile_system.py`:
1. Mide la latencia de **red** al servidor (conexión TCP y petición HTTP mínima).
2. Con `--cold`, descarga el modelo para forzar un **arranque en frío**.
3. Lanza una inferencia mientras un hilo **muestrea** CPU, RAM, GPU (si hay NVIDIA) y tráfico de red cada 0.25 s.
4. Consulta a Ollama qué porcentaje del modelo quedó en GPU.
5. Guarda todo en `results/profiling_<fecha>.json`.

## Ejecución
```bash
source .venv/bin/activate
python labs/lab02_profiling/profile_system.py --model llama3.2:1b --cold          # arranque en frío
python labs/lab02_profiling/profile_system.py --model llama3.2:1b                 # modelo ya caliente
python labs/lab02_profiling/profile_system.py --prompt-tokens 1500 --num-predict 32   # prompt largo, salida corta (¡prefill!)
python labs/lab02_profiling/profile_system.py --prompt-tokens 20 --num-predict 300     # prompt corto, salida larga (¡decode!)
```

## Cómo leer el resultado
| Línea | Significado | Si es alto… |
|---|---|---|
| `carga del modelo` | Tiempo de cargar pesos a memoria | Estaba en frío: use `keep_alive` o precalentamiento |
| `prefill (prompt_eval)` | Procesar el prompt | Prompt largo; considere reuso de prefijo (Lab 3c) |
| `TPOT` / `decode tok/s` | Fluidez de generación | Modelo grande para su hardware, o parte del modelo en CPU |
| `CPU pico` | ¿La CPU es el cuello de botella? | Si la GPU está ociosa y la CPU al 100 %, el modelo corre en CPU |
| `GPU util / VRAM` | Uso de GPU | VRAM llena ⇒ el modelo se derrama a RAM (muy lento) |
| `% del modelo en GPU` | Reparto GPU/RAM | < 100 % ⇒ rendimiento degradado |

## Experimento guiado
Complete la tabla con **sus** mediciones (no con valores de otros):

| Caso | Prompt (tokens) | Salida (tokens) | TTFT | TPOT | ¿Qué fase domina? |
|---|---:|---:|---|---|---|
| Frío | 400 | 128 | | | |
| Caliente | 400 | 128 | | | |
| Prompt largo | 1500 | 32 | | | |
| Salida larga | 20 | 300 | | | |

## Preguntas de reflexión
1. ¿Qué cambió entre *frío* y *caliente*? ¿Qué decisión de arquitectura en la nube evita el arranque en frío (y cuánto cuesta)?
2. ¿Por qué `prompt largo / salida corta` y `prompt corto / salida larga` estresan recursos distintos?
3. Si la red agrega 40 ms al TTFT, ¿es relevante frente a un prefill de 800 ms? ¿Y si el prefill fuera 30 ms?

## Solución de problemas
- `GPU: no se detectó nvidia-smi`: normal en CPU/AMD/Apple Silicon; el resto de métricas sigue funcionando.
- Muestras de CPU en 0 %: el modelo corre en GPU o la inferencia fue muy corta; aumente `--num-predict`.
