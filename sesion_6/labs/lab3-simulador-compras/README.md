# Laboratorio 3 · Simulador de modalidades de compra (E1)

**Estado:** 15 pruebas del simulador pasan. **Los precios del catálogo son ilustrativos.**

## 1. Objetivo
Comparar on-demand, compromiso (1 o 3 años) y spot para una flota con base constante y picos, y detectar el error de «comprometer el pico».

## 2. Arquitectura
Herramienta de consola, sin servicios: `finops/finops_sim` lee `finops/data/catalogo_ilustrativo.json`.

## 3–5. Requisitos y entorno
`make setup` (solo Python 3.12).

## 6–8. Procedimiento
```bash
cd finops
python -m finops_sim catalog
python -m finops_sim strategies --instance gpu-s --baseline 2 --peak-extra 2 --peak-hours 120
python -m finops_sim scenario --instance gpu-s            # caso universitario completo
```
Cambie `--commitment 3y`, `--peak-hours` y la instancia. Para usar **sus** precios copie el JSON y pase `--catalog su_catalogo.json`.

## 9. Resultado esperado (con el catálogo ilustrativo incluido)
Para `strategies … --baseline 2 --peak-extra 2 --peak-hours 120`: `all_on_demand` $1,700 · `commit_baseline` $1,262 (−25.8 %) · `commit_spot` $1,114 (−34.4 %) · `all_commit_peak` $2,044 (+20.2 %): comprometer el pico sale **más caro** que no comprometer nada.

## 10. Validación
`make test-finops`.

## 11. Métricas
USD/mes por estrategia y % frente a on-demand.

## 12. Seguridad
No hay credenciales. Si usa precios reales de su organización, no los suba a un repositorio público.

## 13. Costos
Ninguno.

## 14. Problemas
`KeyError` de instancia → ejecute `catalog` y use uno de los nombres listados.

## 15. Limpieza
No aplica.

## 16. Reflexión
¿A partir de cuántas horas de pico al mes cambia la estrategia ganadora? ¿Qué riesgo operativo introduce usar spot para el servicio de 99,9 %?
