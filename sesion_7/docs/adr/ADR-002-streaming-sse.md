# ADR-002 — Server-Sent Events (SSE) para el streaming de tokens

- **Estado:** Aceptada

## Contexto
La latencia *percibida* mejora si el usuario ve tokens a medida que se generan. Se necesita un canal servidor→cliente unidireccional.

## Alternativas
| Opción | Ventajas | Desventajas |
|---|---|---|
| **SSE** | Simple, sobre HTTP, reconexión nativa, atraviesa proxies si se desactiva el buffering | Solo servidor→cliente; el navegador solo permite `EventSource` con GET |
| WebSockets | Bidireccional, baja sobrecarga | Más complejo de operar (balanceadores, autenticación, escalado) |
| Respuesta completa (sin streaming) | Trivial | Mala latencia percibida: el usuario espera todo el TPOT×N |

## Decisión
SSE sobre `POST /api/chat/stream`; en el cliente se usa `fetch` + `ReadableStream` (porque `EventSource` no admite POST).

## Consecuencias
- nginx/proxies deben desactivar el *buffering* (`proxy_buffering off`), ya incluido en `app/frontend/nginx.conf`.
- Un balanceador con *timeouts* cortos puede cortar respuestas largas: configurar `idle timeout` acorde.
