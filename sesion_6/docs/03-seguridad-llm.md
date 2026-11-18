# Seguridad de LLM: OWASP LLM Top 10 2026 → controles de este repositorio

**Fuente y versión:** OWASP GenAI Security Project, *Top 10 for LLM Applications 2026 (v1.0)*, publicada en agosto de 2026 (reemplaza la edición 2025; la página antigua del proyecto en owasp.org puede seguir mostrando la 2025). Para sistemas donde el modelo actúa con herramientas, memoria y permisos, OWASP indica usar **además** el *Top 10 for Agentic Applications 2026*. Verifique la versión vigente antes de clase.

> Las heurísticas del gateway son una **primera barrera**. Ninguna lista de patrones detiene la inyección de prompt; por eso el diseño combina capas y limita el daño posible (mínimo privilegio).

| ID 2026 | Riesgo | Qué significa (resumen propio) | Control en el repositorio | Alcance / límites |
|---|---|---|---|---|
| LLM01 | Prompt Injection | La entrada (directa o dentro de documentos) cambia el comportamiento del modelo | `scan_prompt_injection` (patrones ES/EN, umbral configurable); el cliente no puede enviar mensajes `system`; el prompt de sistema lo pone el servidor | Cubre ataques directos obvios. **No** cubre inyección indirecta ni ofuscación |
| LLM02 | Sensitive Information Disclosure | El sistema expone datos que no debía | `redact_pii` (correo, teléfono, tarjetas con Luhn) antes de enviar al modelo; `LOG_PROMPTS=false` por defecto | Redacción por patrones: puede omitir PII no estándar |
| LLM03 | Excessive Agency | Demasiadas funciones/permisos/autonomía permiten acciones reales por salidas manipuladas | Agentes con **solo dos herramientas de cálculo**, sin red ni datos; ver `cloud-agents/` | En agentes con herramientas reales: permisos mínimos y aprobación humana |
| LLM04 | Supply Chain | Modelos, datasets, adaptadores y frameworks de terceros | Versiones acotadas en `requirements.txt`; aviso de frameworks legados (AutoGen, SK); modelos de Ollama solo de fuentes conocidas | Falta inventario firmado y verificación de digest (recomendado) |
| LLM05 | Data and Model Poisoning | Datos de entrenamiento/ajuste/recuperación contaminados | Fuera de alcance de esta sesión (aplica a RAG y fine-tuning) | — |
| LLM06 | Unbounded Consumption | Cómputo costoso a bajo costo para el atacante («Denial of Wallet») | Límite de entrada (413), `max_output_tokens`, rate limit por cliente, **presupuesto por cliente con bloqueo (429)**, autenticación por API key | Estado en memoria; para varias réplicas requiere almacén compartido |
| LLM07 | Misinformation | Salida errónea pero creíble usada para decidir | Las herramientas de agentes calculan de forma determinista en vez de «de memoria» | Requiere evaluación de calidad y verificación de fuentes |
| LLM08 | Hidden Context Exposure | El contexto oculto (prompt de sistema, esquemas) puede descubrirse | Diseño: no poner secretos en el prompt de sistema; autorización fuera del modelo | Asuma que el prompt de sistema es descubrible |
| LLM09 | Vector and Embedding Weaknesses | Fallas en RAG/memoria vectorial, fuga entre inquilinos | Fuera de alcance (sin índice vectorial en esta sesión) | Ver sesiones de RAG |
| LLM10 | Improper Output Handling | La salida llega sin validar a otros componentes | `sanitize_output` y el front React renderiza texto (no HTML) | Trate toda salida como entrada no confiable |

## Otras capas (no son «de OWASP», son de ingeniería)
- **Identidad:** Entra ID / IAM / ADC en vez de claves en código.
- **Redes y datos:** puntos de enlace privados, cifrado en tránsito y reposo (responsabilidad compartida: el proveedor protege la infraestructura; usted configura identidad, datos y uso).
- **Observabilidad segura:** registre metadatos (tokens, latencia, cliente con *hash*), no contenido.
- **Gobierno:** inventario de modelos y casos de uso, evaluación de riesgos; marcos de referencia aplicables: NIST AI RMF, ISO/IEC 42001 (citar la versión vigente en su organización).

## Preguntas de discusión
1. ¿Qué daño máximo podría causar una inyección exitosa contra el agente de `cloud-agents/` y por qué es acotado?
2. ¿Qué cambia si se le añade una herramienta que envía correos?
3. ¿Por qué el presupuesto con bloqueo es un control de seguridad y no solo de finanzas?
