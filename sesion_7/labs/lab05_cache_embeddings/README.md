# Lab 5 · Cache de embeddings y batching

**Duración:** 25 min · **Prerrequisito:** Lab 1 (`nomic-embed-text` descargado).

## Idea
Un embedding es siempre el mismo para el mismo (modelo, texto). Tres formas de obtener los de un corpus con repeticiones:

| Estrategia | Descripción |
|---|---|
| **A · Ingenua** | Una llamada HTTP por texto |
| **B · Por lotes** | Una sola llamada con todos los textos |
| **C · Cache + lote** | Consulta la cache; envía en un lote **solo** los textos nuevos y sin duplicados |

## Ejecución
```bash
python labs/lab05_cache_embeddings/embedding_cache_bench.py --model nomic-embed-text --size 200 --repeat-ratio 0.5 --rounds 3
```
Pruebe `--repeat-ratio 0.1` y `0.9`.

## Qué observar
- **A → B:** el lote elimina la sobrecarga fija de cada llamada (ida y vuelta HTTP, planificación).
- **C en la ronda 1:** ya ahorra por **de-duplicación**; en las rondas 2 y 3 el tiempo cae casi a cero (todo está en cache).
- ¿Cómo cambia la mejora cuando casi no hay repeticiones? ¿Sigue valiendo la pena la cache? (considere memoria y complejidad)

## La misma cache en la API
El backend usa exactamente la misma clase (`app/backend/app/services/cache.py`). Con la API levantada:
```bash
curl -s localhost:8000/api/embeddings -H 'Content-Type: application/json' -d '{"texts":["hola","hola","adiós"]}' | head -c 300
curl -s localhost:8000/api/embeddings/cache/stats
```

## Preguntas de reflexión
1. ¿Qué pasa con la cache si **cambia el modelo de embeddings**? (La clave incluye el modelo: ¿por qué es imprescindible?)
2. En una universidad con varios usuarios, ¿qué riesgo de privacidad tiene una cache **compartida**? ¿Cómo lo mitigaría?
3. ¿Cuándo expiraría (TTL) las entradas? ¿Y cuándo las invalidaría?
