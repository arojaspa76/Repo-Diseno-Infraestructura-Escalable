# Laboratorio 6 · Prueba de carga y SLO (E6)

**Estado:** la lógica del generador está validada (4 pruebas con servidor simulado). **No se midió contra Ollama real.**

## 1. Objetivo
Medir TTFT, latencia p95 y disponibilidad con N usuarios concurrentes y compararlas con un SLO.

## 2–5. Requisitos
Laboratorio 2 funcionando. **Importante:** el límite por defecto (30 solicitudes/min) y el presupuesto bloquearán la prueba. Antes de ejecutarla suba `RATE_LIMIT_PER_MINUTE=1000` y el presupuesto en `.env` y reinicie el gateway.

## 6–8. Procedimiento
```bash
cd loadtest
python loadgen.py --url http://localhost:8000 --users 4 --requests 20 --max-tokens 64 \
   --slo-p95-s 10 --slo-ttft-s 3 --slo-availability 0.99 --out resultados/run1.json
```
Repita con `--users 1, 2, 4, 8` y anote cómo cambia la latencia.

## 9. Resultado esperado
Tabla de p50/p95, TTFT, solicitudes por segundo y veredicto contra cada SLO. Los valores dependerán de su hardware: **no existen cifras de referencia** en este material.

## 10. Validación
`make test-loadtest`.

## 11. Métricas
TTFT, p50/p95, tokens/s agregados, disponibilidad.

## 12. Seguridad
Ejecute la carga solo contra sistemas propios o autorizados.

## 13. Costos
Cero con Ollama. **Contra una API de pago, esta prueba consume dinero:** calcule antes `usuarios × solicitudes × costo por solicitud`.

## 14. Problemas
Muchos 429 → rate limit o presupuesto. Muchos timeouts → modelo demasiado grande para su equipo.

## 15. Limpieza
Borre `resultados/`.

## 16. Reflexión
¿En qué punto de concurrencia deja de cumplirse el SLO? ¿Cuántas réplicas necesitaría para 100 usuarios simultáneos y cuánto costarían (conecte con el laboratorio 3)?
