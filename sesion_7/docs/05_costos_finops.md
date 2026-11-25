# Costos y FinOps para inferencia de LLMs

> ⚠ **Todos los precios de este documento son HIPOTÉTICOS** y existen solo para ilustrar el método de cálculo. Use las calculadoras oficiales de cada nube
> con precios vigentes de su región antes de decidir.

## 1. Dos modelos de costo

| Modelo | Unidad de cobro | Ejemplo | Riesgo principal |
|---|---|---|---|
| **Por token** (API administrada) | USD por millón de tokens de entrada/salida | Foundry, Gemini, Bedrock | Costo impredecible si crece el uso o hay abuso (*unbounded consumption*) |
| **Por capacidad** (GPU propia/alquilada) | USD por hora de GPU | vLLM en AKS/GKE/EKS | Pagar la GPU aunque esté ociosa |

## 2. Costo por millón de tokens en autogestionado

```
USD / 1M tokens = (USD por hora de GPU) / (tokens/s agregados × 3600 × utilización) × 1 000 000
```

**Ejemplo con números hipotéticos:** GPU a 2 USD/h, 1 500 tok/s agregados medidos con batching, utilización media del 40 %:
`2 / (1500 × 3600 × 0.40) × 1e6 ≈ 0.93 USD por millón de tokens`.
Con utilización del 10 % el mismo servidor cuesta ≈ 3.7 USD/M. **La utilización manda.**

Calcule su propio punto de equilibrio: `python labs/lab06_analisis_comparativo/finops_breakeven.py --help`.

## 3. Palancas de optimización (y su efecto)

| Palanca | Efecto en costo | Efecto en latencia/calidad |
|---|---|---|
| Cuantización | Menos GPU/VRAM por modelo | Mejora decode; riesgo de pérdida de calidad |
| Batching continuo | Más tokens por segundo por GPU | Sube latencia por usuario si se exagera |
| Cache (embeddings, prefijos) | Evita cómputo repetido | Mejora; cuidado con privacidad |
| Modelo más pequeño / enrutamiento | Grandes ahorros | Posible pérdida de calidad en casos difíciles |
| Límites de tokens y cuotas | Acota el peor caso | Respuestas truncadas |
| Autoscaling con mínimo cero (serverless) | No paga ociosidad | Cold start (carga del modelo: segundos a minutos) |
| Instancias reservadas / *spot* | Descuentos por compromiso o interrupciones | *Spot* exige tolerancia a fallos |

## 4. Etiquetado y gobierno de costos

- Etiquete recursos (`env`, `owner`, `course`, `cost-center`) desde el día uno.
- Configure **presupuestos y alertas** en la nube antes de desplegar (Azure Cost Management, Google Cloud Billing budgets, AWS Budgets).
- Registre **tokens por usuario/proyecto** (el backend de este repositorio expone contadores en `/metrics`).

## 5. Advertencia de costos para los laboratorios de nube

| Laboratorio | Qué puede generar cobro | Cómo evitarlo |
|---|---|---|
| Agentes administrados (Foundry Agent Service, Agent Engine, AgentCore) | Tokens del modelo, runtime, registro de contenedores | Pruebe con pocas peticiones y **ejecute la limpieza** |
| Despliegues con GPU | Hora de GPU aunque no haya tráfico | Apáguelos al terminar; use alertas de presupuesto |
| Cuentas *trial* | Créditos limitados | No actualice a pago por uso; elimine el proyecto/grupo de recursos al final |
