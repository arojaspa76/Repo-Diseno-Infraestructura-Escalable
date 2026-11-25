# ADR-003 — Guardrails propios como primera capa de defensa (no la única)

- **Estado:** Aceptada

## Contexto
Las aplicaciones LLM enfrentan riesgos como inyección de prompts, fuga de datos sensibles y manejo inseguro de salidas (OWASP Top 10 for LLM Applications).

## Decisión
Implementar en el backend, como material **didáctico**:
1. Prompt de sistema controlado por el servidor (el cliente no puede enviarlo).
2. Detección heurística de inyección (reglas ponderadas; bloqueo por umbral).
3. Redacción de PII y secretos *antes* de enviar al modelo.
4. Sanitización de la *salida* (imágenes externas, etiquetas HTML peligrosas) y render como texto plano en el frontend.
5. API key (comparación de tiempo constante), rate limiting y límites de tamaño.
6. Logs sin contenido de prompts.

## Limitaciones reconocidas
Las heurísticas son evadibles (paráfrasis, otros idiomas, codificaciones). **No** reemplazan: mínimo privilegio en herramientas, aislamiento de red,
revisión humana de acciones críticas ni servicios administrados (Azure AI Content Safety/Prompt Shields, Bedrock Guardrails, Model Armor).

## Consecuencias
- (+) Los estudiantes ven el concepto funcionando y pueden atacarlo (ejercicio de la guía).
- (−) En producción se complementa con servicios administrados y *red teaming* continuo.
