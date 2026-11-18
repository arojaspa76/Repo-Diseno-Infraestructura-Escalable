# Laboratorio 5 · Presupuesto, alertas y límite duro (E3)

**Estado:** lógica validada por pruebas (`backend/tests/test_finops.py`, `test_api.py`).

## 1. Objetivo
Entender la diferencia entre **alertar** (las nubes) y **detener** (su gateway): los presupuestos de Azure Cost Management o AWS Budgets notifican con retraso; el límite que realmente frena el gasto debe estar en su código.

## 2. Arquitectura
`BudgetTracker` (libro diario por cliente) → niveles 50/80/100 % → bloqueo (HTTP 429) al llegar a 100 %.

## 3–5. Requisitos
Laboratorio 2 funcionando. En `.env`: `DAILY_BUDGET_USD_PER_CLIENT=0.01`, `GATEWAY_API_KEYS=clave-demo`.

## 6–8. Procedimiento
```bash
for i in $(seq 1 30); do
  curl -s -o /dev/null -w "%{http_code} " localhost:8000/v1/chat -H 'X-API-Key: clave-demo' \
   -H 'Content-Type: application/json' -d '{"messages":[{"role":"user","content":"Cuéntame algo largo sobre FinOps"}]}'
done; echo
curl -s localhost:8000/v1/budget -H 'X-API-Key: clave-demo'
```
(La cabecera de clave es `X-API-Key`.)

## 9. Resultado esperado
Respuestas 200 al inicio, y 429 cuando el gasto acumulado del cliente alcanza el tope; `/v1/budget` muestra gasto, límite y alertas disparadas (cada nivel se dispara **una sola vez**).

## 10. Validación
`make test-backend`.

## 11. Métricas
Gasto acumulado, alertas disparadas, solicitudes bloqueadas.

## 12. Seguridad
Es la defensa contra *Denial of Wallet* (OWASP LLM06:2026 Unbounded Consumption). Un tope por cliente evita que una clave filtrada agote todo el presupuesto.

## 13. Costos
Ninguno (usa el modelo local).

## 14. Problemas
Si siempre ve 200: el costo sombra de pocas solicitudes es muy bajo; reduzca el presupuesto o suba `MAX_OUTPUT_TOKENS`.

## 15. Limpieza
El libro es en memoria: reinicie el gateway.

## 16. Reflexión
El libro está en memoria y se pierde al reiniciar. ¿Qué cambiaría para varias réplicas del gateway? (pista: estado compartido, Redis/base de datos, consistencia).
