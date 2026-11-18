# Laboratorio 4 · Rightsizing y punto de equilibrio (E2)

**Estado:** validado con el simulador (precios ilustrativos).

## 1. Objetivo
(a) Elegir el tamaño de instancia con el **percentil 95** de utilización, no el promedio. (b) Hallar a cuántas solicitudes por mes conviene autogestionar frente a una API.

## 2–5. Arquitectura y entorno
Igual que el laboratorio 3. Datos: `finops/data/utilizacion_ejemplo.csv` (336 muestras, 2 semanas por hora).

## 6–8. Procedimiento
```bash
cd finops
python -m finops_sim rightsize --instance gpu-m --csv data/utilizacion_ejemplo.csv
python -m finops_sim breakeven --instance gpu-s
python -m finops_sim breakeven --instance gpu-s --util 0.8
python -m finops_sim capacity --instance gpu-s --users 100 --out-tokens 300 --think 30
```

## 9. Resultado esperado
`rightsize`: p50 = 12.1 %, p95 = 25.1 %; recomienda pasar de gpu-m ($1,168) a gpu-s ($730): ahorro $438/mes. `breakeven`: punto de equilibrio 730,000 solicitudes/mes; costo autogestionado a 40 % de utilización $15.43 por millón de tokens de salida frente a $4.00 de la API.

## 10. Validación
Repita `breakeven` con `--util 0.8`: el costo unitario autogestionado cae. Anote cuánto y explique por qué (la utilización es el motor del costo unitario).

## 11. Métricas
p50/p95, USD/mes, USD por millón de tokens, solicitudes de equilibrio.

## 12. Seguridad
Los CSV reales de utilización pueden revelar patrones de uso; trátelos como datos internos.

## 13. Costos
Ninguno.

## 14. Problemas
CSV con otras columnas: debe tener `hora,utilizacion_pct`.

## 15. Limpieza
No aplica.

## 16. Reflexión
El promedio fue 12 %, el p95 25 %: ¿por qué aun así no se recomienda bajar a un tamaño más pequeño que gpu-s? (pista: SLO, N+1 y arranque en frío). ¿Qué dato adicional necesita antes de aplicar la recomendación?
