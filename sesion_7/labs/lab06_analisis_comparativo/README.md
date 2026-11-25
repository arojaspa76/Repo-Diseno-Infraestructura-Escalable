# Lab 6 · Análisis comparativo de rendimiento

**Duración:** 30 min · **Prerrequisito:** haber ejecutado al menos los Labs 2 y 3.

## Qué hace
- `compare_results.py` lee los JSON de `results/` y genera `results/REPORTE.md` con tablas y gráficas listas para su informe.
- `finops_breakeven.py` calcula el costo por millón de tokens de una GPU propia según su utilización y lo compara con el precio de una API.

## Ejecución
```bash
python labs/lab06_analisis_comparativo/compare_results.py
python labs/lab06_analisis_comparativo/finops_breakeven.py --gpu-usd-h 2 --tok-s <SU_RESULTADO_DEL_LAB3> --api-usd-per-m 0.60
```
> Los precios por defecto son **hipotéticos**. Tome los reales de las calculadoras oficiales.

## Entregable: informe comparativo (máx. 2 páginas)
Use `report_template.md`. Debe incluir:
1. Su entorno (CPU/GPU/RAM, versión de Ollama, modelo).
2. Tabla de concurrencia (Lab 3a) y la gráfica generada.
3. Comparación de cuantizaciones (Lab 4b) con la **salvedad** sobre la sonda de calidad.
4. Una **recomendación de arquitectura** (modelo, cuantización, concurrencia por réplica) para el caso universitario (100 usuarios concurrentes, TTFT p95 ≤ 1 s) **justificada con sus datos**.
5. Una sección *Limitaciones*: qué NO puede concluir con sus mediciones.

## Criterios de evaluación (sugeridos)
| Criterio | Peso |
|---|---:|
| Rigor de la medición (repeticiones, entorno documentado) | 30 % |
| Interpretación correcta de TTFT/TPOT/throughput | 25 % |
| Justificación de la recomendación | 25 % |
| Honestidad sobre limitaciones | 20 % |
