# Lab 4 · Cuantización: memoria, velocidad y calidad

**Duración:** 35 min · **Prerrequisito:** Lab 1 · **Espacio en disco:** ≈ 3 GB para las variantes del modelo de 1B.

## Idea
La misma red neuronal puede guardarse con distinta precisión. Menos bits ⇒ menos memoria y normalmente más rápido, a cambio de cierta pérdida de calidad.

## 4a · Teoría numérica (sin modelo)
```bash
python labs/lab04_quantizacion/quant_estimator.py --params-b 8.03
```

## 4b · Comparación empírica
```bash
ollama pull llama3.2:1b-instruct-q4_K_M
ollama pull llama3.2:1b-instruct-q8_0
python labs/lab04_quantizacion/quant_compare.py \
  --models llama3.2:1b-instruct-q4_K_M,llama3.2:1b-instruct-q8_0 --runs 3
```
> Verifique que las etiquetas existan en <https://ollama.com/library/llama3.2/tags>. Si alguna no existe, elija otras dos cuantizaciones del mismo modelo.

Mide por variante: **memoria cargada**, **tiempo de carga**, **TTFT**, **tokens/s** y una **sonda de calidad** de 8 preguntas.

## ⚠ Cómo interpretar (y cómo NO)
- La sonda de calidad tiene **8 preguntas**: es un detector de desastres, no un benchmark. Una diferencia de 1/8 no es significativa.
- Para decisiones reales se usan evaluaciones en **su** tarea o suites estándar (p. ej. `lm-evaluation-harness`).
- La velocidad depende de su hardware: no compare sus números con los de un compañero con otra máquina.

## Preguntas de reflexión
1. ¿Por qué Q4 suele ser más rápido que Q8 en el decode? (pista: ancho de banda de memoria)
2. ¿Qué tipo de tarea degradaría primero con cuantización agresiva (matemáticas, código, idiomas minoritarios…)? ¿Cómo lo comprobaría?
3. Si cuantizar libera 6 GB de VRAM, ¿en qué otra cosa podría gastar esa memoria? (pista: KV cache)

## Limpieza
```bash
ollama rm llama3.2:1b-instruct-q4_K_M llama3.2:1b-instruct-q8_0
```
