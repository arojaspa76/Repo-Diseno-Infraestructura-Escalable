# Aplicación de la sesión: backend FastAPI + frontend React

## ¿Qué es?
Una aplicación pequeña pero completa para **ver y medir** los conceptos de la sesión: un chat con streaming que muestra TTFT y TPOT en cada respuesta,
un panel de métricas del servidor, una calculadora de memoria de GPU y un laboratorio de guardrails de seguridad.

```
app/
├── backend/     API en Python (FastAPI)  → habla con Ollama
├── frontend/    Interfaz web (React 18 + Vite 6)
├── docker-compose.yml        Ollama + backend + frontend con un comando
└── docker-compose.gpu.yml    Extensión para GPU NVIDIA
```

## Cómo ejecutarla

### Opción 1 — Desarrollo (recomendada para aprender)
Necesita Ollama funcionando (Lab 1) y haber instalado dependencias (`docs/00_guia_instalacion_ubuntu.md`).
```bash
# Terminal 1 — backend (http://localhost:8000, documentación interactiva en /docs)
make backend

# Terminal 2 — frontend (http://localhost:5173)
make frontend
```

### Opción 2 — Todo en contenedores
```bash
cd app
docker compose up --build            # solo CPU
# con GPU NVIDIA:
# docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build

# en otra terminal, la primera vez:
docker compose exec ollama ollama pull llama3.2:1b
docker compose exec ollama ollama pull nomic-embed-text
```
Abra <http://localhost:8080>.

## Qué hace cada pestaña
| Pestaña | Qué verá | Concepto |
|---|---|---|
| 1 · Chat con streaming | Respuesta token a token + tarjetas TTFT, TPOT, decode, total, prefill, carga | Latencia percibida vs real |
| 2 · Métricas del servidor | p50/p95/p99 y estadísticas de la cache | Percentiles y SLOs |
| 3 · Calculadora de memoria | Barra de pesos + KV cache + overhead frente a la GPU | KV cache y capacidad |
| 4 · Guardrails | Detección de inyección y redacción de PII | Seguridad por capas |

## La API en una tabla
| Método y ruta | Para qué |
|---|---|
| `GET /health` · `GET /ready` | Vivo / listo (use *ready* como probe de Kubernetes) |
| `POST /api/chat` | Respuesta completa + métricas |
| `POST /api/chat/stream` | Respuesta en streaming (SSE) |
| `POST /api/embeddings` | Embeddings con cache y batching |
| `GET /api/embeddings/cache/stats` | Aciertos/fallos de la cache |
| `POST /api/security/inspect` | Ver qué detectaría el guardrail |
| `POST /api/capacity/estimate` | Memoria de pesos + KV cache |
| `GET /api/metrics/summary` · `GET /metrics` | Métricas (JSON / Prometheus) |

Ejemplo:
```bash
curl -s localhost:8000/api/chat -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Explica el KV cache en dos frases"}],"max_tokens":80}'
```

## Configuración
Todo se controla con variables `S07_*` (ver `backend/.env.example`). Las más importantes:

| Variable | Qué hace | Por defecto |
|---|---|---|
| `S07_OLLAMA_BASE_URL` | Dónde está Ollama | `http://localhost:11434` |
| `S07_DEFAULT_MODEL` | Modelo de chat | `llama3.2:1b` |
| `S07_API_KEY` | Si se define, exige `X-API-Key` | (vacía = sin auth, solo laboratorio) |
| `S07_RATE_LIMIT_PER_MINUTE` | Límite por clave/IP | `60` |
| `S07_GUARD_MODE` | `block`, `flag` u `off` | `block` |

## Pruebas
```bash
make test            # 21 pruebas del backend (no necesitan Ollama: usan un backend falso)
cd app/frontend && npm run build     # tsc + vite build
```
Qué cubren las pruebas: streaming SSE, métricas, bloqueo de inyección, redacción de PII, auth por API key, rate limit, cache y batching de embeddings, calculadora de memoria.
**Qué NO cubren** (pendiente): pruebas contra un Ollama real y pruebas end-to-end del frontend en un navegador.

## Seguridad en esta aplicación
Ver `docs/04_seguridad_llm.md`. Resumen: el prompt de sistema lo controla el servidor; se redacta PII antes de llegar al modelo; la salida se sanitiza y el frontend la
muestra como texto plano; hay API key opcional, rate limit y límites de tamaño; **los logs no guardan el contenido de los prompts**.
**Antes de exponerla fuera de su laptop:** active `S07_API_KEY`, ponga TLS delante y no publique el puerto de Ollama.

## Solución de problemas
| Síntoma | Causa probable | Solución |
|---|---|---|
| El chat dice "No se pudo contactar a Ollama" | Ollama no corre o URL incorrecta | `curl localhost:11434/api/version`; revise `S07_OLLAMA_BASE_URL` |
| `502` al listar modelos | Igual que arriba | Igual |
| `422 guardrail` | La entrada activó el guardrail | Es lo esperado en la pestaña 4; pruebe con `S07_GUARD_MODE=flag` |
| `429` | Rate limit | Espere o aumente `S07_RATE_LIMIT_PER_MINUTE` |
| El streaming llega "de golpe" detrás de un proxy | Buffering del proxy | `proxy_buffering off` (ya en `frontend/nginx.conf`) |
| Docker: `ollama` no arranca con GPU | Falta NVIDIA Container Toolkit | Instálelo o use solo CPU |

## Limpieza
```bash
cd app && docker compose down -v          # detiene y borra volúmenes (incluye modelos descargados)
```
