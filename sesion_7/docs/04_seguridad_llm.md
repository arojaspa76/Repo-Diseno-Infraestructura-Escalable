# Seguridad de aplicaciones LLM

## 1. Qué es distinto en un LLM

En software tradicional, el código y los datos están separados. En un LLM, **las instrucciones y los datos viajan juntos en el mismo texto**.
Por eso un documento, una página web o un mensaje de usuario pueden contener texto que el modelo interprete como una *orden*. Esa es la raíz de la
*inyección de prompts* y obliga a diseñar con **defensa en capas**.

## 2. OWASP Top 10 for LLM Applications

**Edición vigente leída en la página oficial (genai.owasp.org) el 24-nov-2026: "2026 Top 10 Critical Security Risks for LLM Applications".**
La edición anterior (2025) sigue siendo la más citada en bibliografía y proveedores, por eso se muestran ambas.

| # | Edición 2026 | Edición 2025 |
|---|---|---|
| 01 | Prompt Injection | Prompt Injection |
| 02 | Sensitive Information Disclosure | Sensitive Information Disclosure |
| 03 | Excessive Agency | Supply Chain |
| 04 | Supply Chain | Data and Model Poisoning |
| 05 | Data and Model Poisoning | Improper Output Handling |
| 06 | Unbounded Consumption | Excessive Agency |
| 07 | Misinformation | System Prompt Leakage |
| 08 | Hidden Context Exposure | Vector and Embedding Weaknesses |
| 09 | Vector and Embedding Weaknesses | Misinformation |
| 10 | Improper Output Handling | Unbounded Consumption |

> *Nota de verificación:* la lista 2026 se obtuvo de la página oficial; no se revisó el detalle de cada categoría. "Hidden Context Exposure" parece ocupar el lugar
> conceptual de "System Prompt Leakage" — confírmelo en la descripción oficial antes de afirmarlo en clase.
> Además, OWASP publica un **Top 10 for Agentic Applications** (diciembre de 2025) específico para agentes autónomos.

## 3. Controles implementados en este repositorio

| Riesgo (OWASP) | Control implementado | Dónde | Limitación honesta |
|---|---|---|---|
| Prompt Injection | Prompt de sistema solo del servidor; reglas ponderadas es/en; bloqueo por umbral | `app/backend/app/services/security.py`, `inference.py` | Evadible por paráfrasis, otros idiomas o codificación; no cubre inyección **indirecta** (documentos recuperados) |
| Sensitive Information Disclosure | Redacción de PII/secretos *antes* de enviar al modelo; logs sin contenido | `security.redact_pii`, `main.py` | Regex ≠ detección completa; use servicios dedicados (DLP) |
| Improper Output Handling | Sanitización de salida (imágenes externas, HTML) y render como texto plano en React | `security.sanitize_output`, `ChatPanel.tsx` | En *streaming* la sanitización del servidor es parcial; por eso el frontend nunca inserta HTML |
| Unbounded Consumption | Límite de tamaño de entrada, tope de tokens de salida, rate limit por clave/IP | `config.py`, `security.py` | Rate limit en memoria: con varias réplicas necesita Redis/API Gateway |
| Excessive Agency | Herramientas de los agentes **solo lectura y sin red** | `cloud_agents/shared/capacity_tools.py` | Un agente real con acciones requiere aprobación humana y permisos mínimos |
| Supply Chain | Dependencias con rangos de versión; recomendación de `pip-audit` y escaneo de imágenes | `requirements*.txt` | Falta firma/verificación de modelos descargados |
| Vector and Embedding Weaknesses | Cache con clave `hash(modelo, texto)` (no mezcla modelos) | `services/cache.py` | Una cache compartida entre usuarios puede filtrar información; aísle por *tenant* |
| Autenticación | `X-API-Key` con `secrets.compare_digest` | `security.make_auth_dependency` | En producción use OIDC/Entra ID/IAM, no claves estáticas |

## 4. Defensa en capas (modelo mental)

```
Usuario → [Red/WAF] → [AuthN/AuthZ + cuotas] → [Guardrails de entrada] → [LLM con prompt de sistema controlado]
        → [Guardrails de salida] → [Herramientas con mínimo privilegio + aprobación humana] → [Auditoría y monitoreo]
```

Ninguna capa es suficiente por sí sola. El objetivo es que **la falla de una capa no sea catastrófica**.

## 5. Seguridad específica de infraestructura de inferencia

- **No exponga** el puerto del servidor de inferencia (Ollama 11434, vLLM 8000) a Internet: solo red privada / backend (ver `docker-compose.yml`: Ollama no publica puertos).
- **Cifrado** en tránsito (TLS) y en reposo (volúmenes de modelos y caches).
- **Secretos** en Key Vault / Secret Manager / Secrets Manager; nunca en Git ni en la imagen.
- **Identidades administradas** en lugar de claves (Managed Identity, Workload Identity, roles IAM).
- **Segmentación de red** y *egress* restringido: un modelo/agente comprometido no debería poder llamar a cualquier URL.
- **Auditoría**: quién llamó, con qué modelo, cuántos tokens (sin guardar el contenido sensible).
- **Cumplimiento**: protección de datos personales aplicable a su jurisdicción (p. ej., Ley 1581 de 2012 en Colombia; GDPR en la UE) — consulte a su oficial de privacidad.

## 6. Marcos de referencia

- OWASP Top 10 for LLM Applications (edición 2026 vigente; 2025 anterior) y OWASP Top 10 for Agentic Applications (dic-2025).
- NIST AI Risk Management Framework 1.0 y su *Generative AI Profile* (NIST AI 600-1).
- ISO/IEC 42001:2023 (sistema de gestión de IA).
- MITRE ATLAS (tácticas y técnicas de ataque a sistemas de IA).

## 7. Ejercicio (laboratorio de seguridad)

1. Abra la pestaña **Guardrails** del frontend y pruebe los tres ejemplos.
2. Intente **evadir** la regla de inyección (por ejemplo, parafraseando o en otro idioma). Documente qué funcionó.
3. Proponga una regla nueva y agregue una prueba en `app/backend/tests/test_services.py`.
4. Discuta: ¿qué ataque **no** puede detectar ninguna regla de texto? (pista: instrucciones ocultas dentro de un documento recuperado por RAG).
